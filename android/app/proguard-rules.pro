# The page talks to the shell by name: every @JavascriptInterface method
# on the RealismCam bridge must survive shrinking and renaming, or the
# web app silently loses its native half.
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# The ads, UMP, and billing libraries ship their own consumer rules in
# their AARs; nothing extra needed here.

# Maximal R8 optimization: flatten packages and allow access widening so
# more methods inline and dex shrinks further.
-repackageclasses ''
-allowaccessmodification
