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
    private lateinit var diag: TextView
    private var booted = false

    private fun report(msg: String) {
        Log.e("Realism", msg)
        runOnUiThread {
            diag.visibility = android.view.View.VISIBLE
            diag.append(msg + "\n")
        }
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
        fun capture() { runOnUiThread { takeStill() } }
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

    private fun openCamera(x: Int, y: Int, w: Int, h: Int) {
        web.setBackgroundColor(Color.TRANSPARENT)
        val lp = FrameLayout.LayoutParams(w, h)
        lp.leftMargin = x; lp.topMargin = y
        previewView.layoutParams = lp
        previewView.visibility = android.view.View.VISIBLE
        val fut = ProcessCameraProvider.getInstance(this)
        fut.addListener({
            try {
                val prov = fut.get(); provider = prov
                // capture-quality ladder, decided per device, no settings:
                // 1. RAW alongside JPEG - true sensor bits for the edit sliders
                // 2. the vendor's own HDR/AUTO extension - the camera app's magic
                // 3. plain maximize-quality JPEG
                var selector = CameraSelector.DEFAULT_BACK_CAMERA
                capLabel = ""; rawMode = false
                val stillB = ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                    .setResolutionSelector(ResolutionSelector.Builder()
                        .setAspectRatioStrategy(AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY)
                        .setResolutionStrategy(ResolutionStrategy.HIGHEST_AVAILABLE_STRATEGY)
                        .build())
                    .setTargetRotation(Surface.ROTATION_0)
                try {
                    val info = prov.getCameraInfo(selector)
                    val caps = ImageCapture.getImageCaptureCapabilities(info)
                    if (caps.supportedOutputFormats.contains(ImageCapture.OUTPUT_FORMAT_RAW_JPEG)) {
                        stillB.setOutputFormat(ImageCapture.OUTPUT_FORMAT_RAW_JPEG)
                        rawMode = true; capLabel = "raw"
                    }
                } catch (e: Throwable) { rawMode = false; capLabel = "" }
                if (!rawMode) try {
                    val em = ExtensionsManager.getInstanceAsync(this, prov).get()
                    for ((mode, name) in listOf(ExtensionMode.AUTO to "auto",
                                                ExtensionMode.HDR to "hdr")) {
                        if (em.isExtensionAvailable(CameraSelector.DEFAULT_BACK_CAMERA, mode)) {
                            selector = em.getExtensionEnabledCameraSelector(
                                CameraSelector.DEFAULT_BACK_CAMERA, mode)
                            capLabel = name
                            break
                        }
                    }
                } catch (e: Throwable) {}
                val fourThree = ResolutionSelector.Builder()
                    .setAspectRatioStrategy(AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY)
                    .build()
                val preview = Preview.Builder()
                    .setResolutionSelector(fourThree)
                    .setTargetRotation(Surface.ROTATION_0)
                    .build()
                val still = stillB.build()
                imageCapture = still
                prov.unbindAll()
                camera = prov.bindToLifecycle(this, selector, preview, still)
                preview.setSurfaceProvider(previewView.surfaceProvider)
                // report the display-oriented frame size once it is known
                var tries = 0
                fun report() {
                    val ri = preview.resolutionInfo
                    if (ri != null) {
                        val rot = ri.rotationDegrees
                        val fw = if (rot % 180 == 0) ri.resolution.width else ri.resolution.height
                        val fh = if (rot % 180 == 0) ri.resolution.height else ri.resolution.width
                        js("window.__natReady && __natReady($fw,$fh)")
                    } else if (tries++ < 40) previewView.postDelayed({ report() }, 50)
                    else js("window.__natFail && __natFail('nores')")
                }
                report()
            } catch (e: Exception) {
                report("camera open failed: ${e.message}")
                js("window.__natFail && __natFail('open')")
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun takeStill() {
        val still = imageCapture ?: run { js("window.__natFail && __natFail('nocap')"); return }
        val expectRaw = rawMode
        val got = java.util.concurrent.ConcurrentHashMap<String, String>()
        var timer: Runnable? = null
        fun deliver() {
            val j = got["jpeg"] ?: return
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
        still.takePicture(captureExec, object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: ImageProxy) {
                try {
                    if (image.format == android.graphics.ImageFormat.RAW_SENSOR) {
                        val payload = demosaicLuma(image)
                        if (payload != null) got["raw"] = LocalServer.park("application/octet-stream", payload)
                    } else {
                        val buf = image.planes[0].buffer
                        val bytes = ByteArray(buf.remaining()); buf.get(bytes)
                        got["jpeg"] = LocalServer.park("image/jpeg", bytes)
                    }
                } catch (e: Throwable) {
                    report("capture decode: ${e.message}")
                } finally { image.close() }
                if (got.containsKey("jpeg") && (!expectRaw || got.containsKey("raw"))) {
                    timer?.let { web.removeCallbacks(it) }
                    deliver()
                }
            }
            override fun onError(e: ImageCaptureException) {
                timer?.let { web.removeCallbacks(it) }
                report("capture: ${e.message}")
                js("window.__natFail && __natFail('shot')")
            }
        })
    }

    // RAW -> full-resolution 16-bit LUMA, no CFA-pattern logic needed: every
    // 2x2 Bayer window holds {R, G, G, B}, and a charcoal drawing is neutral,
    // so the flat window mean IS its luminance. Black/white levels from the
    // camera characteristics, gamma 1/2.2 into a 0..255*256 fixed-point plane
    // the page divides back into floats - the real 'shoot raw' the sliders
    // have been waiting for.
    @androidx.annotation.OptIn(androidx.camera.camera2.interop.ExperimentalCamera2Interop::class)
    private fun demosaicLuma(image: ImageProxy): ByteArray? {
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
        val bb = java.nio.ByteBuffer.allocate(8 + out.size * 2)
            .order(java.nio.ByteOrder.LITTLE_ENDIAN)
        bb.putInt(ow); bb.putInt(oh)
        bb.asShortBuffer().put(out)
        return bb.array()
    }

    private fun closeCamera() {
        web.setBackgroundColor(Color.BLACK)
        try { provider?.unbindAll() } catch (e: Exception) {}
        camera = null; imageCapture = null
        previewView.visibility = android.view.View.GONE
    }

    override fun onDestroy() { captureExec.shutdown(); super.onDestroy() }
}
