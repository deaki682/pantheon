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
    private var modeAnnounced = false
    private lateinit var diag: TextView
    private var booted = false

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
        setContentView(root)
        run {
            val prefs = getSharedPreferences("cam", 0)
            if (prefs.getInt("amnesty", 0) < 2) {
                prefs.edit().remove("ceiling").remove("attempting")
                    .putInt("amnesty", 2).apply()
            }
            prefs.getString("crash", null)?.let {
                prefs.edit().remove("crash").commit()
                report("last run crashed:\n" + it)
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
                if (m.messageLevel() == android.webkit.ConsoleMessage.MessageLevel.ERROR)
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
        // the system back gesture walks the page's screens (the page arms one
        // history entry whenever it is deeper than the project page) and only
        // closes the app from the project page itself
        onBackPressedDispatcher.addCallback(this,
            object : androidx.activity.OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    if (web.canGoBack()) web.goBack()
                    else { isEnabled = false; onBackPressedDispatcher.onBackPressed() }
                }
            })
        web.addJavascriptInterface(Bridge(), "RealismCam")
        val port = LocalServer.start(this)
        if (port == 0) report("local server failed to bind")
        else web.loadUrl("http://127.0.0.1:$port/index.html")
        web.postDelayed({
            if (!booted) report("page did not finish loading in 8s (progress ${web.progress}%)")
        }, 8000)
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
            val preview = Preview.Builder()
                .setResolutionSelector(ResolutionSelector.Builder()
                    .setAspectRatioStrategy(AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY)
                    .build())
                .setTargetRotation(Surface.ROTATION_0)
                .build()
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
                        report("capture mode: " + (if (capLabel == "") "standard" else capLabel))
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
        val rot = image.imageInfo.rotationDegrees
        val ow = if (rot % 180 == 0) w else h
        val oh = if (rot % 180 == 0) h else w
        val out = ShortArray(ow * oh)
        val row = ShortArray(rowShorts)
        val row2 = ShortArray(rowShorts)
        for (y in 0 until h) {
            val yn = if (y + 1 < h) y + 1 else y
            sb.position(y * rowShorts); sb.get(row, 0, minOf(rowShorts, sb.remaining()))
            sb.position(yn * rowShorts); sb.get(row2, 0, minOf(rowShorts, sb.remaining()))
            for (x in 0 until w) {
                val xn = if (x + 1 < w) x + 1 else x
                var sum = (row[x].toInt() and 0xFFFF) + (row[xn].toInt() and 0xFFFF) +
                          (row2[x].toInt() and 0xFFFF) + (row2[xn].toInt() and 0xFFFF)
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
