// DeviceCapabilities.kt — generic template (Phase 5 pattern)
// Place in the app module, initialize once at startup, memoize.
// Consumers ask for CAPABILITIES, never for Build.MODEL strings.
// Verify every field on the real target device before trusting it.
package your.app.package.op7

import android.app.ActivityManager
import android.content.Context
import android.content.pm.PackageManager
import android.media.MediaCodecInfo
import android.media.MediaCodecList
import android.os.Build

data class DeviceCapabilities(
    val abiList: List<String>,
    val is64Bit: Boolean,
    val apiLevel: Int,
    val manufacturer: String,
    val model: String,
    val totalRamBytes: Long,
    val memoryClassMb: Int,
    val largeMemoryClassMb: Int,
    val isLowRamDevice: Boolean,
    val glesVersion: String?,
    val vulkanSupported: Boolean,
    val openGlEsSupported: Boolean,
    val hardwareDecoders: List<Pair<String, Boolean>>, // codecName -> isHardware
    val displayWidthPx: Int,
    val displayHeightPx: Int,
    val densityDpi: Int,
) {
    val hasArm64Only: Boolean get() = abiList == listOf("arm64-v8a")
    val has8GbRamClass: Boolean get() = totalRamBytes >= 7L * 1024 * 1024 * 1024
    fun hasHardwareDecoder(mimePrefix: String): Boolean = hardwareDecoders.any { it.first.startsWith(mimePrefix) && it.second }

    companion object {
        @Volatile private var cached: DeviceCapabilities? = null
        fun get(context: Context): DeviceCapabilities = cached ?: synchronized(this) {
            cached ?: capture(context).also { cached = it }
        }

        private fun capture(context: Context): DeviceCapabilities {
            val am = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
            val mem = ActivityManager.MemoryInfo().also { am.getMemoryInfo(it) }
            val pm = context.packageManager
            val display = context.resources.displayMetrics

            val codecs = mutableListOf<Pair<String, Boolean>>()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                for (info in MediaCodecList(MediaCodecList.ALL_CODECS).codecInfos) {
                    if (info.isEncoder) continue
                    val isHw = info.isHardwareAccelerated
                    val name = info.name
                    // keep one entry per distinct component; type it by supported MIME type
                    val mime = info.supportedTypes.firstOrNull() ?: "unknown"
                    codecs.add("$mime/$name" to isHw)
                }
            }

            return DeviceCapabilities(
                abiList = Build.SUPPORTED_ABIS.toList(),
                is64Bit = Build.SUPPORTED_64_BIT_ABIS.isNotEmpty(),
                apiLevel = Build.VERSION.SDK_INT,
                manufacturer = Build.MANUFACTURER,
                model = Build.MODEL,
                totalRamBytes = mem.totalMem,
                memoryClassMb = am.memoryClass,
                largeMemoryClassMb = am.largeMemoryClass,
                isLowRamDevice = am.isLowRamDevice,
                glesVersion = pm.systemFeatureInfo(PackageManager.FEATURE_OPENGLES_VERSION)?.let { "0x%08x".format(it.version) },
                vulkanSupported = pm.hasSystemFeature(PackageManager.FEATURE_VULKAN_HARDWARE_VERSION),
                openGlEsSupported = pm.hasSystemFeature(PackageManager.FEATURE_OPENGLES_3_1) || pm.hasSystemFeature(PackageManager.FEATURE_OPENGLES_3_2),
                hardwareDecoders = codecs,
                displayWidthPx = display.widthPixels,
                displayHeightPx = display.heightPixels,
                densityDpi = display.densityDpi,
            )
        }
    }
}

// Anti-patterns:
//  - if (Build.MODEL == "GM1901") { ... }  — never gate on model strings
//  - -march=native / hard-coded CPU instructions
//  - using capabilities to disable security (sandboxing, HTTPS, site isolation)
//  - guessing codec support instead of reading MediaCodecList
