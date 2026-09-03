import java.util.Base64

plugins {
    id("com.android.application")
}

val animalHealthVersion = "0.9.0-alpha.7"
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
        require(ordered.size == 99) {
            "Expected 99 Animal Health frontend parts, found ${ordered.size}"
        }
        val target = generatedSharedUiAssets.get().file("animal-health-panel.js").asFile
        target.parentFile.mkdirs()
        target.writeText(ordered.joinToString(separator = "") { it.readText() })
    }
}

val alphaSigningSource = file("../alpha-signing-keystore.b64")
val generatedAlphaSigningFile = layout.buildDirectory.file("generated/alpha-signing/animal-health-alpha.jks")
val prepareAlphaSigning by tasks.registering {
    inputs.file(alphaSigningSource)
    outputs.file(generatedAlphaSigningFile)
    doLast {
        val target = generatedAlphaSigningFile.get().asFile
        target.parentFile.mkdirs()
        val encoded = alphaSigningSource.readText().filterNot(Char::isWhitespace)
        target.writeBytes(Base64.getDecoder().decode(encoded))
    }
}

android {
    namespace = "ch.animalhealth.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "ch.animalhealth.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 900007
        versionName = animalHealthVersion
        buildConfigField("String", "ANIMAL_HEALTH_VERSION", "\"$animalHealthVersion\"")
    }

    buildFeatures {
        buildConfig = true
    }

    sourceSets {
        getByName("main").assets.srcDirs(
            "src/main/assets",
            "../../custom_components/animal_health/frontend",
            "../../custom_components/animal_health/catalogs"
        )
        getByName("main").assets.srcDir(generatedSharedUiAssets)
    }

    signingConfigs {
        create("alpha") {
            storeFile = generatedAlphaSigningFile.get().asFile
            storePassword = "animalhealthalpha"
            keyAlias = "animal-health-alpha"
            keyPassword = "animalhealthalpha"
        }
    }

    buildTypes {
        getByName("debug") {
            applicationIdSuffix = ".alpha"
            versionNameSuffix = "-debug"
            signingConfig = signingConfigs.getByName("alpha")
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
    dependsOn(bundleSharedFrontend, prepareAlphaSigning)
}

dependencies {
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
}
