plugins {
    id("com.android.application")
    id("com.chaquo.python")
}

// The release version comes from the git tag in CI (v1.2.3 -> "1.2.3", code 10203).
val appVersionName: String = (System.getenv("APP_VERSION") ?: "1.0.0").removePrefix("v")
val appVersionCode: Int = appVersionName.split(".").map { it.toIntOrNull() ?: 0 }
    .let { (it + listOf(0, 0, 0)).take(3) }
    .let { (major, minor, patch) -> major * 10000 + minor * 100 + patch }

// The game itself is the Flask app at the root of the repository. It is copied into a
// "priceguesser" package so Chaquopy can extract it (Flask needs real files for templates).
val webAppDir = layout.buildDirectory.dir("generated/webapp")
val copyWebApp by tasks.registering(Sync::class) {
    val repoRoot = rootProject.projectDir.parentFile
    from(repoRoot) {
        include("main.py", "game.py", "forms.py", "Zillow/**", "templates/**", "static/**")
        exclude("**/__pycache__/**", "**/*.pyc")
    }
    from(resources.text.fromString("")) {
        rename { "__init__.py" }
    }
    into(webAppDir.map { it.dir("priceguesser") })
}

android {
    namespace = "com.brigham4210.priceguesser"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.brigham4210.priceguesser"
        minSdk = 24
        targetSdk = 36
        versionCode = appVersionCode
        versionName = appVersionName

        ndk {
            // Python 3.12 is 64-bit only.
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    signingConfigs {
        create("release") {
            val keystore = System.getenv("ANDROID_KEYSTORE_PATH")
            if (keystore != null) {
                storeFile = file(keystore)
                storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("ANDROID_KEY_ALIAS")
                keyPassword = System.getenv("ANDROID_KEYSTORE_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            if (System.getenv("ANDROID_KEYSTORE_PATH") != null) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

chaquopy {
    defaultConfig {
        version = "3.12"
        pip {
            install("-r", rootProject.projectDir.parentFile.resolve("requirements.txt").path)
        }
        extractPackages("priceguesser")
    }
    sourceSets {
        getByName("main") {
            srcDir(webAppDir)
        }
    }
}

// Chaquopy reads the copied web app, so copy it before anything else runs.
tasks.named("preBuild") { dependsOn(copyWebApp) }
tasks.matching { it.name.startsWith("merge") && it.name.contains("PythonSources") }.configureEach {
    dependsOn(copyWebApp)
}
