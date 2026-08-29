import UIKit
import WebKit

// The iOS shell, mirroring the Android MainActivity's contract: a black
// edge, the web app inset from the system bars, served from the loopback
// origin so the artist's saved work survives every update. The native
// camera pipeline and the ad card arrive in later rounds; until then the
// page's own browser paths (file inputs, getUserMedia) carry the load.
final class ViewController: UIViewController {
    private var web: WKWebView!
    private var dlDest: URL?

    override var preferredStatusBarStyle: UIStatusBarStyle { .lightContent }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black

        let cfg = WKWebViewConfiguration()
        cfg.allowsInlineMediaPlayback = true
        cfg.mediaTypesRequiringUserActionForPlayback = []
        cfg.websiteDataStore = .default()

        web = WKWebView(frame: .zero, configuration: cfg)
        web.uiDelegate = self
        web.navigationDelegate = self
        web.isOpaque = false
        web.backgroundColor = .black
        web.scrollView.backgroundColor = .black
        web.scrollView.bounces = false
        web.scrollView.contentInsetAdjustmentBehavior = .never
        web.allowsBackForwardNavigationGestures = false
        #if DEBUG
        if #available(iOS 16.4, *) { web.isInspectable = true }
        #endif

        web.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(web)
        NSLayoutConstraint.activate([
            web.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            web.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor),
            web.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            web.trailingAnchor.constraint(equalTo: view.trailingAnchor),
        ])

        let port = LocalServer.shared.start()
        if port == 0 {
            let l = UILabel()
            l.text = "local server failed to bind"
            l.textColor = .white
            l.translatesAutoresizingMaskIntoConstraints = false
            view.addSubview(l)
            l.centerXAnchor.constraint(equalTo: view.centerXAnchor).isActive = true
            l.centerYAnchor.constraint(equalTo: view.centerYAnchor).isActive = true
            return
        }
        web.load(URLRequest(url: URL(string: "http://127.0.0.1:\(port)/index.html")!))
    }

    private func share(_ url: URL?) {
        guard let url else { return }
        DispatchQueue.main.async {
            let av = UIActivityViewController(activityItems: [url], applicationActivities: nil)
            av.popoverPresentationController?.sourceView = self.view
            av.popoverPresentationController?.sourceRect =
                CGRect(x: self.view.bounds.midX, y: self.view.bounds.midY, width: 1, height: 1)
            self.present(av, animated: true)
        }
    }
}

extension ViewController: WKNavigationDelegate {
    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else { return decisionHandler(.allow) }
        let scheme = url.scheme ?? ""
        let local = url.host == "127.0.0.1" || scheme == "about" || scheme == "blob" || scheme == "data"
        if local {
            if navigationAction.shouldPerformDownload { decisionHandler(.download) }
            else { decisionHandler(.allow) }
            return
        }
        // anything off the loopback origin leaves for the real browser
        UIApplication.shared.open(url)
        decisionHandler(.cancel)
    }

    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationResponse: WKNavigationResponse,
                 decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        if !navigationResponse.canShowMIMEType { decisionHandler(.download) }
        else { decisionHandler(.allow) }
    }

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
        download.delegate = self
    }

    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
        download.delegate = self
    }
}

extension ViewController: WKDownloadDelegate {
    // exports land in a scratch file and go straight to the share sheet -
    // Save Image / Files / AirDrop are all the same door on iOS
    func download(_ download: WKDownload,
                  decideDestinationUsing response: URLResponse,
                  suggestedFilename: String,
                  completionHandler: @escaping (URL?) -> Void) {
        let dir = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let name = suggestedFilename.isEmpty ? "photorealism.png" : suggestedFilename
        let dest = dir.appendingPathComponent(name)
        dlDest = dest
        completionHandler(dest)
    }

    func downloadDidFinish(_ download: WKDownload) {
        share(dlDest)
        dlDest = nil
    }

    func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
        dlDest = nil
    }
}

extension ViewController: WKUIDelegate {
    func webView(_ webView: WKWebView,
                 createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction,
                 windowFeatures: WKWindowFeatures) -> WKWebView? {
        // target=_blank links (privacy policy, help) open in Safari
        if let url = navigationAction.request.url { UIApplication.shared.open(url) }
        return nil
    }

    @available(iOS 15.0, *)
    func webView(_ webView: WKWebView,
                 requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                 initiatedByFrame frame: WKFrameInfo,
                 type: WKMediaCaptureType,
                 decisionHandler: @escaping (WKPermissionDecision) -> Void) {
        // the OS-level camera prompt still governs; don't double-ask per page
        decisionHandler(.grant)
    }
}
