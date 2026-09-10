# Android WebView wrapper

A minimal Android app that embeds the web tracker as a WebView, so the tracker
becomes a real Android app that installs from an APK and works fully offline.

The web assets (`index.html`, `habits.json`, service worker, icons) are copied
from the repo root into `app/src/main/assets/` by the `apk` GitHub Actions
workflow before the build. Locally, if you want to build too, copy them yourself:

```bash
cp ../index.html ../habits.json ../manifest.webmanifest ../sw.js ../icon*.svg \
   app/src/main/assets/
gradle assembleRelease
# APK ends up in app/build/outputs/apk/release/app-release.apk
```

The APK is signed with a stable local keystore (`app/debug.keystore`, standard
Android debug password) so successive rebuilds install as **updates** on the
same device instead of failing with "signatures don't match". This keystore is
committed intentionally: this app is not distributed through the Play Store,
just installed by sideload on the author's own device.
