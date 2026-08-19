package app.realism.draw

import android.content.Context
import java.io.BufferedOutputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket

// The page is served from a real loopback HTTP socket instead of a WebView
// request interceptor: interception proved unreliable on at least one real
// device (the main frame fell through to the network), and a genuine
// http://127.0.0.1 origin gets first-class localStorage/IndexedDB. The port
// is remembered so the origin - and with it the artist's saved work - stays
// stable across launches.
object LocalServer {
    var port = 0; private set
    private var server: ServerSocket? = null

    // captures are far too large for evaluateJavascript: the native side
    // parks them here and the page fetches /__cap/<id> exactly once
    private val store = java.util.concurrent.ConcurrentHashMap<String, Pair<String, ByteArray>>()
    private val ids = java.util.concurrent.atomic.AtomicInteger(1)
    fun park(mime: String, bytes: ByteArray): String {
        val id = "c" + ids.getAndIncrement()
        store[id] = Pair(mime, bytes)
        return "/__cap/" + id
    }

    fun start(ctx: Context): Int {
        server?.let { if (!it.isClosed) return port }
        val prefs = ctx.getSharedPreferences("srv", 0)
        val remembered = prefs.getInt("port", 8399)
        var ss: ServerSocket? = null
        for (p in intArrayOf(remembered, 8399, 8517, 8641, 0)) {
            try { ss = ServerSocket(p, 16, InetAddress.getByName("127.0.0.1")); break }
            catch (e: Exception) {}
        }
        val s = ss ?: return 0
        server = s; port = s.localPort
        prefs.edit().putInt("port", port).apply()
        val app = ctx.applicationContext
        Thread {
            while (!s.isClosed) {
                try {
                    val c = s.accept()
                    Thread { handle(app, c) }.apply { isDaemon = true }.start()
                } catch (e: Exception) {}
            }
        }.apply { isDaemon = true }.start()
        return port
    }

    private fun mime(p: String) = when {
        p.endsWith(".html") -> "text/html; charset=utf-8"
        p.endsWith(".js") -> "application/javascript"
        p.endsWith(".webmanifest") || p.endsWith(".json") -> "application/json"
        p.endsWith(".png") -> "image/png"
        p.endsWith(".jpg") || p.endsWith(".jpeg") -> "image/jpeg"
        p.endsWith(".svg") -> "image/svg+xml"
        else -> "application/octet-stream"
    }

    private fun handle(ctx: Context, sock: Socket) {
        try {
            sock.use { c ->
                val br = c.getInputStream().bufferedReader()
                val first = br.readLine() ?: return
                while (true) { val h = br.readLine() ?: break; if (h.isEmpty()) break }
                val out = BufferedOutputStream(c.getOutputStream())
                var path = Regex("^GET\\s+([^\\s?#]+)").find(first)?.groupValues?.get(1) ?: "/"
                if (path == "/") path = "/index.html"
                path = path.removePrefix("/")
                if (path.contains("..")) path = "index.html"
                if (path.startsWith("__cap/")) {
                    val hit = store.remove(path.removePrefix("__cap/"))
                    if (hit == null) {
                        sock.getOutputStream().write(
                            "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".toByteArray())
                    } else {
                        out.write(("HTTP/1.1 200 OK\r\nContent-Type: ${hit.first}\r\n" +
                            "Content-Length: ${hit.second.size}\r\nCache-Control: no-store\r\n" +
                            "Connection: close\r\n\r\n").toByteArray())
                        out.write(hit.second)
                    }
                    out.flush()
                    return
                }
                val bytes = try { ctx.assets.open(path).use { it.readBytes() } } catch (e: Exception) { null }
                if (bytes == null) {
                    out.write("HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".toByteArray())
                } else {
                    out.write(("HTTP/1.1 200 OK\r\nContent-Type: ${mime(path)}\r\n" +
                        "Content-Length: ${bytes.size}\r\nCache-Control: no-cache\r\n" +
                        "Connection: close\r\n\r\n").toByteArray())
                    out.write(bytes)
                }
                out.flush()
            }
        } catch (e: Exception) {}
    }
}
