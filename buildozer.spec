[app]

# ── Identity ──────────────────────────────────────────────────────────────────
title           = Todo List
package.name    = todolist
package.domain  = ir.shayannezhad
version         = 1.0

# ── Source ────────────────────────────────────────────────────────────────────
# Buildozer always uses main.py as the entry point (see main.py in this folder)
source.dir      = .
source.include_exts = py,ttf,json
source.include_patterns = fonts/*.ttf

# ── Dependencies ──────────────────────────────────────────────────────────────
requirements    = python3,kivy,python-bidi,arabic-reshaper

# ── UI / behaviour ───────────────────────────────────────────────────────────
orientation     = portrait
fullscreen      = 0

# ── Android ──────────────────────────────────────────────────────────────────
android.api             = 33
android.minapi          = 21
android.ndk             = 25b
android.archs           = arm64-v8a, armeabi-v7a

# ── Buildozer internals ───────────────────────────────────────────────────────
log_level       = 2
warn_on_root    = 1

# (bool) Automatically accept SDK license agreements (required for CI/non-interactive builds)
android.accept_sdk_license = True
