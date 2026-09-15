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
        // portrait: edge to edge. Landscape: a floating card weighted to the
        // left, 460pt wide, so the page shows through beside it
        let stripTrail = wrap.trailingAnchor.constraint(equalTo: host.view.trailingAnchor)
        let stripWide = wrap.widthAnchor.constraint(equalToConstant: 460)
        let stripLead = wrap.leadingAnchor.constraint(equalTo: host.view.leadingAnchor)
        let stripLeadIn = wrap.leadingAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.leadingAnchor, constant: 8)
        let stripBottom = wrap.bottomAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.bottomAnchor)
        let stripBottomIn = wrap.bottomAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.bottomAnchor, constant: -6)
        self.stripTrail = stripTrail; self.stripWide = stripWide
        self.stripLead = stripLead; self.stripLeadIn = stripLeadIn
        self.stripBottom = stripBottom; self.stripBottomIn = stripBottomIn
        // the inset set: the same card, held off every edge by AD_MARGIN, and
        // anchored to whichever end the page asks for
        let g = host.view.safeAreaLayoutGuide
        let topM = wrap.topAnchor.constraint(equalTo: g.topAnchor, constant: AD_MARGIN)
        let botM = wrap.bottomAnchor.constraint(equalTo: g.bottomAnchor, constant: -AD_MARGIN)
        let leadM = wrap.leadingAnchor.constraint(equalTo: g.leadingAnchor, constant: AD_MARGIN)
        let trailM = wrap.trailingAnchor.constraint(equalTo: g.trailingAnchor, constant: -AD_MARGIN)
        self.stripTopM = topM; self.stripBottomM = botM
        self.stripLeadM = leadM; self.stripTrailM = trailM
        NSLayoutConstraint.activate([
            botM, leadM, trailM,
            wrap.heightAnchor.constraint(equalToConstant: AD_H),
        ])
        cornerWrap.isHidden = true
        cornerWrap.translatesAutoresizingMaskIntoConstraints = false
        host.view.addSubview(cornerWrap)
        // the card opens in the GAP: the page keeps one button at each end of
        // the top row and nothing in between, in either orientation, so the
        // card slides open in the middle and covers neither.
        let mid = cornerWrap.centerXAnchor.constraint(
            equalTo: host.view.safeAreaLayoutGuide.centerXAnchor)
        let lead = cornerWrap.leadingAnchor.constraint(
            equalTo: host.view.safeAreaLayoutGuide.leadingAnchor)
        cornerMid = mid; cornerLead = lead
        NSLayoutConstraint.activate([
            cornerWrap.topAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.topAnchor),
            mid,
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

    private var cornerMid: NSLayoutConstraint?
    private var cornerLead: NSLayoutConstraint?
    // the card's own size, re-made on every build - held so the previous
    // pair comes off first instead of stacking into a conflict
    private var cornerW: NSLayoutConstraint?
    private var cornerH: NSLayoutConstraint?
    private var stripTrail: NSLayoutConstraint?
    private var stripWide: NSLayoutConstraint?
    private var stripLead: NSLayoutConstraint?
    private var stripLeadIn: NSLayoutConstraint?
    private var stripBottom: NSLayoutConstraint?
    private var stripBottomIn: NSLayoutConstraint?
    // the card floats: a margin all round, so it reads as a piece of the app
    // rather than a bar welded to the screen edge. The page is told
    // AD_H + AD_MARGIN*2, which is everything the card takes from the edge,
    // so it reserves the gap as well as the card - the same arrangement the
    // Android shell uses, where the margin is padding inside the wrapper.
    private let AD_H: CGFloat = 76
    private let AD_MARGIN: CGFloat = 10
    private var stripTopM: NSLayoutConstraint?
    private var stripBottomM: NSLayoutConstraint?
    private var stripLeadM: NSLayoutConstraint?
    private var stripTrailM: NSLayoutConstraint?
    private var topSide = false
    @objc private func orientationChanged() {
        guard let v = host?.view else { return }
        let land = v.bounds.width > v.bounds.height
        // portrait now uses the SAME inset card as landscape - the only
        // difference left is landscape's fixed 460pt width, so the page shows
        // through beside it
        stripTrail?.isActive = false; stripLead?.isActive = false; stripBottom?.isActive = false
        stripBottomIn?.isActive = false; stripLeadIn?.isActive = false
        stripWide?.isActive = land
        stripTrailM?.isActive = !land
        stripLeadM?.isActive = true
        applySide()
        // the card wears the app's own button in BOTH orientations now: the
        // same corner and the same 1px #555 edge, so it reads as a piece of
        // the app rather than a bar welded to the screen.
        // NOTE: the portrait strip is still bottom-anchored and flush to the
        // edges here. Moving it to the top of the drawing screen, and giving
        // it the margin that makes it float, is a constraint change in this
        // file - Android has it; iOS needs a build to verify and has not had
        // one.
        wrap.layer.cornerRadius = 14
        wrap.clipsToBounds = true
        wrap.layer.borderWidth = 1
        wrap.layer.borderColor = UIColor(white: 0x55/255.0, alpha: 1).cgColor
    }

    // Which end the card sits at. The drawing screen wears it at the TOP:
    // thumbs rest at the bottom of a phone, which is exactly where a banner
    // collects stray taps, so the one screen the artist lives on puts it out
    // of reach. Every other screen keeps it at the bottom.
    // where the card opens: "mid" (the gap in the middle of the top row) or
    // "left" (the top-left corner). The page decides, because the page is what
    // knows which corner its layout left empty.
    func setSpot(_ spot: String) {
        let left = (spot == "left")
        guard left != spotLeft else { return }
        spotLeft = left
        cornerMid?.isActive = !left
        cornerLead?.isActive = left
        host?.view.layoutIfNeeded()
    }
    private var spotLeft = false

    func setTop(_ on: Bool) {
        guard topSide != on else { return }
        topSide = on
        applySide()
        reportHeight()
    }
    private func applySide() {
        let land = (host?.view.bounds.width ?? 0) > (host?.view.bounds.height ?? 0)
        let up = topSide && !land          // landscape uses the corner card
        stripTopM?.isActive = up
        stripBottomM?.isActive = !up
        host?.view.layoutIfNeeded()
    }
    // the page reserves what the card takes from the edge: the card plus the
    // margin on both sides of it. Without this it would reserve the 76pt
    // default and the card would sit over 20pt of the drawing.
    private func reportHeight() {
        let px = Int((AD_H + AD_MARGIN * 2).rounded())
        let n = (wrap.isHidden || removed) ? 0 : px
        web?.evaluateJavaScript("window.__adH && __adH(\(n))", completionHandler: nil)
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
        // ask for WIDE media: the card that plays video has a 16:9 player,
        // and a portrait creative in it is two black bars and a sliver.
        // A request, not a guarantee - the player stays 120pt tall so the
        // card is video-eligible whatever the auction returns.
        let media = NativeAdMediaAdLoaderOptions()
        media.mediaAspectRatio = .landscape
        let l = AdLoader(adUnitID: AdController.NATIVE_UNIT, rootViewController: host,
                         adTypes: [.native], options: [opts, media])
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
        reportHeight()
        if cornerShown && !(base && onProj) { collapseCorner() }
        else if !cornerShown && base && onProj { tryShowCorner() }
    }

    // It SLIDES OPEN: the card's own height constraint is animated from
    // nothing to full while the wrapper clips, so the card is uncovered from
    // the top edge down rather than scaled up out of a point - which is what
    // an ad appearing in a gap in a row of buttons should look like. The wrap
    // stops clipping at the end so its shadow can paint past its bounds.
    private func cornerReveal(_ open: Bool, _ then: (() -> Void)? = nil) {
        let full = cornerH?.constant ?? 120
        cornerWrap.clipsToBounds = true
        cornerH?.constant = open ? 0 : full
        cornerWrap.superview?.layoutIfNeeded()
        cornerH?.constant = open ? full : 0
        UIView.animate(withDuration: open ? 0.34 : 0.22, delay: 0,
                       options: open ? [.curveEaseOut, .allowUserInteraction]
                                     : [.curveEaseIn]) {
            self.cornerWrap.superview?.layoutIfNeeded()
        } completion: { _ in
            self.cornerWrap.clipsToBounds = false
            self.cornerH?.constant = full
            then?()
        }
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
        cornerWrap.alpha = 1
        cornerWrap.transform = .identity
        cornerWrap.isHidden = false
        cornerReveal(true)
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
        cornerReveal(false) { [weak self] in
            guard let self, !self.cornerShown else { return }
            self.cornerWrap.isHidden = true
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

    // The corner card, lying down: a wide player on the left, the Ad badge
    // and headline in a column to its RIGHT. It is exactly as SHORT as a card
    // may be and still be allowed to play video - 120pt, AdMob's media floor,
    // with the player flush top and bottom - and it spends the screen's WIDTH
    // instead, growing until it is about to reach the back and gear buttons
    // flanking it and stopping a margin short of each. The collapse pill has
    // a lane of its own inside the card's box, so it is still outside the ad
    // view (never an ad click) without costing the player 38pt of width.
    private func buildCorner(_ ad: NativeAd) {
        cornerWrap.subviews.forEach { $0.removeFromSuperview() }

        let adv = NativeAdView()
        adv.translatesAutoresizingMaskIntoConstraints = false
        adv.backgroundColor = .clear

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

        head.numberOfLines = 3

        // How far it may grow: the screen, less what a flanking chrome button
        // takes on each side - the 8pt edge inset, the 44pt button and a 12pt
        // margin off it. The player is never below 120pt square: that is the
        // floor for a card to be video-eligible at all, and a card that cannot
        // take video is not worth the width it would save.
        let GUT: CGFloat = 8, PILL: CGFloat = 32, PH: CGFloat = 120
        let screenW = host?.view.bounds.width ?? 390
        let budget = screenW - 2 * (8 + 44 + 12)
        var textW = min(max(budget * 0.34, 44), 118)
        let playerW = min(max(budget - GUT - PILL - textW, 120), 213)
        textW = min(max(budget - GUT - PILL - playerW, 44), 118)
        let advW = playerW + GUT + textW

        adv.addSubview(media); adv.addSubview(badge); adv.addSubview(head)
        NSLayoutConstraint.activate([
            adv.widthAnchor.constraint(equalToConstant: advW),
            adv.heightAnchor.constraint(equalToConstant: PH),
            // the player is flush: top, bottom and leading edge, no padding
            media.topAnchor.constraint(equalTo: adv.topAnchor),
            media.leadingAnchor.constraint(equalTo: adv.leadingAnchor),
            media.widthAnchor.constraint(equalToConstant: playerW),
            media.heightAnchor.constraint(equalToConstant: PH),
            badge.leadingAnchor.constraint(equalTo: media.trailingAnchor, constant: GUT),
            badge.widthAnchor.constraint(equalToConstant: 22),
            badge.heightAnchor.constraint(equalToConstant: 13),
            head.leadingAnchor.constraint(equalTo: badge.leadingAnchor),
            head.widthAnchor.constraint(equalToConstant: textW),
            head.topAnchor.constraint(equalTo: badge.bottomAnchor, constant: 4),
            // badge + headline ride as one block, centred on the player
            badge.topAnchor.constraint(equalTo: adv.topAnchor, constant: 26),
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
        close.layer.cornerRadius = 11
        close.translatesAutoresizingMaskIntoConstraints = false
        close.addTarget(self, action: #selector(closeTap), for: .touchUpInside)

        // the wrapper IS the card: it carries the skin, and holds the ad view
        // and the pill side by side inside it
        cornerWrap.backgroundColor = bgCol
        cornerWrap.layer.cornerRadius = 14
        cornerWrap.layer.borderWidth = 1
        cornerWrap.layer.borderColor = UIColor(white: 1, alpha: 0.12).cgColor
        cornerWrap.layer.shadowColor = UIColor.black.cgColor
        cornerWrap.layer.shadowOpacity = 0.5
        cornerWrap.layer.shadowRadius = 12
        cornerWrap.layer.shadowOffset = CGSize(width: 0, height: 4)
        cornerWrap.addSubview(adv)
        cornerWrap.addSubview(close)
        cornerW?.isActive = false; cornerH?.isActive = false
        cornerW = cornerWrap.widthAnchor.constraint(equalToConstant: advW + PILL)
        cornerH = cornerWrap.heightAnchor.constraint(equalToConstant: PH)
        NSLayoutConstraint.activate([
            cornerW!, cornerH!,
            adv.topAnchor.constraint(equalTo: cornerWrap.topAnchor),
            adv.leadingAnchor.constraint(equalTo: cornerWrap.leadingAnchor),
            close.trailingAnchor.constraint(equalTo: cornerWrap.trailingAnchor, constant: -5),
            close.topAnchor.constraint(equalTo: cornerWrap.topAnchor, constant: 5),
            close.widthAnchor.constraint(equalToConstant: 22),
            close.heightAnchor.constraint(equalToConstant: 22),
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
