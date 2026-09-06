# The page talks to the shell by name: every @JavascriptInterface method
# on the RealismCam bridge must survive shrinking and renaming, or the
# web app silently loses its native half.
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# The ads, UMP, and billing libraries ship their own consumer rules in
# their AARs; nothing extra needed here.
