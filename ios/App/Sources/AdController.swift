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
    // corner mode (the two canvas screens): a thin banner rests in whichever
    // corner the page's own layout leaves empty, and blooms to the 120pt video
    // card for a bounded window before settling back to the banner
    /* An ad view is always a rectangle; upright this card is an L. Everything
       to the RIGHT of the tab and BELOW the band is the drawing, not the ad,
       and a touch there has to reach the page - both because the artist is
       trying to draw and because an ad collecting taps on empty air over
       someone's work is exactly the accidental-click layout the network
       polices. */
    /* THE INNER CORNER OF THE L, where the tab's right edge meets the band's
       underside. Every other corner of this card is convex and a radius does
       it; this one is CONCAVE - the material has to bulge INTO the empty
       quadrant to meet itself smoothly - and no corner radius can express
       that, so it is a small painted patch: a square of card with a quarter
       disc taken out of it, and the hairline running round the arc. */
    final class Fillet: UIView {
        var rad: CGFloat = 14
        var fillCol: UIColor = .black
        override func draw(_ rect: CGRect) {
            let r = rad
            guard r > 0, let c = UIGraphicsGetCurrentContext() else { return }
            let p = UIBezierPath()
            p.move(to: .zero)
            p.addLine(to: CGPoint(x: r, y: 0))
            p.addArc(withCenter: CGPoint(x: r, y: r), radius: r,
                     startAngle: -.pi / 2, endAngle: .pi, clockwise: false)
            p.close()
            fillCol.setFill()
            p.fill()
            // only the ARC carries a line: the patch's two straight sides are
            // continuations of the band and the tab, not edges of their own
            let arc = UIBezierPath()
            arc.addArc(withCenter: CGPoint(x: r, y: r), radius: r,
                       startAngle: -.pi / 2, endAngle: .pi, clockwise: false)
            UIColor(white: 1, alpha: 0.2).setStroke()
            arc.lineWidth = 1
            arc.stroke()
            _ = c
        }
    }
    private var filletV: Fillet?
    private var tabV: UIView?

    final class LWrap: UIView {
        var bandH: CGFloat = 0
        var tabW: CGFloat = 0
        var isL = false
        override func point(inside point: CGPoint, with event: UIEvent?) -> Bool {
            guard isL, bandH > 0, tabW > 0 else { return super.point(inside: point, with: event) }
            if !super.point(inside: point, with: event) { return false }
            return point.y <= bandH || point.x <= tabW
        }
    }
    private let cornerWrap = LWrap()
    private var onProj = false
    private var cornerShown = false
    private var viewMode = ""
    private var lastTouch: CFTimeInterval = 0
    private var cardH: CGFloat = 120                // the bloomed height
    private var headV: UILabel?
    private var mediaClipH: NSLayoutConstraint?
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
        // Both canvas screens stack their two controls down the LEFT edge, so
        // the card owns the top-RIGHT corner on every screen and in either
        // orientation - it never has to be near a button. (cornerLead stays
        // for a layout that wants it on the other side.)
        //
        // The web view is constrained to this same safe-area guide, so the
        // card clears the Dynamic Island, the notch and the home indicator for
        // free. The 8pt puts it on the same line as the page's own buttons.
        let mid = cornerWrap.trailingAnchor.constraint(
            equalTo: host.view.safeAreaLayoutGuide.trailingAnchor, constant: 0)
        let lead = cornerWrap.leadingAnchor.constraint(
            equalTo: host.view.safeAreaLayoutGuide.leadingAnchor, constant: 0)
        let top = cornerWrap.topAnchor.constraint(
            equalTo: host.view.safeAreaLayoutGuide.topAnchor, constant: 0)
        cornerMid = mid; cornerLead = lead; cornerTop = top
        // the flush pair: both edges of the safe area, no inset. The web view
        // shares this guide, so flush is flush with the CONTENT - never under
        // the Dynamic Island or the notch.
        cornerLeadFlush = cornerWrap.leadingAnchor.constraint(
            equalTo: host.view.safeAreaLayoutGuide.leadingAnchor)
        cornerTrailFlush = cornerWrap.trailingAnchor.constraint(
            equalTo: host.view.safeAreaLayoutGuide.trailingAnchor)
        NSLayoutConstraint.activate([top, mid])
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
    private var cornerTop: NSLayoutConstraint?
    private var cardClip: UIView?          // the crop the card rides in
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
    // which corner the card takes: "right" upright, "left" sideways. The page
    // decides, because the page is what knows which corner its own layout left
    // empty - and the card's SHAPE hangs off the answer.
    func setSpot(_ spot: String) {
        let left = (spot == "left")
        let flush = (spot == "top")
        guard left != spotLeft || flush != spotFlush else { return }
        spotLeft = left
        spotFlush = flush
        bloomWork?.cancel(); bloomWork = nil; bloomed = false
        topSent = -1
        // FLUSH takes both edges of the safe area and gives up the fixed
        // width the corner card carries; the corner card takes one edge and
        // keeps it.
        cornerMid?.isActive = !left && !flush
        cornerLead?.isActive = left && !flush
        cornerLeadFlush?.isActive = flush
        cornerTrailFlush?.isActive = flush
        cornerW?.isActive = !flush
        if !flush { reportTop(0) }
        // the card's SHAPE hangs off this - `tall` is spotLeft - so a corner
        // change is a change of shape, not just of position, and the card has
        // to be rebuilt or it ends up lying down inside a standing box
        if viewMode == "corner", let ad = nativeAd { buildCorner(ad) }
        applyCornerGeometry()
        host?.view.layoutIfNeeded()
    }
    private var spotLeft = false
    /* UPRIGHT THE CARD IS A FLUSH BANNER. Not a corner card with a margin -
       wall to wall along the top edge, no inset, no rounding, the shape a
       banner actually is. It can be that now because the top of both canvas
       screens is empty: the gear-and-Download pill that held the top-left is
       gone and every remaining control sits along the bottom.
       It rests as a band and OPENS for a video. Rarely - four minutes is the
       floor between two of them and most creatives carry no video at all -
       because a banner that resizes often is a banner that moves while
       someone is drawing under it. Nothing on the page is displaced either
       way: the banner floats over it. */
    private var spotFlush = false
    private var cornerLeadFlush: NSLayoutConstraint?
    private var cornerTrailFlush: NSLayoutConstraint?
    // the floor: what a banner conventionally is, and below which the band
    // stops reading as one. The real resting height is MEASURED from the
    // headline at the viewer's own text size (see buildCorner).
    private let FLUSH_MIN: CGFloat = 64
    private var flushRest: CGFloat = 0     // measured; 0 until a card is built
    private var restH: CGFloat { flushRest > 0 ? flushRest : FLUSH_MIN }
    private let BLOOM_GAP: CFTimeInterval = 4 * 60
    private let BLOOM_MAX: TimeInterval = 32
    private var bloomed = false
    private var lastBloom: CFTimeInterval = 0
    private var bloomWork: DispatchWorkItem?
    private var topSent = -1

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
        cornerWrap.backgroundColor = bgCol  // the corner card, and the clip
        cardClip?.backgroundColor = bgCol   // in front of it that wears its skin
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
        // THE STRIP CANNOT COME UP AT ALL. It appears when ads are wanted
        // but the card does not own the screen - and no screen in the app is
        // like that any more: the page asks for an ad only on the two canvas
        // screens, and on both of those the card owns it. So the condition is
        // only ever true in the gap between the two messages that say so, and
        // every time it was true it animated a strip up from the bottom edge
        // and straight back down. Ordering the messages closed that gap; this
        // makes the gap harmless. The strip is still BUILT, because the
        // placement is the operator's to change and not the shell's to
        // assume - it simply is not raised.
        let stripWant = false
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
        let slot = false
        web?.evaluateJavaScript("window.__adOn && __adOn(\(slot ? "true" : "false"))",
                                completionHandler: nil)
        reportHeight()
        // "there is an ad to show at all", which is separate from whether any
        // particular screen wants it. This was declared beside `stripWant`,
        // and when the strip was hardcoded off in v480 the declaration went
        // with it while its two uses below stayed - so the iOS target has not
        // compiled since. It is the same condition tryShowCorner guards on.
        let base = wanted && nativeAd != nil && !removed
        if cornerShown && !(base && onProj) { hideCorner() }
        else if !cornerShown && base && onProj { tryShowCorner() }
    }

    // The card is PERMANENT on a canvas screen: a thin banner, always there,
    // which blooms to the video height now and then and shrinks back to the
    // banner. Showing it at all is the screen's business; expanding it is the
    // cadence's, so the artist never gets a hole where an ad used to be.
    // The card is one fixed size, floating a margin off the corner with all
    // four corners rounded. This is what is left of a banner-to-bloom
    // animation, and it stays a function because a rotation or a rebuild has
    // to re-apply it.
    private func applyCornerGeometry(_ h0: CGFloat = -1) {
        // FLUSH rests as a band and opens its TAB to the square; the corner
        // card has one height and always had.
        let h = h0 >= 0 ? h0
              : (spotFlush && !bloomed ? restH : cardH)
        if spotFlush {
            // ONLY THE TAB MOVES. The band keeps the height its headline
            // asked for whatever the video is doing - that is the whole point
            // of the shape - so the wrapper stands at the tab's full reach
            // and the tab's own clip is the thing that animates.
            cornerH?.constant = cardH
            mediaClipH?.constant = h
            // SHUT, THE TAB IS NOT A BOX. It is exactly the band's height and
            // the band's colour, so an outline round it would just be a line
            // drawn across the banner, and a rounded bottom would bite a
            // notch out of the band's own underside. Both belong to the tab
            // only while it is OUT.
            let out = h > restH + 1
            tabV?.layer.cornerRadius = out ? 14 : 0
            tabV?.layer.borderWidth = out ? 1 : 0
            filletV?.isHidden = !out
        } else {
            cornerH?.constant = h
        }
        // FLUSH IN THE CORNER, SIDEWAYS TOO. The standing card used to float a
        // margin off the top-left, which left a sliver of drawing showing
        // behind two of its edges and read as a sticker rather than as part
        // of the frame. Hard into the corner it belongs to the edge, the way
        // the upright banner belongs to the top.
        cornerTop?.constant = 0
        cornerMid?.constant = 0
        cornerLead?.constant = 0
        // ONLY THE CORNER THAT FACES THE DRAWING IS ROUND. Two of the card's
        // edges are the screen's own now, and a radius on a corner sitting on
        // a screen edge just opens a gap in it. Sideways that leaves the
        // bottom-trailing one; upright the band is welded to the top and the
        // tab carries the curve instead.
        let r: CGFloat = spotFlush ? 0 : 14
        let skin = cardClip ?? cornerWrap
        let free: CACornerMask = [.layerMaxXMaxYCorner]
        cornerWrap.layer.cornerRadius = r
        skin.layer.cornerRadius = r
        skin.layer.maskedCorners = free
        cornerWrap.layer.maskedCorners = free
        if !spotLeft { headV?.numberOfLines = 3 }   // the card always has the room
        if spotFlush { reportTop(cornerShown ? Int(h.rounded()) : 0) }
    }
    // how much of the page's top edge the banner is standing on
    private func reportTop(_ px: Int) {
        guard topSent != px else { return }
        topSent = px
        web?.evaluateJavaScript("window.__adTop && __adTop(\(px))", completionHandler: nil)
    }

    private func bloomEligible() -> Bool {
        guard spotFlush, cornerShown, !bloomed, let ad = nativeAd else { return false }
        guard ad.mediaContent.hasVideoContent else { return false }
        let now = CACurrentMediaTime()
        return lastBloom == 0 || now - lastBloom >= BLOOM_GAP
    }
    private func bloomTry() {
        guard bloomEligible() else { return }
        lastBloom = CACurrentMediaTime()
        bloomSet(true)
        let w = DispatchWorkItem { [weak self] in self?.bloomSet(false) }
        bloomWork?.cancel(); bloomWork = w
        DispatchQueue.main.asyncAfter(deadline: .now() + BLOOM_MAX, execute: w)
        // ...and sooner if the video finishes first
        nativeAd?.mediaContent.videoController.delegate = self
    }
    private func bloomSet(_ open: Bool) {
        guard spotFlush, bloomed != open else { return }
        bloomed = open
        applyCornerGeometry()
        UIView.animate(withDuration: 0.26, delay: 0,
                       options: [.curveEaseInOut, .allowUserInteraction]) {
            self.cornerWrap.superview?.layoutIfNeeded()
        }
    }

    private func tryShowCorner() {
        guard !cornerShown, wanted, onProj, !removed, let ad = nativeAd else { return }
        if viewMode != "corner" { buildCorner(ad) }
        cornerShown = true
        cornerWrap.alpha = 1
        cornerWrap.transform = .identity
        cornerWrap.isHidden = false
        applyCornerGeometry()
        cornerWrap.superview?.layoutIfNeeded()
        web?.evaluateJavaScript("window.__adCorner && __adCorner(true)", completionHandler: nil)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.9) { [weak self] in self?.bloomTry() }
    }

    // ...and this is the card leaving, when the screen changes. Nothing else
    // takes it away: it is the video card at one size the whole time it is up,
    // and there is no X on it to dismiss it with.
    private func hideCorner() {
        guard cornerShown else { return }
        cornerShown = false
        cornerWrap.isHidden = true
        bloomWork?.cancel(); bloomWork = nil; bloomed = false
        if spotFlush { reportTop(0) }
        web?.evaluateJavaScript("window.__adCorner && __adCorner(false)", completionHandler: nil)
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

    /* THE L. Upright the ad is a banner welded to the top edge, and the video
       does not swell the whole of it - only the PLAYER'S COLUMN drops, like a
       tab pulled down out of the band, and the rest of the band stays exactly
       where it was. That is a smaller hole in the drawing than a full-width
       card of the same height: 64 across plus a 120-wide tongue, against 120
       across everything.
       The player is a 120 SQUARE, AdMob's floor in both directions and the
       narrowest a tab can be and still be served video at all. A 16:9
       creative letterboxes inside it; that is the price of the narrow tab and
       it is a conscious one. */
    private func buildFlushCard(_ ad: NativeAd) {
        // 213x120: AdMob's floor is 120 in BOTH directions, and 213 is 16:9 at
        // that height - the narrowest tab that is video-eligible AND fills
        // its frame with the landscape creative the loader asks for. A 120
        // square qualified too, but letterboxed every 16:9 ad inside it.
        let GUT: CGFloat = 8, PADR: CGFloat = 8, PW: CGFloat = 213, PHT: CGFloat = 120
        let screenW = host?.view.safeAreaLayoutGuide.layoutFrame.width
            ?? host?.view.bounds.width ?? 390
        let textW = max(screenW - PW - GUT - PADR - GUT, 40)

        let adv = NativeAdView()
        adv.translatesAutoresizingMaskIntoConstraints = false
        adv.backgroundColor = .clear

        // the band: the whole width, the height the headline asks for
        let bandBg = UIView()
        bandBg.translatesAutoresizingMaskIntoConstraints = false
        bandBg.backgroundColor = bgCol

        let badge = badgeLabel()
        let head = UILabel()
        head.font = .systemFont(ofSize: 11)
        head.textColor = UIColor(red: 0xE8/255.0, green: 0xE6/255.0, blue: 0xE1/255.0, alpha: 1)
        head.lineBreakMode = .byTruncatingTail
        head.numberOfLines = 2
        head.text = ad.headline
        head.translatesAutoresizingMaskIntoConstraints = false
        headV = head

        let textCol = UIView()
        textCol.translatesAutoresizingMaskIntoConstraints = false
        textCol.addSubview(badge); textCol.addSubview(head)

        // the tab: the player's column, the band's height at rest and the
        // square's when it is open. Same colour as the band, so the two read
        // as one L rather than as a card with a box on it.
        // THE TAB WEARS THE SAME HAIRLINE the band does, and turns the corner
        // where its right edge meets its bottom. Without an outline the
        // tongue had nothing between it and the picture but a colour change,
        // which on a dark drawing is no edge at all. Its TOP corners stay
        // square: that edge is welded to the band.
        let tabClip = UIView()
        tabClip.translatesAutoresizingMaskIntoConstraints = false
        tabClip.backgroundColor = bgCol
        tabClip.clipsToBounds = true
        tabClip.layer.cornerRadius = 14
        tabClip.layer.maskedCorners = [.layerMinXMaxYCorner, .layerMaxXMaxYCorner]
        tabClip.layer.borderWidth = 1
        tabClip.layer.borderColor = UIColor(white: 1, alpha: 0.2).cgColor
        let media = MediaView()
        media.translatesAutoresizingMaskIntoConstraints = false

        adv.addSubview(bandBg); adv.addSubview(tabClip); adv.addSubview(textCol)
        tabClip.addSubview(media)

        NSLayoutConstraint.activate([
            bandBg.topAnchor.constraint(equalTo: adv.topAnchor),
            bandBg.leadingAnchor.constraint(equalTo: adv.leadingAnchor),
            bandBg.trailingAnchor.constraint(equalTo: adv.trailingAnchor),
            tabClip.topAnchor.constraint(equalTo: adv.topAnchor),
            tabClip.leadingAnchor.constraint(equalTo: adv.leadingAnchor),
            tabClip.widthAnchor.constraint(equalToConstant: PW),
            // the player keeps its full square whatever the tab is doing -
            // that is what makes the card video-eligible - and the tab CLIPS
            // it, centred, so a shut tab shows the middle of the picture
            media.centerYAnchor.constraint(equalTo: tabClip.centerYAnchor),
            media.leadingAnchor.constraint(equalTo: tabClip.leadingAnchor),
            media.widthAnchor.constraint(equalToConstant: PW),
            media.heightAnchor.constraint(equalToConstant: PHT),
            textCol.leadingAnchor.constraint(equalTo: tabClip.trailingAnchor, constant: GUT),
            textCol.widthAnchor.constraint(equalToConstant: textW),
            badge.topAnchor.constraint(equalTo: textCol.topAnchor),
            badge.leadingAnchor.constraint(equalTo: textCol.leadingAnchor),
            badge.widthAnchor.constraint(equalToConstant: 22),
            badge.heightAnchor.constraint(equalToConstant: 13),
            head.topAnchor.constraint(equalTo: badge.bottomAnchor, constant: 4),
            head.leadingAnchor.constraint(equalTo: textCol.leadingAnchor),
            head.widthAnchor.constraint(equalToConstant: textW),
            head.bottomAnchor.constraint(equalTo: textCol.bottomAnchor),
        ])

        // HOW TALL THE BAND IS is measured, not typed: the headline is the
        // auction's words at the viewer's own text size, so it grows when
        // they do. 64 is the floor - the height asked for - and the measure
        // only ever raises it, so a large text size gets its second line
        // instead of losing it.
        textCol.setNeedsLayout(); textCol.layoutIfNeeded()
        let want = textCol.systemLayoutSizeFitting(
            CGSize(width: textW, height: 0),
            withHorizontalFittingPriority: .required,
            verticalFittingPriority: .fittingSizeLevel).height + 8
        flushRest = max(want, FLUSH_MIN)
        NSLayoutConstraint.activate([
            bandBg.heightAnchor.constraint(equalToConstant: flushRest),
            textCol.centerYAnchor.constraint(equalTo: bandBg.centerYAnchor),
        ])

        adv.mediaView = media
        adv.headlineView = head
        adv.nativeAd = ad
        badgeV = badge
        ctaV = nil

        cornerWrap.subviews.forEach { $0.removeFromSuperview() }
        cornerWrap.backgroundColor = .clear
        cornerWrap.clipsToBounds = false
        cornerWrap.layer.cornerRadius = 0
        cornerWrap.layer.shadowOpacity = 0
        cardClip = nil
        cornerWrap.addSubview(adv)
        cornerW?.isActive = false; cornerH?.isActive = false
        mediaClipH?.isActive = false
        mediaClipH = tabClip.heightAnchor.constraint(equalToConstant: flushRest)
        mediaClipH?.isActive = true
        cardH = PHT                     // the tab, fully out
        cornerH = cornerWrap.heightAnchor.constraint(equalToConstant: PHT)
        NSLayoutConstraint.activate([
            cornerH!,
            adv.topAnchor.constraint(equalTo: cornerWrap.topAnchor),
            adv.leadingAnchor.constraint(equalTo: cornerWrap.leadingAnchor),
            adv.trailingAnchor.constraint(equalTo: cornerWrap.trailingAnchor),
            adv.bottomAnchor.constraint(equalTo: cornerWrap.bottomAnchor),
        ])
        // the fillet sits exactly on the inner corner and shows only when the
        // tab is out - there is no corner to soften while it is shut
        let fil = Fillet()
        fil.translatesAutoresizingMaskIntoConstraints = false
        fil.backgroundColor = .clear
        fil.isOpaque = false
        fil.fillCol = bgCol
        fil.isHidden = true
        fil.isUserInteractionEnabled = false
        adv.addSubview(fil)
        NSLayoutConstraint.activate([
            fil.leadingAnchor.constraint(equalTo: tabClip.trailingAnchor),
            fil.topAnchor.constraint(equalTo: tabClip.bottomAnchor),
            fil.widthAnchor.constraint(equalToConstant: 14),
            fil.heightAnchor.constraint(equalToConstant: 14),
        ])
        filletV = fil
        tabV = tabClip
        cornerWrap.bandH = flushRest
        cornerWrap.tabW = PW
        cornerWrap.isL = true
        cardV = adv
        viewMode = "corner"
        applyCornerGeometry()
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
        if spotFlush { buildFlushCard(ad); return }
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

        // THE CARD IS EXACTLY THE VIDEO MINIMUM TALL - 120pt, AdMob's floor
        // for a media view to be video-eligible at all - and nothing is
        // allowed to grow it: the headline stands BESIDE the player, never
        // under it, whatever that costs the headline.
        //
        // Width is then set by how far it may reach: the screen, less what a
        // flanking chrome button takes on each side and a FINGERTIP clear of
        // it. It used to stop 12pt short, under 2mm - the adjacency the ad
        // network reads as an accidental-click layout, and close enough for a
        // thumb going for Download to catch the ad. FLANK is one standard
        // touch target, ~7.6mm.
        //
        // The collapse pill has no LANE; it floats at the card's top-right
        // corner, clear of the badge (left-aligned) and above the centred
        // headline - 28pt the headline gets to keep.
        let GUT: CGFloat = 8, PADR: CGFloat = 8, PH: CGFloat = 120
        // FLANKW is the pill's width: it is one of the app's ordinary buttons
        // wide, because that is what each of its halves is
        let FLANK: CGFloat = 48, FLANKW: CGFloat = 8 + 44
        let screenW = host?.view.bounds.width ?? 390
        let flush = false          // buildFlushCard owns the upright shape
        let budget = screenW - (FLANKW + FLANK) - 8
        // SIDEWAYS THE CARD STANDS UP: there is no room beside a wide card on
        // a short screen, so the headline goes UNDER the player and the card
        // is taller than it is wide. Upright it lies down, where the width
        // across the top is free and the height is not.
        // standing up it was 136 wide and 164 tall, which left the header
        // about 70pt of headline and the player no more than its floor.
        // Sideways there is height to spare on a canvas screen, so the player
        // gets a 4:3 frame and the header a line it can read on.
        // flush is a LYING-DOWN card too - it just gets the whole width
        let tall = spotLeft && !flush
        // narrow and tall: a landscape screen has height to spare down its
        // edge and none of the width the flat card wants. 144x190 of player,
        // clear of the 120x120 video floor, under a 46pt header.
        let TALLW: CGFloat = 160, TALLPH: CGFloat = 190, TALLHDR: CGFloat = 46
        // 106, down from 118: the headline gives up about three characters a
        // line so the player can have that width instead - and the player's width is the BUDGET's leftover, not a flat 120. 120 is
        // AdMob's video FLOOR, not a target, and pinning the width to it while
        // capping the headline left 49dp of the allowance unspent on a 411dp
        // phone and 68 on a 430 - so a 16:9 creative letterboxed into a square
        // and rendered 120x67 with black above and below. Handing the leftover
        // to the player makes that 181x101 on the same phone: two and a third
        // times the picture, in the same card, with the same clearance.
        let TEXTWANT: CGFloat = 106, PLAYERMAX: CGFloat = 213   // 16:9 at 120
        let playerW: CGFloat = tall ? TALLW - 16
            : min(max(budget - GUT - PADR - TEXTWANT, 120), PLAYERMAX)
        // ...and flush lets the text take what the player leaves, uncapped, so
        // the banner actually reaches both edges instead of stopping short
        // with a band of empty card on the right
        let textW = tall ? playerW
            : (flush ? max(budget - playerW - GUT - PADR, 40)
                     : min(max(budget - playerW - GUT - PADR, 40), TEXTWANT))
        let advW = tall ? TALLW : playerW + GUT + textW + PADR
        let advH = tall ? TALLPH + TALLHDR : PH

        head.numberOfLines = 3
        headV = head
        let mediaClip = UIView()
        mediaClip.translatesAutoresizingMaskIntoConstraints = false
        mediaClip.clipsToBounds = true
        adv.addSubview(mediaClip); mediaClip.addSubview(media)
        adv.addSubview(badge); adv.addSubview(head)
        NSLayoutConstraint.activate([
            adv.widthAnchor.constraint(equalToConstant: advW),
            adv.heightAnchor.constraint(equalToConstant: advH),
            // the clip is flush with the card and follows its height; the
            // player keeps its full 120pt square inside it whatever the card
            // is doing - that is what makes it video-eligible - so the resting
            // banner shows the MIDDLE of the creative, not the top of it
            mediaClip.topAnchor.constraint(equalTo: adv.topAnchor, constant: tall ? TALLHDR : 0),
            mediaClip.leadingAnchor.constraint(equalTo: adv.leadingAnchor,
                                               constant: tall ? 8 : 0),
            mediaClip.widthAnchor.constraint(equalToConstant: playerW),
            media.centerYAnchor.constraint(equalTo: mediaClip.centerYAnchor),
            media.leadingAnchor.constraint(equalTo: mediaClip.leadingAnchor),
            media.widthAnchor.constraint(equalToConstant: playerW),
            media.heightAnchor.constraint(equalToConstant: tall ? TALLPH : PH),
            badge.widthAnchor.constraint(equalToConstant: 22),
            badge.heightAnchor.constraint(equalToConstant: 13),
        ])
        if tall {
            // standing up, the badge and headline sit ABOVE the player: the
            // resting banner is a 48pt slice of the card, and with the header
            // underneath that slice was a piece of the picture and nothing
            // else - no "Ad", no headline, which is a required asset
            head.numberOfLines = 2
            NSLayoutConstraint.activate([
                badge.leadingAnchor.constraint(equalTo: adv.leadingAnchor, constant: 8),
                badge.topAnchor.constraint(equalTo: adv.topAnchor, constant: 8),
                head.leadingAnchor.constraint(equalTo: badge.trailingAnchor, constant: 5),
                // the header used to stop 32pt short of the corner, where the
                // collapse pill sat; there is no pill now, so it gets it back
                head.trailingAnchor.constraint(equalTo: adv.trailingAnchor, constant: -8),
                head.centerYAnchor.constraint(equalTo: badge.centerYAnchor),
            ])
        } else {
            // badge + headline ride as one block in a column of their own,
            // centred on the PLAYER'S CLIP rather than on the card. The clip
            // is what shrinks to the band, so centring on it puts the text in
            // the middle of whatever is on show - pinned 26pt below the card's
            // top they sat BELOW a 48pt band and the banner came out as a
            // slice of empty card with no "Ad" and no headline in it.
            badge.removeFromSuperview(); head.removeFromSuperview()
            let textCol = UIView()
            textCol.translatesAutoresizingMaskIntoConstraints = false
            adv.addSubview(textCol)
            textCol.addSubview(badge); textCol.addSubview(head)
            NSLayoutConstraint.activate([
                textCol.leadingAnchor.constraint(equalTo: mediaClip.trailingAnchor, constant: GUT),
                textCol.widthAnchor.constraint(equalToConstant: textW),
                textCol.centerYAnchor.constraint(equalTo: mediaClip.centerYAnchor),
                badge.topAnchor.constraint(equalTo: textCol.topAnchor),
                badge.leadingAnchor.constraint(equalTo: textCol.leadingAnchor),
                head.leadingAnchor.constraint(equalTo: textCol.leadingAnchor),
                head.widthAnchor.constraint(equalToConstant: textW),
                head.topAnchor.constraint(equalTo: badge.bottomAnchor, constant: 4),
                head.bottomAnchor.constraint(equalTo: textCol.bottomAnchor),
            ])
        }
        adv.mediaView = media
        adv.headlineView = head
        adv.nativeAd = ad

        // the wrapper IS the card: it carries the skin, and holds the ad view
        // and the pill side by side inside it
        // The wrapper is what the animation resizes, and it carries the drop
        // shadow - which a view cannot have while it clips. So the SKIN and
        // the crop move inside, to a clip pinned to all four of the wrapper's
        // edges: the card keeps its full height inside that clip, and the
        // banner is a genuine crop of it rather than a full-size card with a
        // short background painted behind it.
        // the wrapper keeps the background even though the clip in front of it
        // paints the same colour: a layer with a CLEAR background casts no
        // shadow, and the shadow is the whole reason the crop had to move off
        // this view in the first place
        cornerWrap.backgroundColor = bgCol
        cornerWrap.layer.cornerRadius = 14
        cornerWrap.layer.shadowColor = UIColor.black.cgColor
        cornerWrap.layer.shadowOpacity = 0.5
        cornerWrap.layer.shadowRadius = 12
        cornerWrap.layer.shadowOffset = CGSize(width: 0, height: 4)
        let clip = UIView()
        clip.translatesAutoresizingMaskIntoConstraints = false
        clip.backgroundColor = bgCol
        clip.clipsToBounds = true
        clip.layer.cornerRadius = flush ? 0 : 14
        clip.layer.borderWidth = 1
        clip.layer.borderColor = UIColor(white: 1, alpha: 0.12).cgColor
        cornerWrap.addSubview(clip)
        cornerWrap.isL = false          // a rectangle: no corner to hand back
        cardClip = clip
        NSLayoutConstraint.activate([
            clip.topAnchor.constraint(equalTo: cornerWrap.topAnchor),
            clip.bottomAnchor.constraint(equalTo: cornerWrap.bottomAnchor),
            clip.leadingAnchor.constraint(equalTo: cornerWrap.leadingAnchor),
            clip.trailingAnchor.constraint(equalTo: cornerWrap.trailingAnchor),
        ])
        clip.addSubview(adv)
        cornerW?.isActive = false; cornerH?.isActive = false
        cornerW = cornerWrap.widthAnchor.constraint(equalToConstant: advW)
        cornerW?.isActive = !flush            // flush takes both safe-area edges
        // THE CLIP IS THE CROP and must track the band, or the banner comes
        // out as a slice of a full-size card. The PLAYER inside it does not
        // shrink - it keeps the 120pt height that makes the card
        // video-eligible at all, centred in the clip - so a short band shows
        // the MIDDLE of the creative rather than its top edge.
        mediaClipH?.isActive = false
        mediaClipH = mediaClip.heightAnchor.constraint(
            equalTo: cornerWrap.heightAnchor, constant: tall ? -TALLHDR : 0)
        mediaClipH?.isActive = true
        cardH = advH
        cornerH = cornerWrap.heightAnchor.constraint(
            equalToConstant: flush ? restH : advH)
        NSLayoutConstraint.activate([
            cornerH!,
            adv.topAnchor.constraint(equalTo: clip.topAnchor),
            adv.leadingAnchor.constraint(equalTo: clip.leadingAnchor),
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
            // a creative with video in it earns the band an opening, but not
            // oftener than once every four minutes
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { [weak self] in
                self?.bloomTry()
            }
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

extension AdController: VideoControllerDelegate {
    // the band closes as soon as the video is over, rather than sitting open
    // for the full 32 seconds against a still frame
    func videoControllerDidEndVideoPlayback(_ videoController: VideoController) {
        DispatchQueue.main.async { [weak self] in self?.bloomSet(false) }
    }
}

extension AdController: UIGestureRecognizerDelegate {
    // passive observer: never steal or delay the page's own touches
    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                           shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool {
        return true
    }
}
