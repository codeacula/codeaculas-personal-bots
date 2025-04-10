package com.example.maestroassistantapp.feature.wakeword

import java.lang.Exception

// --- Listener Interface ---
/**
 * Interface for receiving callbacks from the WakeWordRecognizer.
 */
interface WakeWordListener {
    /** Called when the configured wake word is detected. */
    fun onWakeWordDetected()

    /** Called when an error occurs during recognition or initialization. */
    fun onError(error: Exception)

    // Add other callbacks if needed (e.g., onTimeout, onPartialResult, onStateChange)
}

// --- Recognizer Interface ---
/**
 * Defines the contract for a wake word recognition component.
 * This abstracts the specific implementation (Vosk, Porcupine, etc.).
 */
interface WakeWordRecognizer {
    /**
     * Sets the listener to receive wake word events.
     * @param listener The listener instance.
     */
    fun setListener(listener: WakeWordListener)

    /**
     * Starts the wake word listening process.
     * Requires RECORD_AUDIO permission.
     * May throw exceptions if initialization failed or permissions are missing.
     */
    fun startListening()

    /**
     * Stops the wake word listening process.
     */
    fun stopListening()

    /**
     * Releases any resources held by the recognizer (models, audio recorder, etc.).
     * Should be called when the recognizer is no longer needed.
     */
    fun release()

    // --- Internal methods for testing simulation (optional) ---
    // These are generally not part of the public interface but can be useful
    // for triggering events in tests without relying on complex SDK mocking.
    // Consider using a separate test-specific interface or implementation if needed.

    /** Simulates a wake word detection event for testing purposes. */
    fun simulateWakeWordDetection() {}

    /** Simulates an initialization error event for testing purposes. */
    fun simulateInitializationError(e: Exception) {}
}
