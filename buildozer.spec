[app]
title = Blue Omega
package.name = blueomega
package.domain = org.blueomega
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db
version = 1.0
requirements = python3,kivy==2.2.1,kivymd,anthropic,requests,sqlite3,SpeechRecognition,pyttsx3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.minapi = 29
android.sdk = 33
android.ndk = 25b
android.arch = arm64-v8a
android.release_artifact = apk
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
