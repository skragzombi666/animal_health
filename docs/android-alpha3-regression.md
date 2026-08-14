# Android alpha.3 regression

The Android wrapper must load the Animal Health frontend as one assembled JavaScript program.

The `animal-health-panel.part*.js` files are source chunks and are intentionally not standalone scripts. The Android build task concatenates all 40 ordered parts into `animal-health-panel.js`; `android-shared-ui.js` loads only that bundle.

This file documents the startup regression found in 0.9.0-alpha.2 and the invariant covered by `tests/test_android_alpha.py`.
