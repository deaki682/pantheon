import Foundation

// The page is served from a real loopback HTTP socket, mirroring the Android
// shell: a genuine http://127.0.0.1 origin gets first-class localStorage/
// IndexedDB, and the artist's whole world (references, drawings, settings)
// is keyed to the 127.0.0.1:<port> ORIGIN - so the port is pinned to 8399
// for the life of the install, bound with reuseAddress and real patience.
// A last-resort ephemeral port serves only the current session and is never
// remembered, so the next launch finds the real data again.
final class LocalServer {
    static let shared = LocalServer()
    private(set) var port: UInt16 = 0
    private(set) var degraded = false
    private var fd: Int32 = -1
    private let webRoot = Bundle.main.resourceURL!.appendingPathComponent("draw", isDirectory: true)

    // captures are far too large for evaluateJavaScript: the native side
    // parks them here and the page fetches /__cap/<id> exactly once
    private var store: [String: (mime: String, bytes: Data)] = [:]
    private var nextId = 1
    private let lock = NSLock()

    func park(mime: String, bytes: Data) -> String {
        lock.lock(); defer { lock.unlock() }
        let id = "c\(nextId)"; nextId += 1
        store[id] = (mime, bytes)
        // a dropped delivery must not pool megabytes: keep only the newest few
        if store.count > 6 {
            let doomed = store.keys
                .sorted { (Int($0.dropFirst()) ?? 0) < (Int($1.dropFirst()) ?? 0) }
                .prefix(store.count - 6)
            for k in doomed { store.removeValue(forKey: k) }
        }
        return "/__cap/" + id
    }

    private func takeParked(_ id: String) -> (mime: String, bytes: Data)? {
        lock.lock(); defer { lock.unlock() }
        return store.removeValue(forKey: id)
    }

    @discardableResult
    func start() -> UInt16 {
        if fd >= 0 { return port }
        let home: UInt16 = 8399
        var s: Int32 = -1
        for _ in 0..<12 {
            s = bindAt(home)
            if s >= 0 { break }
            usleep(250_000)
        }
        degraded = s < 0
        if s < 0 { s = bindAt(0) }
        guard s >= 0 else { return 0 }
        fd = s
        var addr = sockaddr_in()
        var len = socklen_t(MemoryLayout<sockaddr_in>.size)
        _ = withUnsafeMutablePointer(to: &addr) { p in
            p.withMemoryRebound(to: sockaddr.self, capacity: 1) { getsockname(s, $0, &len) }
        }
        port = UInt16(bigEndian: addr.sin_port)
        Thread.detachNewThread { [weak self] in self?.acceptLoop() }
        return port
    }

    private func bindAt(_ p: UInt16) -> Int32 {
        let s = socket(AF_INET, SOCK_STREAM, 0)
        guard s >= 0 else { return -1 }
        var on: Int32 = 1
        setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &on, socklen_t(MemoryLayout<Int32>.size))
        var addr = sockaddr_in()
        addr.sin_family = sa_family_t(AF_INET)
        addr.sin_port = p.bigEndian
        addr.sin_addr.s_addr = inet_addr("127.0.0.1")
        let ok = withUnsafePointer(to: &addr) { ptr in
            ptr.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                bind(s, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        if ok != 0 || listen(s, 16) != 0 { close(s); return -1 }
        return s
    }

    private func acceptLoop() {
        while fd >= 0 {
            let c = accept(fd, nil, nil)
            if c < 0 { continue }
            Thread.detachNewThread { [weak self] in self?.handle(c) }
        }
    }

    private func handle(_ c: Int32) {
        defer { close(c) }
        // read until the end of the request headers (or a sane cap)
        var req = Data()
        var buf = [UInt8](repeating: 0, count: 4096)
        while req.count < 64 * 1024 {
            let n = read(c, &buf, buf.count)
            if n <= 0 { break }
            req.append(contentsOf: buf[0..<n])
            if req.range(of: Data([13, 10, 13, 10])) != nil { break }
        }
        guard let head = String(data: req, encoding: .utf8) ?? String(data: req, encoding: .isoLatin1),
              let first = head.components(separatedBy: "\r\n").first else { return }
        let parts = first.components(separatedBy: " ")
        guard parts.count >= 2, parts[0] == "GET" else {
            send(c, "HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".data(using: .utf8)!)
            return
        }
        var path = parts[1]
        if let q = path.firstIndex(where: { $0 == "?" || $0 == "#" }) { path = String(path[..<q]) }
        if path == "/" { path = "/index.html" }
        path = String(path.drop(while: { $0 == "/" }))
        if path.contains("..") { path = "index.html" }

        if path.hasPrefix("__cap/") {
            if let hit = takeParked(String(path.dropFirst("__cap/".count))) {
                var r = "HTTP/1.1 200 OK\r\nContent-Type: \(hit.mime)\r\n"
                r += "Content-Length: \(hit.bytes.count)\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n"
                send(c, r.data(using: .utf8)! + hit.bytes)
            } else {
                send(c, "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".data(using: .utf8)!)
            }
            return
        }

        let file = webRoot.appendingPathComponent(path)
        if let bytes = try? Data(contentsOf: file) {
            var r = "HTTP/1.1 200 OK\r\nContent-Type: \(mime(path))\r\n"
            r += "Content-Length: \(bytes.count)\r\nCache-Control: no-cache\r\nConnection: close\r\n\r\n"
            send(c, r.data(using: .utf8)! + bytes)
        } else {
            send(c, "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".data(using: .utf8)!)
        }
    }

    private func send(_ c: Int32, _ data: Data) {
        data.withUnsafeBytes { (raw: UnsafeRawBufferPointer) in
            var off = 0
            while off < raw.count {
                let n = write(c, raw.baseAddress!.advanced(by: off), raw.count - off)
                if n <= 0 { break }
                off += n
            }
        }
    }

    private func mime(_ p: String) -> String {
        if p.hasSuffix(".html") { return "text/html; charset=utf-8" }
        if p.hasSuffix(".js") { return "application/javascript" }
        if p.hasSuffix(".webmanifest") || p.hasSuffix(".json") { return "application/json" }
        if p.hasSuffix(".png") { return "image/png" }
        if p.hasSuffix(".jpg") || p.hasSuffix(".jpeg") { return "image/jpeg" }
        if p.hasSuffix(".svg") { return "image/svg+xml" }
        if p.hasSuffix(".txt") { return "text/plain" }
        return "application/octet-stream"
    }
}
