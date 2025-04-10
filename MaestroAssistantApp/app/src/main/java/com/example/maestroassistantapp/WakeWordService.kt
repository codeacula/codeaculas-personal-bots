package com.example.maestroassistantapp.service // Place in a 'service' package

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo // Required for foregroundServiceType
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat // For stopForeground with behavior flags
import com.example.maestroassistantapp.MainActivity // Assuming your main activity
import com.example.maestroassistantapp.R // Assuming you have R file
import com.example.maestroassistantapp.feature.wakeword.WakeWordListener
import com.example.maestroassistantapp.feature.wakeword.WakeWordRecognizer
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject
import java.lang.Exception

/**
 * A Foreground Service responsible for running the WakeWordRecognizer in the background.
 */
@AndroidEntryPoint // Use Hilt for DI
class WakeWordService : Service(), WakeWordListener {

    // Inject the recognizer (Hilt will provide WakeWordRecognizerImpl if bound in a Module)
    @Inject
    lateinit var wakeWordRecognizer: WakeWordRecognizer

    private var isServiceRunning = false

    companion object {
        const val ACTION_START_LISTENING = "com.example.maestroassistantapp.ACTION_START_LISTENING"
        const val ACTION_STOP_LISTENING = "com.example.maestroassistantapp.ACTION_STOP_LISTENING"
        private const val NOTIFICATION_CHANNEL_ID = "WakeWordServiceChannel"
        private const val NOTIFICATION_ID = 1 // Must be > 0
        private const val TAG = "WakeWordService"
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Service onCreate")
        createNotificationChannel()
        // Set the listener for the recognizer. Crucial to receive callbacks.
        wakeWordRecognizer.setListener(this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action
        Log.d(TAG, "Service onStartCommand, Action: $action")

        when (action) {
            ACTION_START_LISTENING -> startListeningWithForeground()
            ACTION_STOP_LISTENING -> stopServiceInternal()
            else -> {
                Log.w(TAG, "Unknown or null action received: $action. Stopping service.")
                stopServiceInternal() // Stop if action is invalid
                return START_NOT_STICKY // Don't restart for invalid actions
            }
        }
        // START_STICKY: If the service is killed, the system will try to restart it,
        // calling onStartCommand again with a null intent. Handle null intent action.
        // Consider START_REDELIVER_INTENT if you need the last intent to be redelivered.
        return START_STICKY
    }

    private fun startListeningWithForeground() {
        if (isServiceRunning) {
            Log.d(TAG, "Service already running.")
            return
        }
        Log.d(TAG, "Attempting to start foreground service and listening...")

        // --- Permission Check ---
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED) {
            Log.e(TAG, "RECORD_AUDIO permission missing. Cannot start listening. Stopping service.")
            // TODO: Notify user or handle appropriately (e.g., send broadcast to UI)
            stopServiceInternal()
            return
        }

        // --- Start Foreground ---
        try {
            val notification = getForegroundNotification()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                // Specify foreground service type for Android 10+
                // This needs to match a type declared in the manifest's <service> tag.
                ServiceCompat.startForeground(this, NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
            } else {
                startForeground(NOTIFICATION_ID, notification)
            }
            isServiceRunning = true
            Log.d(TAG, "Service started in foreground.")

            // --- Start Recognizer ---
            // Start the actual wake word recognition process
            wakeWordRecognizer.startListening() // This might throw if init failed earlier

        } catch (e: Exception) {
            Log.e(TAG, "Error starting foreground service or wake word recognizer", e)
            onError(e) // Handle error (e.g., stop service)
        }
    }

    private fun stopServiceInternal() {
        Log.d(TAG, "Stopping foreground service...")
        if (!isServiceRunning) {
            Log.d(TAG, "Service not running, nothing to stop.")
            // Ensure stopSelf is called even if not "running" to handle edge cases
            stopSelf()
            return
        }

        isServiceRunning = false
        try {
            // Stop the recognizer first
            wakeWordRecognizer.stopListening()
            // Release recognizer resources
            wakeWordRecognizer.release()
            Log.d(TAG,"Recognizer stopped and released.")
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping/releasing recognizer", e)
            // Continue stopping the service anyway
        } finally {
            // Stop foreground state and remove notification
            ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE)
            Log.d(TAG,"Foreground state stopped.")
            // Stop the service instance
            stopSelf()
            Log.d(TAG,"stopSelf() called.")
        }
    }

    override fun onDestroy() {
        Log.d(TAG, "Service onDestroy")
        // Clean up resources if the service is destroyed unexpectedly
        // (e.g., by the system). Avoid calling stopServiceInternal() directly
        // as it might have already been called or could cause issues if called
        // during system-initiated destruction. Just release the recognizer if needed.
        if (isServiceRunning) { // Check flag just in case
            try {
                wakeWordRecognizer.stopListening() // Attempt graceful stop
                wakeWordRecognizer.release()
                Log.w(TAG, "Recognizer released in onDestroy (service might have been killed).")
            } catch (e: Exception) {
                Log.e(TAG, "Error releasing recognizer in onDestroy", e)
            }
        }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? {
        // Return null for non-bindable services (started services).
        return null
    }

    // --- WakeWordListener Callbacks Implementation ---

    override fun onWakeWordDetected() {
        Log.i(TAG, "*** Wake Word 'Maestro' Detected! ***")

        // --- Action on Detection ---
        // TODO: Implement the desired action when the wake word is detected.
        // Examples:
        // 1. Bring MainActivity to the foreground:
        val intent = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            // Add extra data if needed to inform the Activity it was opened by wake word
            putExtra("SOURCE", "WakeWordService")
        }
        startActivity(intent)

        // 2. Send a broadcast:
        // Intent broadcastIntent = new Intent("com.example.maestroassistantapp.WAKE_WORD_DETECTED");
        // sendBroadcast(broadcastIntent);

        // 3. Start another service (e.g., for full voice command processing):
        // Intent commandServiceIntent = new Intent(this, CommandProcessingService.class);
        // startService(commandServiceIntent);

        // --- Post-Detection Behavior ---
        // Decide whether to stop listening or continue.
        // Option A: Stop the service after detection
        // stopServiceInternal()

        // Option B: Continue listening (do nothing here)
    }

    override fun onError(error: Exception) {
        Log.e(TAG, "Wake word recognizer error: ${error.message}", error)
        // --- Error Handling Strategy ---
        // TODO: Implement a robust error handling strategy.
        // Example: Log the error and stop the service.
        // Could also attempt to restart after a delay, log to analytics, notify user, etc.
        stopServiceInternal()
    }

    // --- Notification Helper ---

    // Make internal for testing access if needed, otherwise private.
    internal fun getForegroundNotification(): Notification {
        val notificationIntent = Intent(this, MainActivity::class.java) // Intent to open on tap
        val pendingIntentFlags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        } else {
            PendingIntent.FLAG_UPDATE_CURRENT
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent, pendingIntentFlags
        )

        // TODO: Replace with your actual app icon
        val icon = R.drawable.ic_launcher_foreground

        return NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle(getString(R.string.app_name)) // Use string resource
            .setContentText("Listening for wake word...") // TODO: Use string resource
            .setSmallIcon(icon)
            .setContentIntent(pendingIntent) // Action on tap
            .setOngoing(true) // Make it non-dismissible while service is foreground
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setPriority(NotificationCompat.PRIORITY_LOW) // Low priority for background task
            // .setVisibility(NotificationCompat.VISIBILITY_SECRET) // Hide sensitive content on lock screen
            .build()
    }

    private fun createNotificationChannel() {
        // Create the NotificationChannel, but only on API 26+ because
        // the NotificationChannel class is new and not in the support library
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "Maestro Background Service" // TODO: Use string resource
            val descriptionText = "Notification channel for the background wake word listener." // TODO: Use string resource
            val importance = NotificationManager.IMPORTANCE_LOW // Low importance = no sound/vibration
            val channel = NotificationChannel(NOTIFICATION_CHANNEL_ID, name, importance).apply {
                description = descriptionText
                // Configure other channel properties if needed (e.g., disable vibration)
                enableVibration(false)
                setSound(null, null)
            }
            // Register the channel with the system
            val notificationManager: NotificationManager =
                getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
            Log.d(TAG, "Notification channel created.")
        }
    }
}
