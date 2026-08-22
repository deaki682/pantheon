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
        // a dropped delivery must not pool megabytes: keep only the newest few
        if (store.size > 6)
            store.keys.sortedBy { it.substring(1).toIntOrNull() ?: 0 }
                .take(store.size - 6).forEach { store.remove(it) }
        return "/__cap/" + id
    }

    @Volatile var degraded = false; private set
    fun start(ctx: Context): Int {
        server?.let { if (!it.isClosed) return port }
        // the page's whole world (references, drawings, settings) is keyed
        // to the 127.0.0.1:<port> ORIGIN, so the port must never drift. The
        // old logic fell through to a fallback port on any bind failure -
        // including the transient one when Android kills the app and it
        // relaunches before the OS releases the socket - and then PERSISTED
        // the fallback: a different origin, which looks like a factory
        // reset. The home port is now pinned for the life of the install
        // (8399, what every install started on), bound with reuseAddress
        // and real patience; a last-resort ephemeral port serves only the
        // current session and is never remembered, so the next launch
        // finds the real data again.
        val prefs = ctx.getSharedPreferences("srv", 0)
        val home = prefs.getInt("home", 8399)
        prefs.edit().putInt("home", home).remove("port").apply()
        fun bindAt(p: Int): ServerSocket? = try {
            val t = ServerSocket()
            t.reuseAddress = true
            t.bind(java.net.InetSocketAddress(InetAddress.getByName("127.0.0.1"), p), 16)
            t
        } catch (e: Exception) { null }
        var ss: ServerSocket? = null
        for (i in 0 until 12) {
            ss = bindAt(home)
            if (ss != null) break
            try { Thread.sleep(250) } catch (e: InterruptedException) {}
        }
        degraded = ss == null
        if (ss == null) ss = bindAt(0)
        val s = ss ?: return 0
        server = s; port = s.localPort
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
