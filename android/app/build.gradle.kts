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
        versionCode = 900002
        versionName = "0.9.0-alpha.2"
    }

    sourceSets {
        getByName("main").assets.srcDirs(
            "src/main/assets",
            "../../custom_components/animal_health/frontend",
            "../../custom_components/animal_health/catalogs"
        )
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
        isCoreLibraryDesugaringEnabled = true
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
}
