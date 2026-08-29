package app.realism.draw

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.util.Base64
import android.view.Surface
import android.webkit.JavascriptInterface
import android.net.Uri
import android.webkit.PermissionRequest
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.util.Log
import android.widget.FrameLayout
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.FocusMeteringAction
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.core.resolutionselector.AspectRatioStrategy
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.extensions.ExtensionMode
import androidx.camera.extensions.ExtensionsManager
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import java.util.concurrent.Executors

// The web app is the whole product; this activity only lends it two things a
// browser cannot give: the platform's real photo pipeline, and a live preview
// BEHIND the page (the page goes transparent over it, so the ghost overlay
// stays exactly the HTML it already is).
class MainActivity : AppCompatActivity() {
    private lateinit var web: WebView
    private lateinit var previewView: PreviewView
    private var provider: ProcessCameraProvider? = null
    private var imageCapture: ImageCapture? = null
    private var camera: androidx.camera.core.Camera? = null
    private val captureExec = Executors.newSingleThreadExecutor()
    private var pendingStart: Runnable? = null
    private var capLabel = ""
    private var rawMode = false
    // freshest lens-shading gain map from the preview's repeating request;
    // rawLuma divides the lens's real corner falloff out of the RAW plane
    @Volatile private var shadeMap: android.hardware.camera2.params.LensShadingMap? = null
    private var modeAnnounced = false
    private lateinit var diag: TextView
    private var booted = false
    // ---- ads: one NATIVE card styled as part of the app, visible only
    // while the page reports the project screen up. Register the dev
    // phone as a test device in the AdMob console before poking at it.
    private lateinit var adWrap: FrameLayout
    private var adWanted = false
    private var adsUp = false
    private var adShownH = 0
    private var nativeAd: com.google.android.gms.ads.nativead.NativeAd? = null
    @Volatile private var adAccentCol = 0xFFE8833A.toInt()   // follows the app accent
    @Volatile private var adBgCol = 0xFF141414.toInt()        // follows the screen backdrop
    private var adCard: com.google.android.gms.ads.nativead.NativeAdView? = null

    private fun report(msg: String) {
        Log.e("Realism", msg)
        runOnUiThread {
            if (!::diag.isInitialized) return@runOnUiThread
            diag.visibility = android.view.View.VISIBLE
            diag.append(msg + "\n")
            diag.setOnClickListener { diag.visibility = android.view.View.GONE }
            diag.removeCallbacks(diagHide); diag.postDelayed(diagHide, 12000)
        }
    }
    private val diagHide = Runnable {
        diag.visibility = android.view.View.GONE; diag.text = ""
    }

    // "ask me where" downloads: the system file picker chooses the exact
    // destination; the bytes wait here between launch and result
    private var pendingSave: ByteArray? = null
    private val createDoc = registerForActivityResult(
        ActivityResultContracts.CreateDocument("image/jpeg")) { uri ->
        val bytes = pendingSave; pendingSave = null
        if (uri == null || bytes == null) {
            js("toast && toast('save cancelled', false)")
        } else try {
            contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
            js("toast && toast('saved')")
        } catch (e: Exception) { js("toast && toast('save failed', false)") }
    }

    private val askCamera = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) pendingStart?.run() else {
            report("camera permission denied")
            js("window.__natFail && __natFail('denied')")
        }
        pendingStart = null
    }

    // <input type=file> does NOTHING in a WebView unless the host runs the
    // chooser itself - the classic gotcha, and the reference picker's whole
    // upload path depends on it
    private var fileCb: ValueCallback<Array<Uri>>? = null
    private val pickFile = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { res ->
        fileCb?.onReceiveValue(
            WebChromeClient.FileChooserParams.parseResult(res.resultCode, res.data))
        fileCb = null
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        run {
            val prefs = getSharedPreferences("cam", 0)
            val prior = Thread.getDefaultUncaughtExceptionHandler()
            Thread.setDefaultUncaughtExceptionHandler { t, e ->
                try {
                    prefs.edit().putString("crash",
                        (e.toString() + "\n" + e.stackTrace.take(6).joinToString("\n"))
                            .take(600)).commit()
                } catch (x: Throwable) {}
                prior?.uncaughtException(t, e)
            }
        }
        val root = FrameLayout(this)
        // targetSdk 36 enforces edge-to-edge with no opt-out, so the layout
        // makes its own room: the root pads itself by the system-bar and
        // cutout insets, and everything inside (WebView + camera preview,
        // which share this coordinate space) sits between the bars exactly
        // as it did before enforcement. The padding band shows root black.
        root.setBackgroundColor(Color.BLACK)
        androidx.core.view.ViewCompat.setOnApplyWindowInsetsListener(root) { v, insets ->
            val b = insets.getInsets(
                androidx.core.view.WindowInsetsCompat.Type.systemBars() or
                androidx.core.view.WindowInsetsCompat.Type.displayCutout())
            v.setPadding(b.left, b.top, b.right, b.bottom)
            androidx.core.view.WindowInsetsCompat.CONSUMED
        }
        previewView = PreviewView(this).apply {
            visibility = android.view.View.GONE
            scaleType = PreviewView.ScaleType.FIT_CENTER
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
        }
        // opaque by default: a permanently transparent WebView fails to
        // composite on some devices (a black screen); transparency is only
        // needed while the native preview runs behind the page
        web = WebView(this).apply { setBackgroundColor(Color.BLACK) }
        WebView.setWebContentsDebuggingEnabled(true)
        root.addView(previewView, FrameLayout.LayoutParams(0, 0))
        root.addView(web, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT))
        diag = TextView(this).apply {
            visibility = android.view.View.GONE
            setBackgroundColor(0xCC000000.toInt())
            setTextColor(Color.WHITE)
            textSize = 12f
            setPadding(24, 48, 24, 24)
        }
        root.addView(diag, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT))
        adWrap = FrameLayout(this)
        adWrap.visibility = android.view.View.GONE
        root.addView(adWrap, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT,
            android.view.Gravity.BOTTOM))
        setContentView(root)
        run {
            val prefs = getSharedPreferences("cam", 0)
            if (prefs.getInt("amnesty", 0) < 2) {
                prefs.edit().remove("ceiling").remove("attempting")
                    .putInt("amnesty", 2).apply()
            }
            prefs.getString("crash", null)?.let {
                prefs.edit().remove("crash").commit()
                logLine("last run crashed: " + it.take(200))
            }
        }

        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
            allowFileAccess = false
        }
        web.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String) { booted = true }
            override fun onReceivedError(view: WebView, request: WebResourceRequest,
                                         error: android.webkit.WebResourceError) {
                if (request.isForMainFrame)
                    report("load error ${error.errorCode}: ${error.description} @ ${request.url}")
            }
            override fun onReceivedHttpError(view: WebView, request: WebResourceRequest,
                                             response: WebResourceResponse) {
                if (request.isForMainFrame)
                    report("http ${response.statusCode} @ ${request.url}")
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(m: android.webkit.ConsoleMessage): Boolean {
                // browser interventions (e.g. a pre-gesture vibrate refusal) log
                // at ERROR level but are engine chatter, not app failures - the
                // diag overlay is for problems a tester should actually see
                if (m.messageLevel() == android.webkit.ConsoleMessage.MessageLevel.ERROR
                    && !m.message().contains("Blocked call to navigator.vibrate")
                    && !m.message().contains("chromestatus.com"))
                    report("js: ${m.message()} (${m.sourceId()}:${m.lineNumber()})")
                return true
            }
            override fun onShowFileChooser(view: WebView,
                cb: ValueCallback<Array<Uri>>,
                params: WebChromeClient.FileChooserParams): Boolean {
                fileCb?.onReceiveValue(null)
                fileCb = cb
                return try { pickFile.launch(params.createIntent()); true }
                catch (e: Exception) { fileCb = null; report("file chooser: ${e.message}"); false }
            }
            // the page's own getUserMedia fallback still works inside the app
            override fun onPermissionRequest(request: PermissionRequest) {
                runOnUiThread {
                    if (ContextCompat.checkSelfPermission(this@MainActivity, Manifest.permission.CAMERA)
                        == PackageManager.PERMISSION_GRANTED) request.grant(request.resources)
                    else request.deny()
                }
            }
        }
        // the system back gesture asks the PAGE what to do - guessing from
        // the WebView history stack let a fast double-back drain the page's
        // one spare entry and close the whole app. The page steps up one
        // screen and answers 'ok', or answers 'exit' only when it is already
        // on the project page; a dead page (no answer) also exits so back
        // can never trap the user.
        onBackPressedDispatcher.addCallback(this,
            object : androidx.activity.OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    val cb = this
                    web.evaluateJavascript(
                        "window.__backStep ? __backStep() : 'exit'") { r ->
                        if (r == null || r.contains("exit") || r == "null") {
                            cb.isEnabled = false
                            onBackPressedDispatcher.onBackPressed()
                        }
                    }
                }
            })
        web.addJavascriptInterface(Bridge(), "RealismCam")
        healHome()
        try {
            val inv = shadowRefDirs().mapIndexed { i, d ->
                val fs = d.listFiles() ?: emptyArray()
                (if (i == 0) "int" else "ext") + "=" + fs.size + "/" +
                    (fs.sumOf { it.length() } / 1024) + "KB"
            }.joinToString(" ")
            val st = android.os.StatFs(filesDir.absolutePath)
            logLine("shadow: $inv meta=" + metaRefCount(shadowBestMeta())
                + " free=" + (st.availableBytes / (1024 * 1024)) + "MB")
        } catch (e: Throwable) {}
        val port = LocalServer.start(this)
        logLine("launch port=$port degraded=${LocalServer.degraded}")
        if (port == 0) report("local server failed to bind")
        else {
            if (LocalServer.degraded)
                report("temporary session: your saved work is safe but hidden - " +
                       "close and reopen the app to get it back")
            web.loadUrl("http://127.0.0.1:$port/index.html")
        }
        web.postDelayed({
            if (!booted) report("page did not finish loading in 8s (progress ${web.progress}%)")
        }, 8000)
        startAds()
        // the daily automatic backup: a full export lands in Downloads -
        // the one location no cleaner, quota manager, or wipe reaches
        web.postDelayed({
            val bp = getSharedPreferences("bak", 0)
            if (System.currentTimeMillis() - bp.getLong("at", 0) > 22 * 3600 * 1000L)
                js("window.__autoBak && __autoBak()")
        }, 15000)
    }

    // ---- the ad stack: consent first (Google's UMP form, configured in
    // AdMob's Privacy & messaging), then one native card. The page drives
    // visibility through Bridge.adScreen, so the drawing, format, and
    // compare screens never carry an ad.
    private val NATIVE_UNIT = "ca-app-pub-4573680538268043/6075308934"

    // TEMP DIAGNOSTIC build: the ad stack narrates itself through toasts
    private fun adSay(m: String) { js("toast && toast(" + org.json.JSONObject.quote("ads: " + m) + ")") }

    private fun startAds() {
        val ci = com.google.android.ump.UserMessagingPlatform.getConsentInformation(this)
        val params = com.google.android.ump.ConsentRequestParameters.Builder().build()
        ci.requestConsentInfoUpdate(this, params, {
            com.google.android.ump.UserMessagingPlatform
                .loadAndShowConsentFormIfRequired(this) { fe ->
                    adSay("consent ok" + (if (fe != null) " (form: " + fe.message + ")" else "")
                        + ", canRequest=" + ci.canRequestAds())
                    if (ci.canRequestAds()) initAdBanner()
                }
        }, { err ->
            adSay("consent update failed: " + err.message + ", canRequest=" + ci.canRequestAds())
            // offline or the consent service hiccuped: the SDK still knows
            // whether ads are permitted from the last stored state
            if (ci.canRequestAds()) initAdBanner()
        })
    }

    private fun initAdBanner() {
        if (adsUp) return
        adsUp = true
        Thread {
            com.google.android.gms.ads.MobileAds.initialize(this) { adSay("sdk initialized") }
            runOnUiThread {
                loadNative()
                // gentle cycle: while the project screen is up, refresh a
                // showing card every 75s - and retry an empty slot too
                val tick = object : Runnable {
                    override fun run() {
                        if (adWanted) loadNative()
                        adWrap.postDelayed(this, 75000)
                    }
                }
                adWrap.postDelayed(tick, 75000)
            }
        }.apply { isDaemon = true }.start()
    }

    private fun loadNative() {
        try {
            val loader = com.google.android.gms.ads.AdLoader.Builder(this, NATIVE_UNIT)
                .forNativeAd { ad -> runOnUiThread { adSay("native loaded"); showNative(ad) } }
                .withAdListener(object : com.google.android.gms.ads.AdListener() {
                    override fun onAdFailedToLoad(e: com.google.android.gms.ads.LoadAdError) {
                        adSay("load failed code " + e.code + " (" + e.message + ")")
                    }
                })
                .withNativeAdOptions(com.google.android.gms.ads.nativead.NativeAdOptions.Builder()
                    .setAdChoicesPlacement(
                        com.google.android.gms.ads.nativead.NativeAdOptions.ADCHOICES_TOP_RIGHT)
                    .build())
                .build()
            loader.loadAd(com.google.android.gms.ads.AdRequest.Builder().build())
        } catch (e: Throwable) { logLine("native load: " + e.message) }
    }

    // the native card, drawn in the app's own dark language: media left,
    // headline + body in the middle, accent CTA right, Ad badge as required
    private fun showNative(ad: com.google.android.gms.ads.nativead.NativeAd) {
        try {
            nativeAd?.destroy()
            nativeAd = ad
            val d = resources.displayMetrics.density
            fun dp(v: Int) = (v * d).toInt()
            val ACC = adAccentCol
            val adv = com.google.android.gms.ads.nativead.NativeAdView(this)
            adv.setBackgroundColor(adBgCol)
            val row = android.widget.LinearLayout(this)
            row.orientation = android.widget.LinearLayout.HORIZONTAL
            row.gravity = android.view.Gravity.CENTER_VERTICAL
            row.setPadding(dp(10), dp(8), dp(10), dp(8))
            val media = com.google.android.gms.ads.nativead.MediaView(this)
            row.addView(media, android.widget.LinearLayout.LayoutParams(dp(96), dp(64)))
            val col = android.widget.LinearLayout(this)
            col.orientation = android.widget.LinearLayout.VERTICAL
            col.setPadding(dp(10), 0, dp(10), 0)
            val badge = TextView(this)
            badge.text = "Ad"
            badge.setTextColor(ACC); badge.textSize = 9f
            val bd = android.graphics.drawable.GradientDrawable()
            bd.setStroke(dp(1), ACC); bd.cornerRadius = dp(3).toFloat()
            badge.background = bd
            badge.setPadding(dp(4), 0, dp(4), 0)
            val badgeWrap = android.widget.LinearLayout(this)
            badgeWrap.addView(badge)
            col.addView(badgeWrap)
            val head = TextView(this)
            head.setTextColor(0xFFE8E6E1.toInt()); head.textSize = 13f
            head.maxLines = 1; head.ellipsize = android.text.TextUtils.TruncateAt.END
            head.text = ad.headline ?: ""
            col.addView(head)
            val body = TextView(this)
            body.setTextColor(0xFF9A9A9A.toInt()); body.textSize = 11f
            body.maxLines = 1; body.ellipsize = android.text.TextUtils.TruncateAt.END
            body.text = ad.body ?: ""
            col.addView(body)
            row.addView(col, android.widget.LinearLayout.LayoutParams(
                0, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
            val cta = TextView(this)
            cta.setTextColor(0xFF141414.toInt()); cta.textSize = 12f
            cta.gravity = android.view.Gravity.CENTER
            val cd = android.graphics.drawable.GradientDrawable()
            cd.setColor(ACC); cd.cornerRadius = dp(14).toFloat()
            cta.background = cd
            cta.setPadding(dp(14), dp(7), dp(14), dp(7))
            cta.text = ad.callToAction ?: "Open"
            row.addView(cta)
            adv.addView(row, FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT))
            adv.mediaView = media
            adv.headlineView = head
            adv.bodyView = body
            adv.callToActionView = cta
            adv.setNativeAd(ad)
            adWrap.removeAllViews()
            adWrap.addView(adv, FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT))
            adWrap.setBackgroundColor(adBgCol)
            adCard = adv
            adShownH = dp(80)
            applyAd()
        } catch (e: Throwable) { logLine("native show: " + e.message) }
    }

    // the ad claims a strip below the WebView while visible, so the page's
    // own layout (and the camera ghost geometry) never sits under it
    private fun applyAd() {
        val have = nativeAd != null
        val on = adWanted && have
        adWrap.visibility = if (on) android.view.View.VISIBLE else android.view.View.GONE
        val lp = web.layoutParams as FrameLayout.LayoutParams
        val h = if (on) adShownH else 0
        if (lp.bottomMargin != h) { lp.bottomMargin = h; web.layoutParams = lp }
        // the page lifts its bottom chrome clear of the strip (click safety)
        js("window.__adOn && __adOn(" + on + ")")
    }

    // the browser engine keeps IndexedDB in per-origin folders on disk,
    // named by port. If the biggest trove of user data lives under a
    // different port than the one we are about to serve on, re-home to it -
    // this recovers references orphaned by the pre-0.8.6 port drift no
    // matter which port they actually landed on, and reports what it found
    // so a wiped install is distinguishable from a mis-homed one.
    private fun healHome() {
        try {
            val prefs = getSharedPreferences("srv", 0)
            val rx = Regex("^http_127\\.0\\.0\\.1_(\\d+)\\.indexeddb\\.leveldb$")
            val found = ArrayList<Pair<Int, Long>>()
            for (base in arrayOf("app_webview/Default/IndexedDB", "app_webview/IndexedDB")) {
                val dir = java.io.File(dataDir, base)
                if (!dir.isDirectory) continue
                dir.listFiles()?.forEach { d ->
                    val m = rx.find(d.name) ?: return@forEach
                    var size = 0L
                    d.walkTopDown().forEach { f -> if (f.isFile) size += f.length() }
                    found.add(Pair(m.groupValues[1].toInt(), size))
                }
            }
            if (found.isEmpty()) { logLine("scan: no idb dirs"); return }
            val best = found.maxByOrNull { it.second }!!
            val home = prefs.getInt("home", 8399)
            val list = found.joinToString(" ") { "${it.first}=${it.second / 1024}KB" }
            logLine("scan: $list home=$home")
            if (best.first != home && best.second > 256 * 1024) {
                prefs.edit().putInt("home", best.first).apply()
                logLine("re-homed to ${best.first}")
            }
        } catch (e: Throwable) {}
    }

    // ---- shadow storage plumbing (activity level so the boot line can
    // inventory it): internal + external mirrors, tolerant meta selection
    fun shadowRoots(): List<java.io.File> {
        val roots = ArrayList<java.io.File>()
        roots.add(java.io.File(filesDir, "shadow"))
        try { getExternalFilesDir(null)?.let { roots.add(java.io.File(it, "shadow")) } }
        catch (e: Exception) {}
        return roots
    }
    fun shadowRefDirs(): List<java.io.File> =
        shadowRoots().map { java.io.File(it, "refs").apply { mkdirs() } }
    fun metaRefCount(text: String): Int {
        try {
            val a = org.json.JSONObject(text).optJSONArray("refs") ?: return 0
            var n = 0
            for (i in 0 until a.length())
                if (a.getJSONObject(i).optInt("seed", 0) == 0) n++
            return n
        } catch (e: Exception) { return -1 }
    }
    fun shadowBestMeta(): String {
        var best = ""; var bestN = -1; var bestAt = -1L
        for (root in shadowRoots()) for (name in arrayOf("meta.json", "meta.bak")) {
            val t = try { java.io.File(root, name).readText() } catch (e: Exception) { continue }
            val n = metaRefCount(t)
            if (n < 0) continue
            val at = try { org.json.JSONObject(t).optLong("at", 0) } catch (e: Exception) { 0L }
            if (n > bestN || (n == bestN && at > bestAt)) { best = t; bestN = n; bestAt = at }
        }
        return best
    }

    private fun logLine(s: String) {
        try {
            val p = getSharedPreferences("dlog", 0)
            val ts = java.text.SimpleDateFormat("MMdd HH:mm", java.util.Locale.US)
                .format(java.util.Date())
            val j = ((p.getString("j", "") ?: "") + ts + " " + s + "\n").takeLast(6000)
            p.edit().putString("j", j).apply()
        } catch (e: Exception) {}
    }

    private fun js(code: String) = runOnUiThread { web.evaluateJavascript(code, null) }

    inner class Bridge {
        @JavascriptInterface
        fun start(x: Int, y: Int, w: Int, h: Int) {
            runOnUiThread {
                val go = Runnable { openCamera(x, y, w, h) }
                if (ContextCompat.checkSelfPermission(this@MainActivity, Manifest.permission.CAMERA)
                    == PackageManager.PERMISSION_GRANTED) go.run()
                else { pendingStart = go; askCamera.launch(Manifest.permission.CAMERA) }
            }
        }
        @JavascriptInterface
        fun stop() { runOnUiThread { closeCamera() } }
        @JavascriptInterface
        fun layout(x: Int, y: Int, w: Int, h: Int) {
            runOnUiThread {
                if (previewView.visibility != android.view.View.VISIBLE) return@runOnUiThread
                val lp = FrameLayout.LayoutParams(w, h)
                lp.leftMargin = x; lp.topMargin = y
                previewView.layoutParams = lp
            }
        }
        @JavascriptInterface
        fun capture() { runOnUiThread { takeStill() } }
        // backups land in Downloads where a file manager can find them
        @JavascriptInterface
        fun saveFile(name: String, mime: String, text: String) {
            runOnUiThread {
                try {
                    val bytes = text.toByteArray(Charsets.UTF_8)
                    if (android.os.Build.VERSION.SDK_INT >= 29) {
                        val cv = android.content.ContentValues().apply {
                            put(android.provider.MediaStore.Downloads.DISPLAY_NAME, name)
                            put(android.provider.MediaStore.Downloads.MIME_TYPE, mime)
                        }
                        val uri = contentResolver.insert(
                            android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI, cv)
                            ?: throw Exception("no uri")
                        contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                        js("toast && toast('backup saved to Downloads')")
                    } else {
                        val f = java.io.File(getExternalFilesDir(null), name)
                        f.writeBytes(bytes)
                        js("toast && toast('backup saved: Android/data/app.realism.draw/files')")
                    }
                } catch (e: Exception) {
                    js("toast && toast('backup failed', false)")
                }
            }
        }
        // the automatic daily backup: prune this app's previous auto file
        // from Downloads, write the fresh one, stamp the clock
        @JavascriptInterface
        fun saveFileAuto(name: String, mime: String, text: String) {
            Thread {
                try {
                    val bytes = text.toByteArray(Charsets.UTF_8)
                    if (android.os.Build.VERSION.SDK_INT >= 29) {
                        val col = android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI
                        try {
                            contentResolver.query(col,
                                arrayOf(android.provider.MediaStore.Downloads._ID),
                                "_display_name LIKE ?", arrayOf("photorealism-auto%"), null)?.use { c ->
                                while (c.moveToNext()) {
                                    try { contentResolver.delete(
                                        android.content.ContentUris.withAppendedId(col, c.getLong(0)),
                                        null, null) } catch (e: Exception) {}
                                }
                            }
                        } catch (e: Exception) {}
                        val cv = android.content.ContentValues().apply {
                            put(android.provider.MediaStore.Downloads.DISPLAY_NAME, name)
                            put(android.provider.MediaStore.Downloads.MIME_TYPE, mime)
                        }
                        val uri = contentResolver.insert(col, cv) ?: throw Exception("no uri")
                        contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                    } else {
                        java.io.File(getExternalFilesDir(null), name).writeBytes(bytes)
                    }
                    getSharedPreferences("bak", 0).edit()
                        .putLong("at", System.currentTimeMillis()).apply()
                    logLine("auto-backup saved ${bytes.size / 1024}KB")
                    js("toast && toast('auto-backup saved to Downloads')")
                } catch (e: Exception) { logLine("auto-backup failed: ${e.message}") }
            }.apply { isDaemon = true }.start()
        }
        // ---- the shadow: a native mirror of every user reference ----
        // WebView storage has been wiped in the field more than once. After
        // the 2026-08-29 incident took app_webview AND the internal shadow
        // in one stroke (shared_prefs survived), the mirror now writes to
        // TWO filesystems - the internal files dir and the external app
        // files dir - the index is written atomically with a .bak
        // generation, and an empty index may never clobber a good one.
        private fun safeName(id: String) = id.filter { it.isLetterOrDigit() } + ".bin"
        @JavascriptInterface
        fun shadowSaveRef(id: String, b64: String) {
            Thread {
                try {
                    val bytes = Base64.decode(b64, Base64.DEFAULT)
                    for (d in shadowRefDirs())
                        try { java.io.File(d, safeName(id)).writeBytes(bytes) }
                        catch (e: Exception) {}
                } catch (e: Exception) {}
            }.apply { isDaemon = true }.start()
        }
        @JavascriptInterface
        fun shadowDeleteRef(id: String) {
            for (d in shadowRefDirs())
                try { java.io.File(d, safeName(id)).delete() } catch (e: Exception) {}
        }
        @JavascriptInterface
        fun shadowList(): String =
            try {
                val names = LinkedHashSet<String>()
                for (d in shadowRefDirs())
                    d.listFiles()?.forEach { names.add(it.name.removeSuffix(".bin")) }
                names.joinToString(",")
            } catch (e: Exception) { "" }
        @JavascriptInterface
        fun shadowReadRef(id: String): String {
            for (d in shadowRefDirs())
                try {
                    val b = java.io.File(d, safeName(id)).readBytes()
                    if (b.isNotEmpty()) return Base64.encodeToString(b, Base64.NO_WRAP)
                } catch (e: Exception) {}
            return ""
        }
        @JavascriptInterface
        fun shadowSaveMeta(text: String) {
            Thread {
                try {
                    // never-shrink: a boot that sees a wiped gallery must
                    // not clobber a good index while mirrored files exist
                    if (metaRefCount(text) == 0
                        && metaRefCount(shadowBestMeta()) > 0
                        && shadowRefDirs().any { !(it.listFiles().isNullOrEmpty()) }) {
                        logLine("shadow: refused meta shrink to 0")
                        return@Thread
                    }
                    for (root in shadowRoots()) {
                        try {
                            root.mkdirs()
                            val meta = java.io.File(root, "meta.json")
                            if (meta.exists())
                                try { meta.copyTo(java.io.File(root, "meta.bak"), overwrite = true) }
                                catch (e: Exception) {}
                            val tmp = java.io.File(root, "meta.tmp")
                            tmp.writeText(text)
                            if (!tmp.renameTo(meta)) { meta.writeText(text); tmp.delete() }
                        } catch (e: Exception) {}
                    }
                } catch (e: Exception) {}
            }.apply { isDaemon = true }.start()
        }
        @JavascriptInterface
        fun shadowLoadMeta(): String = shadowBestMeta()
        // rolling diagnostics journal: every launch and storage event lands
        // here so the NEXT incident carries evidence instead of anecdote
        @JavascriptInterface
        fun adScreen(onProject: Boolean) {
            runOnUiThread { adWanted = onProject; applyAd() }
        }
        @JavascriptInterface
        fun adAccent(hex: String) {
            try { adAccentCol = android.graphics.Color.parseColor(hex) } catch (e: Exception) {}
        }
        // every screen carries the strip; the page names the backdrop it
        // should melt into (and clears it while the native camera is up)
        @JavascriptInterface
        fun adPlace(on: Boolean, bg: String) {
            val c = try { android.graphics.Color.parseColor(bg) }
                    catch (e: Exception) { 0xFF141414.toInt() }
            runOnUiThread {
                adBgCol = c
                adWanted = on
                adWrap.setBackgroundColor(c)
                adCard?.setBackgroundColor(c)
                applyAd()
            }
        }
        @JavascriptInterface
        fun dlog(line: String) = logLine("page: " + line.take(300))
        @JavascriptInterface
        fun dlogs(): String =
            try { getSharedPreferences("dlog", 0).getString("j", "") ?: "" } catch (e: Exception) { "" }
        // the page's share button routes here so the system share sheet
        // carries the Play listing instead of the loopback URL
        @JavascriptInterface
        fun share(text: String) {
            runOnUiThread {
                try {
                    val i = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                        type = "text/plain"
                        putExtra(android.content.Intent.EXTRA_TEXT, text)
                    }
                    startActivity(android.content.Intent.createChooser(i, "Share Photorealism"))
                } catch (e: Exception) {}
            }
        }
        @JavascriptInterface
        fun saveImageAsk(name: String, mime: String, b64: String) {
            runOnUiThread {
                try {
                    pendingSave = Base64.decode(b64, Base64.DEFAULT)
                    createDoc.launch(name)
                } catch (e: Exception) {
                    pendingSave = null
                    js("toast && toast('save failed', false)")
                }
            }
        }
        // comparison/photo downloads land in Pictures where the gallery sees them
        @JavascriptInterface
        fun saveImage(name: String, mime: String, b64: String) {
            runOnUiThread {
                try {
                    val bytes = Base64.decode(b64, Base64.DEFAULT)
                    if (android.os.Build.VERSION.SDK_INT >= 29) {
                        val cv = android.content.ContentValues().apply {
                            put(android.provider.MediaStore.Images.Media.DISPLAY_NAME, name)
                            put(android.provider.MediaStore.Images.Media.MIME_TYPE, mime)
                            put(android.provider.MediaStore.Images.Media.RELATIVE_PATH,
                                "Pictures/Realism")
                        }
                        val uri = contentResolver.insert(
                            android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv)
                            ?: throw Exception("no uri")
                        contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                        js("toast && toast('saved to Pictures')")
                    } else {
                        val f = java.io.File(getExternalFilesDir(null), name)
                        f.writeBytes(bytes)
                        js("toast && toast('saved: Android/data/app.realism.draw/files')")
                    }
                } catch (e: Exception) {
                    js("toast && toast('save failed', false)")
                }
            }
        }
        @JavascriptInterface
        fun focus(nx: Float, ny: Float) {
            runOnUiThread {
                val cam = camera ?: return@runOnUiThread
                val pt = previewView.meteringPointFactory.createPoint(
                    nx * previewView.width, ny * previewView.height)
                cam.cameraControl.startFocusAndMetering(FocusMeteringAction.Builder(pt).build())
            }
        }
    }

    // capture-quality ladder, per device, self-healing: a rung is marked
    // 'attempting' in prefs before it binds and cleared once the preview
    // reports ready - if the process died mid-attempt (vendor HAL crash),
    // the next launch demotes past that rung instead of crashing forever.
    private val RUNG_RAW = 2; private val RUNG_EXT = 1; private val RUNG_PLAIN = 0

    private fun openCamera(x: Int, y: Int, w: Int, h: Int) {
        web.setBackgroundColor(Color.TRANSPARENT)
        val lp = FrameLayout.LayoutParams(w, h)
        lp.leftMargin = x; lp.topMargin = y
        previewView.layoutParams = lp
        previewView.visibility = android.view.View.VISIBLE
        val fut = ProcessCameraProvider.getInstance(this)
        fut.addListener({
            val prov = try { fut.get() } catch (e: Exception) {
                report("camera provider: ${e.message}")
                js("window.__natFail && __natFail('open')"); return@addListener
            }
            provider = prov
            // decide the rung OFF the main thread: extensions init blocks,
            // and blocking main here was an ANR-crash at camera open
            Thread {
                val prefs = getSharedPreferences("cam", 0)
                val crashed = prefs.getInt("attempting", -1)
                if (crashed >= 0) {
                    prefs.edit().putInt("ceiling", crashed - 1).remove("attempting").apply()
                    report("previous ${'"'}${rungName(crashed)}${'"'} attempt died - demoting")
                }
                val ceiling = prefs.getInt("ceiling", RUNG_RAW)
                var rung = RUNG_PLAIN
                var selector = CameraSelector.DEFAULT_BACK_CAMERA
                if (ceiling >= RUNG_RAW) try {
                    val caps = ImageCapture.getImageCaptureCapabilities(
                        prov.getCameraInfo(CameraSelector.DEFAULT_BACK_CAMERA))
                    if (caps.supportedOutputFormats.contains(ImageCapture.OUTPUT_FORMAT_RAW))
                        rung = RUNG_RAW
                } catch (e: Throwable) {}
                if (rung == RUNG_PLAIN && ceiling >= RUNG_EXT) try {
                    val em = ExtensionsManager.getInstanceAsync(this, prov).get()
                    for (mode in intArrayOf(ExtensionMode.AUTO, ExtensionMode.HDR)) {
                        if (em.isExtensionAvailable(CameraSelector.DEFAULT_BACK_CAMERA, mode)) {
                            selector = em.getExtensionEnabledCameraSelector(
                                CameraSelector.DEFAULT_BACK_CAMERA, mode)
                            rung = RUNG_EXT
                            break
                        }
                    }
                } catch (e: Throwable) {}
                runOnUiThread { bindRung(rung, selector, prefs) }
            }.apply { isDaemon = true }.start()
        }, ContextCompat.getMainExecutor(this))
    }

    private fun rungName(r: Int) = when (r) { 2 -> "raw"; 1 -> "hdr"; else -> "" }

    @androidx.annotation.OptIn(androidx.camera.camera2.interop.ExperimentalCamera2Interop::class)
    private fun bindRung(rung: Int, selector: CameraSelector,
                         prefs: android.content.SharedPreferences) {
        val prov = provider ?: return
        prefs.edit().putInt("attempting", rung).apply()
        rawMode = rung == RUNG_RAW
        capLabel = rungName(rung)
        try {
            val stillB = ImageCapture.Builder()
                .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                .setResolutionSelector(ResolutionSelector.Builder()
                    .setAspectRatioStrategy(AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY)
                    .setResolutionStrategy(ResolutionStrategy.HIGHEST_AVAILABLE_STRATEGY)
                    .build())
                .setTargetRotation(Surface.ROTATION_0)
            // RAW alone is legal on the in-memory path; the display JPEG is
            // rendered from the RAW plane itself - one capture, aligned planes
            if (rawMode) stillB.setOutputFormat(ImageCapture.OUTPUT_FORMAT_RAW)
            val previewB = Preview.Builder()
                .setResolutionSelector(ResolutionSelector.Builder()
                    .setAspectRatioStrategy(AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY)
                    .build())
                .setTargetRotation(Surface.ROTATION_0)
            if (rawMode) {
                // RAW skips the ISP's lens-shading correction, so ask the HAL
                // to report the gain map it WOULD have applied; the preview's
                // repeating request keeps a fresh map warm for every still
                shadeMap = null
                val ext = androidx.camera.camera2.interop.Camera2Interop.Extender(previewB)
                ext.setCaptureRequestOption(
                    android.hardware.camera2.CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE,
                    android.hardware.camera2.CameraMetadata.STATISTICS_LENS_SHADING_MAP_MODE_ON)
                ext.setSessionCaptureCallback(object :
                        android.hardware.camera2.CameraCaptureSession.CaptureCallback() {
                    override fun onCaptureCompleted(
                        s: android.hardware.camera2.CameraCaptureSession,
                        rq: android.hardware.camera2.CaptureRequest,
                        res: android.hardware.camera2.TotalCaptureResult) {
                        res.get(android.hardware.camera2.CaptureResult
                            .STATISTICS_LENS_SHADING_CORRECTION_MAP)?.let { shadeMap = it }
                    }
                })
            }
            val preview = previewB.build()
            val still = stillB.build()
            imageCapture = still
            prov.unbindAll()
            camera = prov.bindToLifecycle(this,
                if (rung == RUNG_EXT) selector else CameraSelector.DEFAULT_BACK_CAMERA,
                preview, still)
            preview.setSurfaceProvider(previewView.surfaceProvider)
            var tries = 0
            fun reportSize() {
                val ri = preview.resolutionInfo
                if (ri != null) {
                    // the app is portrait-locked: the display-oriented frame is
                    // ALWAYS taller than wide, whatever the rotation metadata
                    // claims - this is what kept the ghost inside the viewfinder
                    val fw = minOf(ri.resolution.width, ri.resolution.height)
                    val fh = maxOf(ri.resolution.width, ri.resolution.height)
                    prefs.edit().remove("attempting").apply()
                    if (!modeAnnounced) {
                        modeAnnounced = true
                        logLine("capture mode: " + (if (capLabel == "") "standard" else capLabel))
                    }
                    js("window.__natReady && __natReady($fw,$fh)")
                } else if (tries++ < 40) previewView.postDelayed({ reportSize() }, 50)
                else {
                    prefs.edit().remove("attempting").apply()
                    js("window.__natFail && __natFail('nores')")
                }
            }
            reportSize()
        } catch (e: Throwable) {
            prefs.edit().remove("attempting").apply()
            if (rung > RUNG_PLAIN) {
                // the extension selector only exists on the decision thread,
                // so any in-process failure demotes straight to plain
                report("${rungName(rung)} bind failed (${e.message}) - plain capture")
                bindRung(RUNG_PLAIN, CameraSelector.DEFAULT_BACK_CAMERA, prefs)
            } else {
                report("camera open failed: ${e.message}")
                js("window.__natFail && __natFail('open')")
            }
        }
    }

    private fun takeStill() {
        val still = imageCapture ?: run { js("window.__natFail && __natFail('nocap')"); return }
        // a crash between here and delivery demotes the rung on next launch
        val prefs = getSharedPreferences("cam", 0)
        prefs.edit().putInt("attempting",
            if (rawMode) RUNG_RAW else if (capLabel != "") RUNG_EXT else RUNG_PLAIN).apply()
        val expectRaw = rawMode
        val got = java.util.concurrent.ConcurrentHashMap<String, String>()
        var timer: Runnable? = null
        fun deliver() {
            val j = got["jpeg"] ?: return
            prefs.edit().remove("attempting").apply()
            val r = got["raw"]
            val rArg = if (r != null) "'" + r + "'" else "null"
            js("window.__natShot && __natShot('" + j + "', " + rArg + ", '" + capLabel + "')")
        }
        fun armTimeout() {
            // RAW and JPEG arrive as separate callbacks; if one never comes,
            // ship what we have rather than hanging the shutter
            val t = Runnable { if (got.containsKey("jpeg")) deliver()
                               else js("window.__natFail && __natFail('shot')") }
            timer = t
            web.postDelayed(t, 4000)
        }
        armTimeout()
        val cb = object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: ImageProxy) {
                try {
                    if (image.format == android.graphics.ImageFormat.RAW_SENSOR) {
                        val t = rawLuma(image)
                        if (t != null) {
                            got["raw"] = LocalServer.park("application/octet-stream",
                                packLuma(t.first, t.second, t.third))
                            got["jpeg"] = LocalServer.park("image/jpeg",
                                lumaJpeg(t.first, t.second, t.third))
                        }
                    } else {
                        val buf = image.planes[0].buffer
                        val bytes = ByteArray(buf.remaining()); buf.get(bytes)
                        got["jpeg"] = LocalServer.park("image/jpeg", bytes)
                    }
                } catch (e: Throwable) {
                    report("capture decode: ${e.message}")
                } finally { image.close() }
                if (got.containsKey("jpeg")) {
                    timer?.let { web.removeCallbacks(it) }
                    deliver()
                }
            }
            override fun onError(e: ImageCaptureException) {
                timer?.let { web.removeCallbacks(it) }
                prefs.edit().remove("attempting").apply()
                report("capture: ${e.message}")
                js("window.__natFail && __natFail('shot')")
            }
        }
        try {
            still.takePicture(captureExec, cb)
        } catch (e: Throwable) {
            // a synchronous reject (the RAW+JPEG crash, once) demotes instead
            timer?.let { web.removeCallbacks(it) }
            val r0 = if (rawMode) RUNG_RAW else if (capLabel != "") RUNG_EXT else RUNG_PLAIN
            prefs.edit().remove("attempting").putInt("ceiling", r0 - 1).apply()
            report("capture rejected (${e.message}) - demoted for next open")
            js("window.__natFail && __natFail('shot')")
        }
    }

    // RAW -> full-resolution 16-bit LUMA, no CFA-pattern logic needed: every
    // 2x2 Bayer window holds {R, G, G, B}, and a charcoal drawing is neutral,
    // so the flat window mean IS its luminance. Black/white levels from the
    // camera characteristics, gamma 1/2.2 into a 0..255*256 fixed-point plane
    // the page divides back into floats - the real 'shoot raw' the sliders
    // have been waiting for.
    private fun packLuma(l: ShortArray, w: Int, h: Int): ByteArray {
        val bb = java.nio.ByteBuffer.allocate(8 + l.size * 2)
            .order(java.nio.ByteOrder.LITTLE_ENDIAN)
        bb.putInt(w); bb.putInt(h)
        bb.asShortBuffer().put(l)
        return bb.array()
    }

    private fun lumaJpeg(l: ShortArray, w: Int, h: Int): ByteArray {
        val px = IntArray(w * h)
        for (i in px.indices) {
            val v = (l[i].toInt() and 0xFFFF) ushr 8
            px[i] = -0x1000000 or (v shl 16) or (v shl 8) or v
        }
        val bm = android.graphics.Bitmap.createBitmap(px, w, h,
            android.graphics.Bitmap.Config.ARGB_8888)
        val bos = java.io.ByteArrayOutputStream()
        bm.compress(android.graphics.Bitmap.CompressFormat.JPEG, 95, bos)
        bm.recycle()
        return bos.toByteArray()
    }

    @androidx.annotation.OptIn(androidx.camera.camera2.interop.ExperimentalCamera2Interop::class)
    private fun rawLuma(image: ImageProxy): Triple<ShortArray, Int, Int>? {
        val w = image.width; val h = image.height
        if (w < 4 || h < 4) return null
        val plane = image.planes[0]
        val rowShorts = plane.rowStride / 2
        val sb = plane.buffer.order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
        var black = 64; var white = 1023
        try {
            val ch = androidx.camera.camera2.interop.Camera2CameraInfo.from(camera!!.cameraInfo)
            ch.getCameraCharacteristic(android.hardware.camera2.CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN)
                ?.let { black = (it.getOffsetForIndex(0,0) + it.getOffsetForIndex(1,0)
                                + it.getOffsetForIndex(0,1) + it.getOffsetForIndex(1,1)) / 4 }
            ch.getCameraCharacteristic(android.hardware.camera2.CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL)
                ?.let { white = it }
        } catch (e: Throwable) {}
        if (white <= black) { black = 0; white = 1023 }
        // gamma LUT over the sensor's code range: 4*value sums index the table
        val span = (white - black).toFloat()
        val lutMax = 4 * white
        val lut = ShortArray(lutMax + 1)
        for (i in 0..lutMax) {
            var v = (i / 4f - black) / span
            if (v < 0f) v = 0f; if (v > 1f) v = 1f
            lut[i] = (Math.pow(v.toDouble(), 1.0 / 2.2) * 255.0 * 256.0)
                .toInt().coerceAtMost(65535).toShort()
        }
        // lens-shading correction: raw sensor data is pre-correction by
        // definition, so it carries the lens's real corner falloff that the
        // ISP removes from every JPEG. Collapse the HAL's per-channel gain
        // map to the window mean's flat R+G+G+B weighting and scale each
        // window's signal-above-black by the bilinearly interpolated gain.
        // No map reported (older HALs) = no correction, same as before.
        val map = shadeMap
        var grid: FloatArray? = null; var gRows = 0; var gCols = 0
        if (map != null && map.rowCount >= 2 && map.columnCount >= 2) {
            gRows = map.rowCount; gCols = map.columnCount
            val g = FloatArray(gRows * gCols)
            for (r in 0 until gRows) for (c in 0 until gCols)
                g[r * gCols + c] = (map.getGainFactor(0, c, r) +
                    map.getGainFactor(1, c, r) + map.getGainFactor(2, c, r) +
                    map.getGainFactor(3, c, r)) / 4f
            grid = g
        }
        val xC = IntArray(w); val xT = FloatArray(w)
        if (grid != null) for (x in 0 until w) {
            val fx = x.toFloat() / (w - 1) * (gCols - 1)
            val c = fx.toInt().coerceIn(0, gCols - 2)
            xC[x] = c; xT[x] = (fx - c).coerceIn(0f, 1f)
        }
        val rowG = FloatArray(if (gCols > 0) gCols else 1)
        val black4 = 4f * black
        val rot = image.imageInfo.rotationDegrees
        val ow = if (rot % 180 == 0) w else h
        val oh = if (rot % 180 == 0) h else w
        val out = ShortArray(ow * oh)
        val row = ShortArray(rowShorts)
        val row2 = ShortArray(rowShorts)
        for (y in 0 until h) {
            val yn = if (y + 1 < h) y + 1 else y
            if (grid != null) {
                val fy = y.toFloat() / (h - 1) * (gRows - 1)
                val r0 = fy.toInt().coerceIn(0, gRows - 2)
                val t = (fy - r0).coerceIn(0f, 1f)
                for (c in 0 until gCols)
                    rowG[c] = grid[r0 * gCols + c] * (1f - t) +
                              grid[(r0 + 1) * gCols + c] * t
            }
            sb.position(y * rowShorts); sb.get(row, 0, minOf(rowShorts, sb.remaining()))
            sb.position(yn * rowShorts); sb.get(row2, 0, minOf(rowShorts, sb.remaining()))
            for (x in 0 until w) {
                val xn = if (x + 1 < w) x + 1 else x
                var sum = (row[x].toInt() and 0xFFFF) + (row[xn].toInt() and 0xFFFF) +
                          (row2[x].toInt() and 0xFFFF) + (row2[xn].toInt() and 0xFFFF)
                if (grid != null) {
                    val c = xC[x]
                    val gn = rowG[c] * (1f - xT[x]) + rowG[c + 1] * xT[x]
                    sum = (black4 + (sum - black4) * gn).toInt()
                    if (sum < 0) sum = 0
                }
                if (sum > lutMax) sum = lutMax
                val v = lut[sum]
                val oi = when (rot) {
                    90 -> x * ow + (ow - 1 - y).coerceAtLeast(0)
                    180 -> (oh - 1 - y) * ow + (ow - 1 - x)
                    270 -> (oh - 1 - x) * ow + y
                    else -> y * ow + x
                }
                out[oi] = v
            }
        }
        return Triple(out, ow, oh)
    }

    private fun closeCamera() {
        web.setBackgroundColor(Color.BLACK)
        try { provider?.unbindAll() } catch (e: Exception) {}
        camera = null; imageCapture = null
        previewView.visibility = android.view.View.GONE
    }

    override fun onDestroy() { captureExec.shutdown(); super.onDestroy() }
}
