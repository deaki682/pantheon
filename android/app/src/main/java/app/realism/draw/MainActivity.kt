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
    private var adBadgeV: TextView? = null
    private var adCtaV: TextView? = null
    // corner mode (drawing screen only): the download button's corner
    // becomes the 120x120-media card for a bounded window, then returns
    private lateinit var adCornerWrap: FrameLayout
    private var adOnProj = false          // page reports the drawing screen
    private var adViewMode = ""           // which container holds the card
    private var adNextShowAt = 0L         // cadence: earliest next window
    private var lastTouchMs = 0L          // never appear under a finger
    private var billing: com.android.billingclient.api.BillingClient? = null

    override fun dispatchTouchEvent(ev: android.view.MotionEvent): Boolean {
        lastTouchMs = android.os.SystemClock.uptimeMillis()
        return super.dispatchTouchEvent(ev)
    }

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

    // migration for installs that swapped their icon before the feature
    // was retired: put every launcher component back to its manifest
    // default (MainActivity enabled, every alias disabled). The aliases
    // themselves must STAY in the manifest so those installs keep a valid
    // launcher entry until this runs.
    private fun restoreLauncherIcon() {
        try {
            val prefs = getSharedPreferences("ui", 0)
            if (prefs.getInt("icon", -1) == -1) return
            val pm = packageManager
            val def = android.content.pm.PackageManager.COMPONENT_ENABLED_STATE_DEFAULT
            val flags = android.content.pm.PackageManager.DONT_KILL_APP
            pm.setComponentEnabledSetting(
                android.content.ComponentName(this, "app.realism.draw.MainActivity"),
                def, flags)
            for (i in 0..9) pm.setComponentEnabledSetting(
                android.content.ComponentName(this, "app.realism.draw.IconA$i"),
                def, flags)
            prefs.edit().putInt("icon", -1).apply()
        } catch (e: Exception) {}
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        restoreLauncherIcon()
        if (android.os.Build.VERSION.SDK_INT >= 31) {
            // the system splash CROSSFADES into the app instead of vanishing
            // in one frame - the launcher icon swells and dissolves as the
            // wordmark splash appears beneath it
            splashScreen.setOnExitAnimationListener { sv ->
                try {
                    // a plain fade: the per-frame RenderEffect blur cost a
                    // stutter right as the page painted its first frames
                    sv.iconView?.animate()?.alpha(0f)?.setDuration(180)?.start()
                    sv.animate().alpha(0f).setDuration(260)
                        .withEndAction { sv.remove() }.start()
                } catch (e: Throwable) { sv.remove() }
            }
        }
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
            // the keyboard too: without the ime inset the soft keyboard
            // OVERLAYS the page and focused inputs vanish beneath it -
            // padding by it shrinks the WebView so the engine scrolls the
            // field into view like any browser
            val ime = insets.getInsets(androidx.core.view.WindowInsetsCompat.Type.ime())
            v.setPadding(b.left, b.top, b.right, maxOf(b.bottom, ime.bottom))
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
        adCornerWrap = FrameLayout(this)
        adCornerWrap.visibility = android.view.View.GONE
        run {
            root.addView(adCornerWrap, adCornerParams())
        }
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
            // anything off the loopback origin leaves for the system: web
            // links open the real browser, market:// the Play Store,
            // discord:// the Discord app. Without this the WebView swallows
            // them and dead-ends on ERR_UNKNOWN_URL_SCHEME.
            override fun shouldOverrideUrlLoading(view: WebView,
                                                  request: WebResourceRequest): Boolean {
                val url = request.url ?: return false
                val scheme = url.scheme ?: ""
                if (url.host == "127.0.0.1" || scheme == "blob" || scheme == "data"
                    || scheme == "about") return false
                return try {
                    val i = if (scheme == "intent")
                        android.content.Intent.parseUri(url.toString(),
                            android.content.Intent.URI_INTENT_SCHEME)
                    else android.content.Intent(android.content.Intent.ACTION_VIEW, url)
                    startActivity(i)
                    true
                } catch (e: Exception) { true }   // no handler: drop it, never error-page
            }
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
                // budget OEM ROMs can lack a handler for any given picker
                // intent - walk a fallback chain instead of dying silently:
                // the page's own intent, the Android 13+ photo picker, the
                // classic gallery ACTION_PICK, then a bare GET_CONTENT
                val tries = mutableListOf<android.content.Intent>()
                try { tries.add(params.createIntent()) } catch (e: Exception) {}
                if (android.os.Build.VERSION.SDK_INT >= 33)
                    tries.add(android.content.Intent(android.provider.MediaStore.ACTION_PICK_IMAGES))
                tries.add(android.content.Intent(android.content.Intent.ACTION_PICK,
                    android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI))
                tries.add(android.content.Intent(android.content.Intent.ACTION_GET_CONTENT)
                    .setType("image/*").addCategory(android.content.Intent.CATEGORY_OPENABLE))
                for (i in tries) {
                    try { pickFile.launch(i); return true }
                    catch (e: Exception) { logLine("file chooser: " + e.message) }
                }
                fileCb = null
                js("toast && toast('no photo picker app found on this device', false, 5000)")
                return false
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
        initBilling()
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

    // the ad stack narrates itself into the version-tap log only
    private fun adSay(m: String) { js("window.plog && plog(" + org.json.JSONObject.quote("ads: " + m) + ")") }

    private fun startAds() {
        if (adsRemovedFlag()) return
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
                adShownH = (80 * resources.displayMetrics.density).toInt()
                applyAd()
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
                    // video creatives may fill the 120x120 corner card:
                    // always muted unless the viewer taps the ad's own control
                    .setVideoOptions(com.google.android.gms.ads.VideoOptions.Builder()
                        .setStartMuted(true).build())
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
            adViewMode = ""                  // rebuilt into whichever mode shows
            applyAd()
        } catch (e: Throwable) { logLine("native show: " + e.message) }
    }

    private fun adBadge(dp: (Int) -> Int): TextView {
        val badge = TextView(this)
        badge.text = "Ad"
        badge.setTextColor(adAccentCol); badge.textSize = 9f
        val bd = android.graphics.drawable.GradientDrawable()
        bd.setStroke(dp(1), adAccentCol); bd.cornerRadius = dp(3).toFloat()
        badge.background = bd
        badge.setPadding(dp(4), 0, dp(4), 0)
        return badge
    }
    private fun adCta(ad: com.google.android.gms.ads.nativead.NativeAd,
                      dp: (Int) -> Int, radius: Int): TextView {
        val cta = TextView(this)
        cta.setTextColor(0xFF141414.toInt()); cta.textSize = 12f
        cta.gravity = android.view.Gravity.CENTER
        val cd = android.graphics.drawable.GradientDrawable()
        cd.setColor(adAccentCol); cd.cornerRadius = dp(radius).toFloat()
        cta.background = cd
        cta.setPadding(dp(12), dp(6), dp(12), dp(6))
        cta.text = ad.callToAction ?: "Open"
        return cta
    }

    // the bottom strip: every screen except the drawing screen
    private fun buildStrip() {
        val ad = nativeAd ?: return
        val d = resources.displayMetrics.density
        fun dp(v: Int) = (v * d).toInt()
        val adv = com.google.android.gms.ads.nativead.NativeAdView(this)
        adv.setBackgroundColor(adBgCol)
        val row = android.widget.LinearLayout(this)
        row.orientation = android.widget.LinearLayout.HORIZONTAL
        row.gravity = android.view.Gravity.CENTER_VERTICAL
        row.setPadding(dp(10), dp(8), dp(10), dp(8))
        val media = com.google.android.gms.ads.nativead.MediaView(this)
        row.addView(media, android.widget.LinearLayout.LayoutParams(dp(40), dp(40)))
        val col = android.widget.LinearLayout(this)
        col.orientation = android.widget.LinearLayout.VERTICAL
        col.setPadding(dp(10), 0, dp(10), 0)
        val badge = adBadge(::dp)
        val badgeWrap = android.widget.LinearLayout(this)
        badgeWrap.addView(badge)
        col.addView(badgeWrap)
        val head = TextView(this)
        head.setTextColor(0xFFE8E6E1.toInt()); head.textSize = 13f
        head.maxLines = 1; head.ellipsize = android.text.TextUtils.TruncateAt.END
        head.text = ad.headline ?: ""
        col.addView(head)
        row.addView(col, android.widget.LinearLayout.LayoutParams(
            0, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
        val cta = adCta(ad, ::dp, 14)
        row.addView(cta)
        adv.addView(row, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT))
        adv.mediaView = media
        adv.headlineView = head
        adv.callToActionView = cta
        adv.setNativeAd(ad)
        adWrap.removeAllViews()
        // landscape: a full-width strip eats a fifth of the short screen -
        // float a compact centered card instead and let the page show
        // through beside it; portrait keeps the edge-to-edge strip
        val land = resources.configuration.orientation ==
            android.content.res.Configuration.ORIENTATION_LANDSCAPE
        val alp = FrameLayout.LayoutParams(
            if (land) minOf(dp(460), resources.displayMetrics.widthPixels - dp(140))
            else FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.WRAP_CONTENT)
        if (land) {
            alp.gravity = android.view.Gravity.CENTER_HORIZONTAL
            alp.bottomMargin = dp(6)
            adv.background = android.graphics.drawable.GradientDrawable().apply {
                setColor(adBgCol); cornerRadius = dp(14).toFloat()
            }
            adv.clipToOutline = true
            adWrap.setBackgroundColor(0)
        } else adWrap.setBackgroundColor(adBgCol)
        adWrap.addView(adv, alp)
        adCard = adv
        adBadgeV = badge
        adCtaV = cta
        adShownH = dp(56)
        adViewMode = "strip"
    }

    // the corner card: 120x120 media (video-eligible), badge over the
    // media, two-line headline, full-width CTA, collapse pill below -
    // the pill is OUTSIDE the ad view so its tap never counts as a click
    private fun buildCorner() {
        val ad = nativeAd ?: return
        val d = resources.displayMetrics.density
        fun dp(v: Int) = (v * d).toInt()
        val adv = com.google.android.gms.ads.nativead.NativeAdView(this)
        val bg = android.graphics.drawable.GradientDrawable()
        bg.setColor(adBgCol); bg.cornerRadius = dp(14).toFloat()
        bg.setStroke(Math.max(1, dp(1)), 0x1FFFFFFF)
        adv.background = bg
        adv.clipToOutline = true
        adv.elevation = dp(10).toFloat()   // the card floats above the page
        val card = android.widget.LinearLayout(this)
        card.orientation = android.widget.LinearLayout.HORIZONTAL
        card.setPadding(dp(6), dp(6), dp(6), dp(6))
        val mediaWrap = FrameLayout(this)
        val media = com.google.android.gms.ads.nativead.MediaView(this)
        mediaWrap.addView(media, FrameLayout.LayoutParams(dp(120), dp(120)))
        val badge = adBadge(::dp)
        val blp = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT,
            android.view.Gravity.BOTTOM or android.view.Gravity.START)
        blp.leftMargin = dp(4); blp.bottomMargin = dp(4)
        mediaWrap.addView(badge, blp)
        card.addView(mediaWrap, android.widget.LinearLayout.LayoutParams(dp(120), dp(120)))
        // text column beside the media: headline up top, CTA pinned at the foot
        val col = android.widget.LinearLayout(this)
        col.orientation = android.widget.LinearLayout.VERTICAL
        col.setPadding(dp(8), 0, 0, 0)
        val head = TextView(this)
        head.setTextColor(0xFFE8E6E1.toInt()); head.textSize = 11.5f
        head.maxLines = 3; head.ellipsize = android.text.TextUtils.TruncateAt.END
        head.text = ad.headline ?: ""
        head.setPadding(dp(2), dp(2), dp(2), dp(4))
        col.addView(head, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f))
        val cta = adCta(ad, ::dp, 10)
        col.addView(cta, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
            android.widget.LinearLayout.LayoutParams.WRAP_CONTENT))
        card.addView(col, android.widget.LinearLayout.LayoutParams(dp(112), dp(120)))
        adv.addView(card, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT))
        adv.mediaView = media
        adv.headlineView = head
        adv.callToActionView = cta
        adv.setNativeAd(ad)
        // the collapse pill sits LEFT of the card, tucked beneath the spot
        // the gear glides to - still outside the ad view, never an ad click
        val rowWrap = android.widget.LinearLayout(this)
        // portrait (top-right anchor): the X sits LEFT of the card, under
        // the gear's glide spot. Landscape (bottom-left anchor): the X
        // floats NEXT to the gear on the left edge - beside the column,
        // vertically centered, clear of both the gear and the card
        val land = adLand()
        rowWrap.orientation = android.widget.LinearLayout.HORIZONTAL
        // let the card's elevation shadow paint past the wrapper bounds
        rowWrap.clipChildren = false; rowWrap.clipToPadding = false
        adCornerWrap.clipChildren = false; adCornerWrap.clipToPadding = false
        val close = TextView(this)
        close.text = "✕"
        close.setTextColor(0xFFB9B5AE.toInt()); close.textSize = 12f
        close.gravity = android.view.Gravity.CENTER
        val cbg = android.graphics.drawable.GradientDrawable()
        cbg.setColor(0xE6191919.toInt()); cbg.cornerRadius = dp(13).toFloat()
        close.background = cbg
        close.setOnClickListener { adCollapse() }
        (adCloseFloat?.parent as? android.view.ViewGroup)?.removeView(adCloseFloat)
        adCloseFloat = null
        if (land) {
            // beside the gear: past the edge column's button width, centered
            val gearW = if (resources.configuration.smallestScreenWidthDp >= 600) 76 else 44
            val flp = FrameLayout.LayoutParams(dp(26), dp(26),
                android.view.Gravity.START or android.view.Gravity.CENTER_VERTICAL)
            flp.leftMargin = dp(8 + gearW + 12)
            close.visibility = android.view.View.GONE
            (adCornerWrap.parent as? FrameLayout)?.addView(close, flp)
            adCloseFloat = close
        } else {
            val clp = android.widget.LinearLayout.LayoutParams(dp(26), dp(26))
            clp.topMargin = dp(64); clp.rightMargin = dp(17)
            rowWrap.addView(close, clp)
        }
        rowWrap.addView(adv, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.WRAP_CONTENT,
            android.widget.LinearLayout.LayoutParams.WRAP_CONTENT))
        adCornerWrap.removeAllViews()
        adCornerWrap.addView(rowWrap, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT))
        adCard = adv
        adBadgeV = badge
        adCtaV = cta
        adViewMode = "corner"
    }

    // two placements, one ad: the bottom strip everywhere EXCEPT the
    // drawing screen (persistent, page reserves room through __adOn), and
    // on the drawing screen an intermittent corner card that replaces the
    // download button for a bounded window (page yields it via __adCorner).
    private var adCloseFloat: TextView? = null  // landscape corner X, beside the gear
    private var adCardShown = false       // strip on screen
    private var adCornerShown = false     // corner card on screen
    private val AD_ON_MS = 45000L         // corner window length
    private val AD_OFF_MS = 240000L       // corner rest between windows
    private fun adBase() = adWanted && adsUp && !adsRemovedFlag() && nativeAd != null
    private fun applyAd() {
        val lp = web.layoutParams as FrameLayout.LayoutParams
        if (lp.bottomMargin != 0) { lp.bottomMargin = 0; web.layoutParams = lp }
        // ---- strip half -------------------------------------------------
        val slot = adWanted && adsUp && !adsRemovedFlag() && !adOnProj
        val stripWant = slot && nativeAd != null
        if (stripWant != adCardShown) {
            adCardShown = stripWant
            adWrap.animate().cancel()
            if (stripWant) {
                if (adViewMode != "strip") buildStrip()
                val h = (if (adShownH > 0) adShownH
                         else (56 * resources.displayMetrics.density).toInt()).toFloat()
                adWrap.translationY = h; adWrap.alpha = 0f
                adWrap.visibility = android.view.View.VISIBLE
                adWrap.animate().translationY(0f).alpha(1f).setDuration(220)
                    .setInterpolator(android.view.animation.DecelerateInterpolator())
                    .withEndAction(null).start()
            } else {
                val h = (if (adShownH > 0) adShownH
                         else (56 * resources.displayMetrics.density).toInt()).toFloat()
                adWrap.animate().translationY(h).alpha(0f).setDuration(160)
                    .setInterpolator(android.view.animation.AccelerateInterpolator())
                    .withEndAction {
                        adWrap.visibility = android.view.View.GONE
                        adWrap.translationY = 0f; adWrap.alpha = 1f
                    }.start()
            }
        }
        js("window.__adOn && __adOn(" + slot + ")")
        // ---- corner half ------------------------------------------------
        if (adCornerShown && !(adBase() && adOnProj)) adCollapse()
        else if (!adCornerShown && adBase() && adOnProj) adTryShow()
        else if (!adCornerShown) adCornerWrap.removeCallbacks(adShowTry)
    }
    private val adShowTry = Runnable { adTryShow() }
    private val adAutoHide = Runnable { adCollapse() }
    private fun adTryShow() {
        adCornerWrap.removeCallbacks(adShowTry)
        if (adCornerShown || !(adBase() && adOnProj)) return
        val now = android.os.SystemClock.uptimeMillis()
        if (now < adNextShowAt) { adCornerWrap.postDelayed(adShowTry, adNextShowAt - now); return }
        // never materialize where a finger just was - wait for a quiet hand
        if (now - lastTouchMs < 3000) { adCornerWrap.postDelayed(adShowTry, 3000); return }
        if (adViewMode != "corner") buildCorner()
        adCornerShown = true
        adCornerWrap.animate().cancel()
        adCornerWrap.scaleX = 0.3f; adCornerWrap.scaleY = 0.3f; adCornerWrap.alpha = 0f
        adCornerWrap.visibility = android.view.View.VISIBLE
        adCornerWrap.post {
            // grow out of the download button's corner, visibly - never a snap
            adCornerWrap.pivotX = if (adLand()) 0f else adCornerWrap.width.toFloat()
            adCornerWrap.pivotY = if (adLand()) adCornerWrap.height.toFloat() else 0f
            adCornerWrap.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(350)
                .setInterpolator(android.view.animation.DecelerateInterpolator()).start()
        }
        adCloseFloat?.visibility = android.view.View.VISIBLE
        js("window.__adCorner && __adCorner(true)")
        adCornerWrap.removeCallbacks(adAutoHide)
        adCornerWrap.postDelayed(adAutoHide, AD_ON_MS)
    }
    private fun adCollapse() {
        adCornerWrap.removeCallbacks(adAutoHide)
        if (!adCornerShown) return
        adCornerShown = false
        adCloseFloat?.visibility = android.view.View.GONE
        adNextShowAt = android.os.SystemClock.uptimeMillis() + AD_OFF_MS
        adCornerWrap.animate().cancel()
        adCornerWrap.pivotX = if (adLand()) 0f else adCornerWrap.width.toFloat()
        adCornerWrap.pivotY = if (adLand()) adCornerWrap.height.toFloat() else 0f
        adCornerWrap.animate().scaleX(0.3f).scaleY(0.3f).alpha(0f).setDuration(250)
            .setInterpolator(android.view.animation.AccelerateInterpolator())
            .withEndAction {
                adCornerWrap.visibility = android.view.View.GONE
                adCornerWrap.scaleX = 1f; adCornerWrap.scaleY = 1f; adCornerWrap.alpha = 1f
            }.start()
        js("window.__adCorner && __adCorner(false)")
        // a fresh creative earns the next window (re-showing one doesn't)
        loadNative()
        if (adBase() && adOnProj) adCornerWrap.postDelayed(adShowTry, AD_OFF_MS)
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

    // ---- remove-ads purchase (Play Billing): the one-time product
    // "remove_ads" flips a local flag and the ad stack never starts
    // again; the entitlement restores from Play's record every launch
    private fun adsRemovedFlag() = getSharedPreferences("iap", 0).getBoolean("noads", false)
    private fun grantNoAds() {
        getSharedPreferences("iap", 0).edit().putBoolean("noads", true).apply()
        logLine("remove_ads granted")
        runOnUiThread {
            adWanted = false
            nativeAd?.destroy(); nativeAd = null; adCard = null
            adBadgeV = null; adCtaV = null
            try { adWrap.removeAllViews() } catch (e: Exception) {}
            applyAd()
            js("window.__adsRemovedUI && __adsRemovedUI()")
        }
    }
    private fun handlePurchase(p: com.android.billingclient.api.Purchase) {
        if (!p.products.contains("remove_ads")) return
        logLine("billing: remove_ads state=" + p.purchaseState + " acked=" + p.isAcknowledged)
        if (p.purchaseState == com.android.billingclient.api.Purchase.PurchaseState.PENDING) {
            js("toast && toast(" + org.json.JSONObject.quote(
                "purchase pending - ads clear once payment completes") + ", true, 5000)")
            return
        }
        if (p.purchaseState != com.android.billingclient.api.Purchase.PurchaseState.PURCHASED) return
        if (!p.isAcknowledged) {
            val ack = com.android.billingclient.api.AcknowledgePurchaseParams.newBuilder()
                .setPurchaseToken(p.purchaseToken).build()
            billing?.acknowledgePurchase(ack) {}
        }
        if (!adsRemovedFlag()) grantNoAds()
    }
    private fun initBilling() {
        try {
            val c = com.android.billingclient.api.BillingClient.newBuilder(this)
                .setListener { br, purchases ->
                    if (br.responseCode ==
                        com.android.billingclient.api.BillingClient.BillingResponseCode.OK
                        && purchases != null) for (p in purchases) handlePurchase(p)
                }
                .enablePendingPurchases(
                    com.android.billingclient.api.PendingPurchasesParams.newBuilder()
                        .enableOneTimeProducts().build())
                .build()
            billing = c
            c.startConnection(object : com.android.billingclient.api.BillingClientStateListener {
                override fun onBillingSetupFinished(br: com.android.billingclient.api.BillingResult) {
                    if (br.responseCode !=
                        com.android.billingclient.api.BillingClient.BillingResponseCode.OK) return
                    val qp = com.android.billingclient.api.QueryPurchasesParams.newBuilder()
                        .setProductType(
                            com.android.billingclient.api.BillingClient.ProductType.INAPP)
                        .build()
                    c.queryPurchasesAsync(qp) { br2, list ->
                        logLine("billing: query rc=" + br2.responseCode
                            + " purchases=" + list.size + " noads=" + adsRemovedFlag())
                        if (br2.responseCode ==
                            com.android.billingclient.api.BillingClient.BillingResponseCode.OK) {
                            var owned = false
                            for (p in list) {
                                if (p.products.contains("remove_ads") && p.purchaseState ==
                                    com.android.billingclient.api.Purchase.PurchaseState.PURCHASED)
                                    owned = true
                                handlePurchase(p)
                            }
                            // a refunded purchase must give the ads back: only a
                            // definitive OK-and-absent answer revokes (an offline
                            // or failed query never does)
                            if (!owned && adsRemovedFlag()) {
                                getSharedPreferences("iap", 0).edit()
                                    .putBoolean("noads", false).apply()
                                logLine("remove_ads revoked - no purchase on this account")
                            }
                        }
                    }
                }
                override fun onBillingServiceDisconnected() {}
            })
        } catch (e: Throwable) { logLine("billing init: " + e.message) }
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
        private var decBuf: java.io.ByteArrayOutputStream? = null
        private fun decodeBytes(bytes: ByteArray): String {
            val probe = android.graphics.BitmapFactory.Options().apply { inJustDecodeBounds = true }
            android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size, probe)
            if (probe.outWidth <= 0 || probe.outHeight <= 0) return ""
            var sample = 1
            while (probe.outWidth / sample > 4096 || probe.outHeight / sample > 4096) sample *= 2
            val opts = android.graphics.BitmapFactory.Options().apply { inSampleSize = sample }
            val bm = android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size, opts)
                ?: return ""
            val out = java.io.ByteArrayOutputStream()
            bm.compress(android.graphics.Bitmap.CompressFormat.JPEG, 92, out)
            bm.recycle()
            return android.util.Base64.encodeToString(out.toByteArray(), android.util.Base64.NO_WRAP)
        }
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
        // the page's decode-of-last-resort: WebView can't read HEIC/HEIF,
        // the OS codec can (API 28+). Downsampled to <=4096px, returned as
        // JPEG base64; empty string = the OS couldn't read it either.
        // Called synchronously off the UI thread by the WebView JS bridge.
        @JavascriptInterface
        fun decodeImage(b64: String): String {
            return try {
                decodeBytes(android.util.Base64.decode(b64, android.util.Base64.DEFAULT))
            } catch (e: Exception) { "" } catch (e: OutOfMemoryError) { "" }
        }
        // chunked variant: low-RAM (Android Go) WebViews can't build one
        // giant base64 string for a 40MP photo without killing the
        // renderer - the page streams ~3MB slices instead. The JS bridge
        // serialises calls on one thread, so the buffer needs no locking.
        @JavascriptInterface
        fun decodeBegin() { decBuf = java.io.ByteArrayOutputStream() }
        @JavascriptInterface
        fun decodeChunk(b64: String): Boolean {
            return try {
                val buf = decBuf ?: return false
                buf.write(android.util.Base64.decode(b64, android.util.Base64.DEFAULT))
                true
            } catch (e: Exception) { decBuf = null; false }
              catch (e: OutOfMemoryError) { decBuf = null; false }
        }
        @JavascriptInterface
        fun decodeEnd(): String {
            val bytes = try { decBuf?.toByteArray() } catch (e: OutOfMemoryError) { null }
            decBuf = null
            if (bytes == null) return ""
            return try { decodeBytes(bytes) }
            catch (e: Exception) { "" } catch (e: OutOfMemoryError) { "" }
        }
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
            val c = try { android.graphics.Color.parseColor(hex) } catch (e: Exception) { return }
            adAccentCol = c
            // re-tint the card already on screen - the accent follows
            // immediately, not at the next 75s refresh
            runOnUiThread {
                val w = Math.max(1, resources.displayMetrics.density.toInt())
                adBadgeV?.let { v ->
                    v.setTextColor(c)
                    (v.background as? android.graphics.drawable.GradientDrawable)?.setStroke(w, c)
                }
                adCtaV?.let { v ->
                    (v.background as? android.graphics.drawable.GradientDrawable)?.setColor(c)
                }
            }
        }
        @JavascriptInterface
        fun adsRemoved(): Boolean = adsRemovedFlag()
        @JavascriptInterface
        fun buyRemoveAds() {
            runOnUiThread {
                val c = billing
                if (c == null || !c.isReady) {
                    js("toast && toast('purchase unavailable - try again shortly', false)")
                    return@runOnUiThread
                }
                val prod = com.android.billingclient.api.QueryProductDetailsParams.Product.newBuilder()
                    .setProductId("remove_ads")
                    .setProductType(com.android.billingclient.api.BillingClient.ProductType.INAPP)
                    .build()
                val qp = com.android.billingclient.api.QueryProductDetailsParams.newBuilder()
                    .setProductList(listOf(prod)).build()
                c.queryProductDetailsAsync(qp) { br, details ->
                    val d = details.productDetailsList.firstOrNull()
                    if (br.responseCode !=
                        com.android.billingclient.api.BillingClient.BillingResponseCode.OK
                        || d == null) {
                        js("toast && toast('purchase not available yet', false)")
                        return@queryProductDetailsAsync
                    }
                    val flow = com.android.billingclient.api.BillingFlowParams.newBuilder()
                        .setProductDetailsParamsList(listOf(
                            com.android.billingclient.api.BillingFlowParams.ProductDetailsParams
                                .newBuilder().setProductDetails(d).build()))
                        .build()
                    runOnUiThread { c.launchBillingFlow(this@MainActivity, flow) }
                }
            }
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
                adCard?.let { v ->
                    val g = v.background as? android.graphics.drawable.GradientDrawable
                    if (g != null) g.setColor(c) else v.setBackgroundColor(c)
                }
                applyAd()
            }
        }
        // the page flags the drawing screen: there the strip yields to the
        // intermittent corner card (and only there)
        @JavascriptInterface
        fun adProj(on: Boolean) {
            runOnUiThread { if (adOnProj != on) { adOnProj = on; applyAd() } }
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
        // RETIRED (Play Deceptive Behavior enforcement, version 187
        // rejection): swapping launcher icons required disabling the
        // MainActivity launcher component, which Play's scanner reads as
        // "app hides its icon". The bridge stays as a no-op so cached
        // pages calling it do nothing.
        @JavascriptInterface
        fun setIcon(idx: Int) {}
        // WebView vibration varies by OEM even with the permission; the
        // bridge drives the vibrator directly - single, clean pulses
        @JavascriptInterface
        fun haptic(kind: String) {
            try {
                val v = getSystemService(android.os.Vibrator::class.java) ?: return
                val ms = if (kind == "ok") 24L else 10L
                v.vibrate(android.os.VibrationEffect.createOneShot(ms,
                    android.os.VibrationEffect.DEFAULT_AMPLITUDE))
            } catch (e: Exception) {}
        }
        // the in-app chooser's Downloads option: MediaStore writes make the
        // destination certain, with no system picker round-trip
        @JavascriptInterface
        fun saveImageDl(name: String, mime: String, b64: String) {
            runOnUiThread {
                try {
                    val bytes = Base64.decode(b64, Base64.DEFAULT)
                    if (android.os.Build.VERSION.SDK_INT >= 29) {
                        val cv = android.content.ContentValues().apply {
                            put(android.provider.MediaStore.Downloads.DISPLAY_NAME, name)
                            put(android.provider.MediaStore.Downloads.MIME_TYPE, mime)
                        }
                        val uri = contentResolver.insert(
                            android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI, cv)
                            ?: throw Exception("no uri")
                        contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                        js("toast && toast('saved to Downloads')")
                    } else {
                        val f = java.io.File(getExternalFilesDir(null), name)
                        f.writeBytes(bytes)
                        js("toast && toast('saved: Android/data/app.realism.draw/files')")
                    }
                } catch (e: Exception) { js("toast && toast('save failed', false)") }
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

    // the corner card grows out of the download button's corner, and the
    // button lives top-right in portrait but bottom-left in landscape
    private fun adLand() = resources.configuration.orientation ==
        android.content.res.Configuration.ORIENTATION_LANDSCAPE
    private fun dispRot(): Int =
        previewView.display?.rotation
            ?: @Suppress("DEPRECATION") windowManager.defaultDisplay.rotation
    private fun adCornerParams(): FrameLayout.LayoutParams {
        val m = (8 * resources.displayMetrics.density).toInt()
        val land = adLand()
        val clp = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT,
            if (land) android.view.Gravity.BOTTOM or android.view.Gravity.START
            else android.view.Gravity.TOP or android.view.Gravity.END)
        if (land) { clp.bottomMargin = m; clp.leftMargin = m }
        else { clp.topMargin = m; clp.rightMargin = m }
        return clp
    }
    override fun onConfigurationChanged(newConfig: android.content.res.Configuration) {
        super.onConfigurationChanged(newConfig)
        // rotation does not recreate the activity (configChanges) - re-lay
        // the ad surfaces for the new orientation; the page restarts the
        // camera itself from its resize handler, and re-sends adProj so
        // the strip/corner split follows the orientation
        runOnUiThread {
            adCornerWrap.layoutParams = adCornerParams()
            if (nativeAd != null) {
                if (adViewMode == "strip") buildStrip()
                else if (adViewMode == "corner") buildCorner()
            }
            if (previewView.visibility == android.view.View.VISIBLE)
                js("window.__natRotate && __natRotate()")
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
                .setTargetRotation(dispRot())
            // RAW alone is legal on the in-memory path; the display JPEG is
            // rendered from the RAW plane itself - one capture, aligned planes
            if (rawMode) stillB.setOutputFormat(ImageCapture.OUTPUT_FORMAT_RAW)
            val previewB = Preview.Builder()
                .setResolutionSelector(ResolutionSelector.Builder()
                    .setAspectRatioStrategy(AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY)
                    .build())
                .setTargetRotation(dispRot())
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
                    // display-oriented frame straight from the use case's own
                    // rotation metadata: 90/270 means the sensor frame turns
                    // sideways on this display, so its dimensions swap
                    val rd = ri.rotationDegrees
                    val fw = if (rd == 90 || rd == 270) ri.resolution.height else ri.resolution.width
                    val fh = if (rd == 90 || rd == 270) ri.resolution.width else ri.resolution.height
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
