plugins {
    id("com.android.application")
}

android {
    namespace = "ch.animalhealth.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "ch.animalhealth.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 900001
        versionName = "0.9.0-alpha.1"
    }

    buildTypes {
        getByName("debug") {
            applicationIdSuffix = ".alpha"
            versionNameSuffix = "-debug"
        }
        getByName("release") {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
