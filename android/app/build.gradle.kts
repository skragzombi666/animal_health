plugins {
    id("com.android.application")
}

val sharedFrontendSource = file("../../custom_components/animal_health/frontend")
val generatedSharedUiAssets = layout.buildDirectory.dir("generated/animalHealthSharedUi")
val bundleSharedFrontend by tasks.registering {
    val parts = fileTree(sharedFrontendSource) {
        include("animal-health-panel.part*.js")
    }
    inputs.files(parts)
    outputs.file(generatedSharedUiAssets.map { it.file("animal-health-panel.js") })
    doLast {
        val ordered = parts.files.sortedBy { it.name }
        require(ordered.size == 40) {
            "Expected 40 Animal Health frontend parts, found ${ordered.size}"
        }
        val target = generatedSharedUiAssets.get().file("animal-health-panel.js").asFile
        target.parentFile.mkdirs()
        target.writeText(ordered.joinToString(separator = "") { it.readText() })
    }
}

android {
    namespace = "ch.animalhealth.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "ch.animalhealth.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 900003
        versionName = "0.9.0-alpha.3"
    }

    sourceSets {
        getByName("main").assets.srcDirs(
            "src/main/assets",
            "../../custom_components/animal_health/frontend",
            "../../custom_components/animal_health/catalogs"
        )
        getByName("main").assets.srcDir(generatedSharedUiAssets)
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

tasks.named("preBuild").configure {
    dependsOn(bundleSharedFrontend)
}

dependencies {
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
}
