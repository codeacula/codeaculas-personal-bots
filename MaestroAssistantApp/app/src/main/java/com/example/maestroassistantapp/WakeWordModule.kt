package com.example.maestroassistantapp.di // Place in a 'di' package

import android.content.Context
import com.example.maestroassistantapp.feature.wakeword.WakeWordRecognizer
import com.example.maestroassistantapp.feature.wakeword.WakeWordRecognizerImpl
import com.google.android.datatransport.runtime.dagger.Provides
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent // Use SingletonComponent for app-wide instance
// Or use ServiceComponent if the recognizer is ONLY ever used by the WakeWordService
// import dagger.hilt.android.components.ServiceComponent
// import dagger.hilt.android.scopes.ServiceScoped
import javax.inject.Singleton

/**
 * Hilt Module for providing dependencies related to the Wake Word feature.
 */
@Module
// InstallIn determines the scope and lifetime of the provided dependencies.
// SingletonComponent means the WakeWordRecognizer instance will live as long as the application.
@InstallIn(SingletonComponent::class)
// If using ServiceComponent:
// @InstallIn(ServiceComponent::class)
object WakeWordModule {

    /**
     * Provides an instance of [WakeWordRecognizer].
     *
     * TODO: Update this provider to initialize and return the actual Vosk or Porcupine
     * implementation of [WakeWordRecognizer]. This might involve:
     * - Injecting API keys or model paths (potentially from BuildConfig or another source).
     * - Handling initialization errors gracefully.
     *
     * @param context The application context.
     * @return An implementation of [WakeWordRecognizer].
     */
    @Provides
    @Singleton // Corresponds to SingletonComponent
    // If using ServiceComponent:
    // @ServiceScoped
    fun provideWakeWordRecognizer(@ApplicationContext context: Context): WakeWordRecognizer {
        // For now, provides the placeholder implementation.
        // Replace with your actual recognizer setup.
        return WakeWordRecognizerImpl(context)

        // Example for Porcupine (conceptual):
        // val accessKey = "YOUR_PICOVOICE_ACCESS_KEY" // TODO: Inject this securely
        // return PorcupineWakeWordRecognizer(context, accessKey) // Assuming you create this wrapper

        // Example for Vosk (conceptual):
        // val modelPath = "path/to/model" // TODO: Inject or determine path
        // return VoskWakeWordRecognizer(context, modelPath) // Assuming you create this wrapper
    }
}
