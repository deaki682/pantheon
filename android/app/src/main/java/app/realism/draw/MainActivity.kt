package app.realism.draw

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.util.Base64
import android.view.Surface
import android.webkit.JavascriptInterface
import android.webkit.PermissionRequest
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
        if (granted) pendingStart?.run() else js("window.__natFail && __natFail('denied')")
        pendingStart = null
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
                    report("load error ${'$'}{error.errorCode}: ${'$'}{error.description} @ ${'$'}{request.url}")
            }
            override fun onReceivedHttpError(view: WebView, request: WebResourceRequest,
                                             response: WebResourceResponse) {
                if (request.isForMainFrame)
                    report("http ${'$'}{response.statusCode} @ ${'$'}{request.url}")
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(m: android.webkit.ConsoleMessage): Boolean {
                if (m.messageLevel() == android.webkit.ConsoleMessage.MessageLevel.ERROR)
                    report("js: ${'$'}{m.message()} (${'$'}{m.sourceId()}:${'$'}{m.lineNumber()})")
                return true
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
            if (!booted) report("page did not finish loading in 8s (progress ${'$'}{web.progress}%)")
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
                val fourThree = ResolutionSelector.Builder()
                    .setAspectRatioStrategy(AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY)
                    .build()
                val preview = Preview.Builder()
                    .setResolutionSelector(fourThree)
                    .setTargetRotation(Surface.ROTATION_0)
                    .build()
                val still = ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                    .setResolutionSelector(ResolutionSelector.Builder()
                        .setAspectRatioStrategy(AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY)
                        .setResolutionStrategy(ResolutionStrategy.HIGHEST_AVAILABLE_STRATEGY)
                        .build())
                    .setTargetRotation(Surface.ROTATION_0)
                    .build()
                imageCapture = still
                prov.unbindAll()
                camera = prov.bindToLifecycle(this, CameraSelector.DEFAULT_BACK_CAMERA, preview, still)
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
                js("window.__natFail && __natFail('open')")
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun takeStill() {
        val still = imageCapture ?: run { js("window.__natFail && __natFail('nocap')"); return }
        still.takePicture(captureExec, object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: ImageProxy) {
                val buf = image.planes[0].buffer
                val bytes = ByteArray(buf.remaining()); buf.get(bytes)
                image.close()
                val b64 = Base64.encodeToString(bytes, Base64.NO_WRAP)
                js("window.__natShot && __natShot('data:image/jpeg;base64,$b64')")
            }
            override fun onError(e: ImageCaptureException) {
                js("window.__natFail && __natFail('shot')")
            }
        })
    }

    private fun closeCamera() {
        web.setBackgroundColor(Color.BLACK)
        try { provider?.unbindAll() } catch (e: Exception) {}
        camera = null; imageCapture = null
        previewView.visibility = android.view.View.GONE
    }

    override fun onDestroy() { captureExec.shutdown(); super.onDestroy() }
}
