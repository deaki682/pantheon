import UIKit
import WebKit
import GoogleMobileAds
import UserMessagingPlatform
import AppTrackingTransparency
import AdSupport

// The iOS half of the ad contract the page already speaks: one native
// card riding the TOP 80px, skinned to the backdrop the page reports
// through adPlace, accent-matched, visible only while a real ad is in
// hand. Consent first (Google's UMP form), then Apple's ATT prompt,
// then the SDK. Mirrors the Android shell's card exactly.
final class AdController: NSObject {
    // set by the AdMob console; the ~ id lives in Info.plist
    static let NATIVE_UNIT = "ca-app-pub-4573680538268043/8895033063"

    private weak var host: UIViewController?
    private weak var web: WKWebView?
    private let wrap = UIView()
    // corner mode (drawing screen only): the download button's corner
    // becomes the 120x120-media card for a bounded window, then returns
    private let cornerWrap = UIView()
    private var onProj = false
    private var cornerShown = false
    private var viewMode = ""
    private var nextShowAt: CFTimeInterval = 0
    private var lastTouch: CFTimeInterval = 0
    private var showTimer: Timer?
    private var hideTimer: Timer?
    private let AD_ON_S: TimeInterval = 45
    private let AD_OFF_S: TimeInterval = 240
    private var loader: AdLoader?
    private var nativeAd: NativeAd?
    private var badgeV: UILabel?
    private var ctaV: UILabel?
    private var cardV: NativeAdView?
    private var wanted = false
    private var started = false
    private var removed = false
    private var bgCol = UIColor(red: 0x14/255.0, green: 0x14/255.0, blue: 0x14/255.0, alpha: 1)
    private var accCol = UIColor(red: 0xE8/255.0, green: 0x83/255.0, blue: 0x3A/255.0, alpha: 1)

    init(host: UIViewController, web: WKWebView) {
        self.host = host
        self.web = web
        super.init()
        wrap.isHidden = true
        wrap.translatesAutoresizingMaskIntoConstraints = false
        host.view.addSubview(wrap)
        NSLayoutConstraint.activate([
            wrap.bottomAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.bottomAnchor),
            wrap.leadingAnchor.constraint(equalTo: host.view.leadingAnchor),
            wrap.trailingAnchor.constraint(equalTo: host.view.trailingAnchor),
            wrap.heightAnchor.constraint(equalToConstant: 76),
        ])
        cornerWrap.isHidden = true
        cornerWrap.translatesAutoresizingMaskIntoConstraints = false
        host.view.addSubview(cornerWrap)
        // the card grows out of the download button's corner: top-right in
        // portrait, top-left in landscape (where the page moves that button)
        let trail = cornerWrap.trailingAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.trailingAnchor)
        let lead = cornerWrap.leadingAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.leadingAnchor)
        cornerTrail = trail; cornerLead = lead
        NSLayoutConstraint.activate([
            cornerWrap.topAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.topAnchor),
            trail,
        ])
        NotificationCenter.default.addObserver(self, selector: #selector(orientationChanged),
            name: UIDevice.orientationDidChangeNotification, object: nil)
        orientationChanged()
        // the card never materializes under a finger: a passive recognizer
        // timestamps every touch so the show gate can wait for a quiet hand
        let touch = UILongPressGestureRecognizer(target: self, action: #selector(anyTouch(_:)))
        touch.minimumPressDuration = 0
        touch.cancelsTouchesInView = false
        touch.delegate = self
        host.view.addGestureRecognizer(touch)
    }

    @objc private func anyTouch(_ g: UIGestureRecognizer) { lastTouch = CACurrentMediaTime() }

    private var cornerTrail: NSLayoutConstraint?
    private var cornerLead: NSLayoutConstraint?
    @objc private func orientationChanged() {
        guard let v = host?.view else { return }
        let land = v.bounds.width > v.bounds.height
        cornerTrail?.isActive = !land
        cornerLead?.isActive = land
    }

    // the remove-ads purchase: the slot collapses and the stack never
    // starts again (the entitlement re-checks on every launch)
    func disable() {
        removed = true
        wanted = false
        nativeAd = nil
        cardShown = false
        wrap.isHidden = true
        cornerShown = false
        cornerWrap.isHidden = true
        showTimer?.invalidate(); showTimer = nil
        hideTimer?.invalidate(); hideTimer = nil
        web?.evaluateJavaScript("window.__adOn && __adOn(false)", completionHandler: nil)
        web?.evaluateJavaScript("window.__adCorner && __adCorner(false)", completionHandler: nil)
    }

    // consent -> tracking prompt -> SDK -> first load + gentle refresh
    func start() {
        guard let host, !removed, !StoreController.removed else { return }
        let params = RequestParameters()
        ConsentInformation.shared.requestConsentInfoUpdate(with: params) { [weak self] err in
            DispatchQueue.main.async {
                if err == nil {
                    ConsentForm.loadAndPresentIfRequired(from: host) { _ in
                        self?.askTrackingThenBoot()
                    }
                } else {
                    self?.askTrackingThenBoot()
                }
            }
        }
    }

    private func askTrackingThenBoot() {
        if #available(iOS 14, *) {
            ATTrackingManager.requestTrackingAuthorization { [weak self] _ in
                DispatchQueue.main.async { self?.boot() }
            }
        } else { boot() }
    }

    private func boot() {
        guard !started, ConsentInformation.shared.canRequestAds else { return }
        started = true
        // surface the advertising identifier in the page's version-tap log
        // so a test device can be registered without Xcode (all zeros =
        // tracking declined; Allow tracking to get the real one)
        let idfa = ASIdentifierManager.shared().advertisingIdentifier.uuidString
        web?.evaluateJavaScript("window.plog && plog('idfa: \(idfa)')", completionHandler: nil)
        MobileAds.shared.start(completionHandler: nil)
        loadNative()
        Timer.scheduledTimer(withTimeInterval: 75, repeats: true) { [weak self] _ in
            guard let self, self.wanted else { return }
            self.loadNative()
        }
    }

    private func loadNative() {
        guard let host else { return }
        let opts = NativeAdViewAdOptions()
        opts.preferredAdChoicesPosition = .topRightCorner
        let l = AdLoader(adUnitID: AdController.NATIVE_UNIT, rootViewController: host,
                         adTypes: [.native], options: [opts])
        l.delegate = self
        loader = l
        l.load(Request())
    }

    // ---- the page's ad contract -----------------------------------------
    func place(on: Bool, bg: String) {
        wanted = on
        if let c = AdController.color(bg) { bgCol = c }
        wrap.backgroundColor = bgCol
        wrap.subviews.first?.backgroundColor = bgCol
        cardV?.backgroundColor = bgCol
        applyAd()
    }

    // the page flags the drawing screen: there the strip yields to the
    // intermittent corner card (and only there)
    func setProj(_ on: Bool) {
        guard onProj != on else { return }
        onProj = on
        applyAd()
    }

    func accent(_ hex: String) {
        guard let c = AdController.color(hex) else { return }
        accCol = c
        badgeV?.textColor = c
        badgeV?.layer.borderColor = c.cgColor
        ctaV?.backgroundColor = c
    }

    // two placements, one ad: the persistent bottom strip everywhere except
    // the drawing screen; there, the intermittent corner card instead
    private var cardShown = false
    private func applyAd() {
        let base = wanted && nativeAd != nil && !removed
        let stripWant = base && !onProj
        if stripWant != cardShown {
            cardShown = stripWant
            wrap.layer.removeAllAnimations()
            if stripWant {
                if viewMode != "strip", let ad = nativeAd { buildStrip(ad) }
                wrap.transform = CGAffineTransform(translationX: 0, y: 56)
                wrap.alpha = 0
                wrap.isHidden = false
                UIView.animate(withDuration: 0.22, delay: 0,
                               options: [.curveEaseOut, .allowUserInteraction]) {
                    self.wrap.transform = .identity
                    self.wrap.alpha = 1
                }
            } else {
                UIView.animate(withDuration: 0.16, delay: 0,
                               options: [.curveEaseIn]) {
                    self.wrap.transform = CGAffineTransform(translationX: 0, y: 56)
                    self.wrap.alpha = 0
                } completion: { _ in
                    guard !self.cardShown else { return }
                    self.wrap.isHidden = true
                    self.wrap.transform = .identity
                    self.wrap.alpha = 1
                }
            }
        }
        let slot = wanted && !removed && !onProj
        web?.evaluateJavaScript("window.__adOn && __adOn(\(slot ? "true" : "false"))",
                                completionHandler: nil)
        if cornerShown && !(base && onProj) { collapseCorner() }
        else if !cornerShown && base && onProj { tryShowCorner() }
    }

    // scale about the wrap's top-right corner - the card visibly grows out
    // of (and returns into) the download button's spot
    private func cornerTransform(_ s: CGFloat) -> CGAffineTransform {
        let w = cornerWrap.bounds.width, h = cornerWrap.bounds.height
        return CGAffineTransform(translationX: (w / 2) * (1 - s), y: -(h / 2) * (1 - s))
            .scaledBy(x: s, y: s)
    }

    private func tryShowCorner() {
        showTimer?.invalidate(); showTimer = nil
        guard !cornerShown, wanted, onProj, !removed, let ad = nativeAd else { return }
        let now = CACurrentMediaTime()
        if now < nextShowAt {
            showTimer = Timer.scheduledTimer(withTimeInterval: nextShowAt - now, repeats: false) {
                [weak self] _ in self?.tryShowCorner() }
            return
        }
        if now - lastTouch < 3 {
            showTimer = Timer.scheduledTimer(withTimeInterval: 3, repeats: false) {
                [weak self] _ in self?.tryShowCorner() }
            return
        }
        if viewMode != "corner" { buildCorner(ad) }
        cornerShown = true
        cornerWrap.isHidden = false
        cornerWrap.layoutIfNeeded()
        cornerWrap.alpha = 0
        cornerWrap.transform = cornerTransform(0.3)
        UIView.animate(withDuration: 0.35, delay: 0,
                       options: [.curveEaseOut, .allowUserInteraction]) {
            self.cornerWrap.alpha = 1
            self.cornerWrap.transform = .identity
        }
        web?.evaluateJavaScript("window.__adCorner && __adCorner(true)", completionHandler: nil)
        hideTimer?.invalidate()
        hideTimer = Timer.scheduledTimer(withTimeInterval: AD_ON_S, repeats: false) {
            [weak self] _ in self?.collapseCorner() }
    }

    @objc private func closeTap() { collapseCorner() }

    private func collapseCorner() {
        hideTimer?.invalidate(); hideTimer = nil
        guard cornerShown else { return }
        cornerShown = false
        nextShowAt = CACurrentMediaTime() + AD_OFF_S
        UIView.animate(withDuration: 0.25, delay: 0, options: [.curveEaseIn]) {
            self.cornerWrap.alpha = 0
            self.cornerWrap.transform = self.cornerTransform(0.3)
        } completion: { _ in
            guard !self.cornerShown else { return }
            self.cornerWrap.isHidden = true
            self.cornerWrap.transform = .identity
            self.cornerWrap.alpha = 1
        }
        web?.evaluateJavaScript("window.__adCorner && __adCorner(false)", completionHandler: nil)
        loadNative()          // a fresh creative earns the next window
        if wanted && onProj && !removed {
            showTimer?.invalidate()
            showTimer = Timer.scheduledTimer(withTimeInterval: AD_OFF_S, repeats: false) {
                [weak self] _ in self?.tryShowCorner() }
        }
    }

    // ---- the card, in the app's own dark language -----------------------
    private static func lift(_ c: UIColor) -> UIColor {
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        c.getRed(&r, green: &g, blue: &b, alpha: &a)
        func up(_ v: CGFloat) -> CGFloat { min(1, v + (1 - v) * 0.07) }
        return UIColor(red: up(r), green: up(g), blue: up(b), alpha: 1)
    }
    private func badgeLabel() -> UILabel {
        let badge = UILabel()
        badge.text = "Ad"
        badge.font = .systemFont(ofSize: 9)
        badge.textColor = accCol
        badge.textAlignment = .center
        badge.layer.borderWidth = 1
        badge.layer.borderColor = accCol.cgColor
        badge.layer.cornerRadius = 3
        badge.translatesAutoresizingMaskIntoConstraints = false
        return badge
    }

    // the bottom strip, refreshed: 64pt media, Ad badge + bold headline,
    // body line, rating/store/price row, filled accent CTA - every asset
    // registered, so a tap anywhere on the card is the ad's click
    private func buildStrip(_ ad: NativeAd) {
        wrap.subviews.forEach { $0.removeFromSuperview() }

        let adv = NativeAdView()
        adv.translatesAutoresizingMaskIntoConstraints = false
        adv.backgroundColor = AdController.lift(bgCol)
        let hair = UIView()
        hair.backgroundColor = UIColor(white: 1, alpha: 0.12)
        hair.translatesAutoresizingMaskIntoConstraints = false

        let media = MediaView()
        media.translatesAutoresizingMaskIntoConstraints = false
        media.layer.cornerRadius = 10
        media.clipsToBounds = true

        let badge = badgeLabel()

        let head = UILabel()
        head.font = .boldSystemFont(ofSize: 13.5)
        head.textColor = UIColor(red: 0xF2/255.0, green: 0xF0/255.0, blue: 0xEB/255.0, alpha: 1)
        head.lineBreakMode = .byTruncatingTail
        head.text = ad.headline
        head.translatesAutoresizingMaskIntoConstraints = false

        let body = UILabel()
        body.font = .systemFont(ofSize: 11.5)
        body.textColor = UIColor(red: 0xA8/255.0, green: 0xA4/255.0, blue: 0x9D/255.0, alpha: 1)
        body.lineBreakMode = .byTruncatingTail
        body.text = ad.body ?? ""
        body.isHidden = (ad.body ?? "").isEmpty
        body.translatesAutoresizingMaskIntoConstraints = false

        let meta = UILabel()
        meta.font = .systemFont(ofSize: 10.5)
        meta.textColor = UIColor(red: 0x8A/255.0, green: 0x87/255.0, blue: 0x81/255.0, alpha: 1)
        meta.lineBreakMode = .byTruncatingTail
        var parts: [String] = []
        if let r = ad.starRating?.doubleValue, r > 0 {
            parts.append(String(repeating: "\u{2605}", count: max(0, min(5, Int(r.rounded())))))
            parts.append(String(format: "%.1f", r))
        }
        if let st = ad.store, !st.isEmpty { parts.append(st) }
        if let pr = ad.price, !pr.isEmpty { parts.append(pr) }
        meta.text = parts.joined(separator: " \u{00b7} ")
        meta.isHidden = parts.isEmpty
        meta.translatesAutoresizingMaskIntoConstraints = false

        let cta = UILabel()
        cta.font = .boldSystemFont(ofSize: 13.5)
        cta.textColor = UIColor(red: 0x14/255.0, green: 0x14/255.0, blue: 0x14/255.0, alpha: 1)
        cta.textAlignment = .center
        cta.backgroundColor = accCol
        cta.layer.cornerRadius = 20
        cta.clipsToBounds = true
        cta.text = "  " + (ad.callToAction ?? "Open") + "  "
        cta.translatesAutoresizingMaskIntoConstraints = false

        let col = UIStackView(arrangedSubviews: [head, body, meta])
        col.axis = .vertical
        col.spacing = 2
        col.translatesAutoresizingMaskIntoConstraints = false

        adv.addSubview(hair); adv.addSubview(media); adv.addSubview(badge)
        adv.addSubview(col); adv.addSubview(cta)
        NSLayoutConstraint.activate([
            hair.topAnchor.constraint(equalTo: adv.topAnchor),
            hair.leadingAnchor.constraint(equalTo: adv.leadingAnchor),
            hair.trailingAnchor.constraint(equalTo: adv.trailingAnchor),
            hair.heightAnchor.constraint(equalToConstant: 1),
            media.leadingAnchor.constraint(equalTo: adv.leadingAnchor, constant: 10),
            media.centerYAnchor.constraint(equalTo: adv.centerYAnchor),
            media.widthAnchor.constraint(equalToConstant: 64),
            media.heightAnchor.constraint(equalToConstant: 64),
            cta.trailingAnchor.constraint(equalTo: adv.trailingAnchor, constant: -10),
            cta.centerYAnchor.constraint(equalTo: adv.centerYAnchor),
            cta.heightAnchor.constraint(equalToConstant: 40),
            cta.widthAnchor.constraint(greaterThanOrEqualToConstant: 84),
            badge.leadingAnchor.constraint(equalTo: media.trailingAnchor, constant: 10),
            badge.centerYAnchor.constraint(equalTo: head.centerYAnchor),
            badge.widthAnchor.constraint(equalToConstant: 22),
            badge.heightAnchor.constraint(equalToConstant: 13),
            col.leadingAnchor.constraint(equalTo: badge.trailingAnchor, constant: 6),
            col.trailingAnchor.constraint(equalTo: cta.leadingAnchor, constant: -10),
            col.centerYAnchor.constraint(equalTo: adv.centerYAnchor),
        ])
        adv.mediaView = media
        adv.headlineView = head
        adv.bodyView = body
        adv.starRatingView = meta
        adv.callToActionView = cta
        adv.nativeAd = ad
        badgeV = badge
        ctaV = cta

        wrap.addSubview(adv)
        NSLayoutConstraint.activate([
            adv.topAnchor.constraint(equalTo: wrap.topAnchor),
            adv.bottomAnchor.constraint(equalTo: wrap.bottomAnchor),
            adv.leadingAnchor.constraint(equalTo: wrap.leadingAnchor),
            adv.trailingAnchor.constraint(equalTo: wrap.trailingAnchor),
        ])
        cardV = adv
        viewMode = "strip"
    }

    // the corner card: the smallest video-eligible card there is - the
    // 120x120 media square with one line of Ad badge + headline beneath
    // (132 x 150pt, no CTA); the collapse pill sits outside the ad view so
    // its tap never counts as an ad click
    private func buildCorner(_ ad: NativeAd) {
        cornerWrap.subviews.forEach { $0.removeFromSuperview() }

        let adv = NativeAdView()
        adv.translatesAutoresizingMaskIntoConstraints = false
        adv.backgroundColor = bgCol
        adv.layer.cornerRadius = 14
        adv.layer.borderWidth = 1
        adv.layer.borderColor = UIColor(white: 1, alpha: 0.12).cgColor
        adv.layer.shadowColor = UIColor.black.cgColor
        adv.layer.shadowOpacity = 0.5
        adv.layer.shadowRadius = 12
        adv.layer.shadowOffset = CGSize(width: 0, height: 4)

        let media = MediaView()
        media.translatesAutoresizingMaskIntoConstraints = false
        media.layer.cornerRadius = 8
        media.clipsToBounds = true

        let badge = badgeLabel()

        let head = UILabel()
        head.font = .systemFont(ofSize: 10.5)
        head.textColor = UIColor(red: 0xE8/255.0, green: 0xE6/255.0, blue: 0xE1/255.0, alpha: 1)
        head.lineBreakMode = .byTruncatingTail
        head.text = ad.headline
        head.translatesAutoresizingMaskIntoConstraints = false

        adv.addSubview(media); adv.addSubview(badge); adv.addSubview(head)
        NSLayoutConstraint.activate([
            adv.widthAnchor.constraint(equalToConstant: 132),
            adv.heightAnchor.constraint(equalToConstant: 150),
            media.topAnchor.constraint(equalTo: adv.topAnchor, constant: 6),
            media.leadingAnchor.constraint(equalTo: adv.leadingAnchor, constant: 6),
            media.widthAnchor.constraint(equalToConstant: 120),
            media.heightAnchor.constraint(equalToConstant: 120),
            badge.leadingAnchor.constraint(equalTo: media.leadingAnchor),
            badge.topAnchor.constraint(equalTo: media.bottomAnchor, constant: 5),
            badge.widthAnchor.constraint(equalToConstant: 22),
            badge.heightAnchor.constraint(equalToConstant: 13),
            head.leadingAnchor.constraint(equalTo: badge.trailingAnchor, constant: 5),
            head.trailingAnchor.constraint(equalTo: media.trailingAnchor),
            head.centerYAnchor.constraint(equalTo: badge.centerYAnchor),
        ])
        adv.mediaView = media
        adv.headlineView = head
        adv.nativeAd = ad

        let close = UIButton(type: .custom)
        close.setTitle("\u{2715}", for: .normal)
        close.setTitleColor(UIColor(red: 0xB9/255.0, green: 0xB5/255.0, blue: 0xAE/255.0, alpha: 1),
                            for: .normal)
        close.titleLabel?.font = .systemFont(ofSize: 12)
        close.backgroundColor = UIColor(white: 0.1, alpha: 0.9)
        close.layer.cornerRadius = 13
        close.translatesAutoresizingMaskIntoConstraints = false
        close.addTarget(self, action: #selector(closeTap), for: .touchUpInside)

        // the collapse pill sits LEFT of the card - outside the ad view,
        // never an ad click
        cornerWrap.addSubview(adv)
        cornerWrap.addSubview(close)
        NSLayoutConstraint.activate([
            adv.topAnchor.constraint(equalTo: cornerWrap.topAnchor),
            adv.trailingAnchor.constraint(equalTo: cornerWrap.trailingAnchor),
            adv.bottomAnchor.constraint(equalTo: cornerWrap.bottomAnchor),
            close.leadingAnchor.constraint(equalTo: cornerWrap.leadingAnchor),
            close.trailingAnchor.constraint(equalTo: adv.leadingAnchor, constant: -12),
            close.topAnchor.constraint(equalTo: cornerWrap.topAnchor, constant: 62),
            close.widthAnchor.constraint(equalToConstant: 26),
            close.heightAnchor.constraint(equalToConstant: 26),
        ])
        badgeV = badge
        ctaV = nil
        cardV = adv
        viewMode = "corner"
    }

    private static func color(_ hex: String) -> UIColor? {
        var h = hex.trimmingCharacters(in: .whitespaces)
        if h.hasPrefix("#") { h.removeFirst() }
        guard h.count == 6, let v = UInt32(h, radix: 16) else { return nil }
        return UIColor(red: CGFloat((v >> 16) & 0xFF)/255.0,
                       green: CGFloat((v >> 8) & 0xFF)/255.0,
                       blue: CGFloat(v & 0xFF)/255.0, alpha: 1)
    }
}

extension AdController: NativeAdLoaderDelegate {
    func adLoader(_ adLoader: AdLoader, didReceive nativeAd: NativeAd) {
        DispatchQueue.main.async {
            self.web?.evaluateJavaScript("window.plog && plog('ad: loaded')",
                                         completionHandler: nil)
            self.nativeAd = nativeAd
            self.viewMode = ""            // rebuilt into whichever mode shows
            self.applyAd()
        }
    }
    func adLoader(_ adLoader: AdLoader, didFailToReceiveAdWithError error: Error) {
        // no fill: the slot stays empty (the page shows through); the 75s
        // tick retries while wanted. The code lands in the version-tap log.
        let code = (error as NSError).code
        DispatchQueue.main.async {
            self.web?.evaluateJavaScript("window.plog && plog('ad: failed code \(code)')",
                                         completionHandler: nil)
        }
    }
}

extension AdController: UIGestureRecognizerDelegate {
    // passive observer: never steal or delay the page's own touches
    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                           shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool {
        return true
    }
}
