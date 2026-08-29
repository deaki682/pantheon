import Foundation
import WebKit
import StoreKit

// Remove Ads on Apple: one non-consumable, the same contract the page
// already speaks. StoreKit 2 verifies entitlements against Apple's own
// transaction records on every launch, so the purchase survives
// reinstalls and new phones with no restore button needed.
final class StoreController {
    static let PRODUCT = "remove_ads"
    static var removed: Bool { UserDefaults.standard.bool(forKey: "noads") }

    private weak var web: WKWebView?
    private weak var ads: AdController?

    init(web: WKWebView, ads: AdController?) {
        self.web = web
        self.ads = ads
        Task { await self.listenForUpdates() }
        Task { await self.refreshEntitlement() }
    }

    // Apple's record is the truth: grant (or re-grant) on every launch
    private func refreshEntitlement() async {
        for await result in Transaction.currentEntitlements {
            if case .verified(let tx) = result, tx.productID == Self.PRODUCT,
               tx.revocationDate == nil {
                await grant()
            }
        }
    }

    // purchases can land from outside the app (ask-to-buy, other devices)
    private func listenForUpdates() async {
        for await result in Transaction.updates {
            if case .verified(let tx) = result {
                if tx.productID == Self.PRODUCT && tx.revocationDate == nil {
                    await grant()
                }
                await tx.finish()
            }
        }
    }

    func buy() {
        Task {
            do {
                guard let product = try await Product.products(for: [Self.PRODUCT]).first else {
                    await self.say("purchase not available yet", ok: false)
                    return
                }
                let result = try await product.purchase()
                switch result {
                case .success(let verification):
                    if case .verified(let tx) = verification {
                        await self.grant()
                        await tx.finish()
                    }
                case .pending:
                    await self.say("purchase pending approval", ok: true)
                case .userCancelled:
                    break
                @unknown default:
                    break
                }
            } catch {
                await self.say("purchase failed - try again", ok: false)
            }
        }
    }

    @MainActor
    private func grant() {
        let first = !Self.removed
        UserDefaults.standard.set(true, forKey: "noads")
        ads?.disable()
        if first {
            web?.evaluateJavaScript("window.__adsRemovedUI && __adsRemovedUI()",
                                    completionHandler: nil)
        }
    }

    @MainActor
    private func say(_ msg: String, ok: Bool) {
        let esc = msg.replacingOccurrences(of: "'", with: "")
        web?.evaluateJavaScript("toast && toast('\(esc)', \(ok ? "true" : "false"))",
                                completionHandler: nil)
    }
}
