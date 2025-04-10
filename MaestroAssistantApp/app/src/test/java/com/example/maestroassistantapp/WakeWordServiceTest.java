package com.example.maestroassistantapp

import android.content.Context
import android.content.Intent
import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import androidx.test.core.app.ApplicationProvider
import com.example.maestroassistantapp.MainActivity
import com.example.maestroassistantapp.service.WakeWordService // Adjust package if needed
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.DisplayName
import org.junit.runner.RunWith
import org.mockito.kotlin.*
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.shadows.ShadowApplication

// --- WakeWordServiceTest ---
@ExperimentalCoroutinesApi
@RunWith(RobolectricTestRunner::class) // Use Robolectric for Service testing
class WakeWordServiceTest {

    // Rule for JUnit to automatically handle LiveData/background tasks
    @get:Rule
    val instantExecutorRule = InstantTaskExecutorRule()

    // Coroutine test rule
    private val testDispatcher = UnconfinedTestDispatcher() // Or StandardTestDispatcher
    private val testScope = TestScope(testDispatcher)

    private lateinit var serviceController: Robolectric.ServiceController<WakeWordService>
    private lateinit var service: WakeWordService
    private lateinit var shadowApplication: ShadowApplication

    // Mock the recognizer dependency
    private val mockRecognizer: WakeWordRecognizer = mock()

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher) // Set main dispatcher for testing
        shadowApplication = shadowOf(ApplicationProvider.getApplicationContext())

        // TODO: If using Hilt, setup Hilt testing rules here
        // (@HiltAndroidTest, @InjectMocks, HiltAndroidRule etc.)

        // Create the service instance for testing
        serviceController = Robolectric.buildService(WakeWordService::class.java)
        service = serviceController.create().get()

        // TODO: Manually inject mock or use Hilt test injection
        // This demonstrates manual injection for a test without Hilt setup.
        // With Hilt testing, you'd typically provide the mock via a @BindValue or test module.
        service.wakeWordRecognizer = mockRecognizer
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain() // Reset main dispatcher
        serviceController.destroy()
    }

    @Test
    @DisplayName("testServiceStartsAndRunsAsForeground")
    fun testServiceStartsAndRunsAsForeground() {
        // Arrange
        val startIntent = Intent(ApplicationProvider.getApplicationContext(), WakeWordService::class.java)
        startIntent.action = WakeWordService.ACTION_START_LISTENING

        // Act
        // Simulate service start via onStartCommand or startService
        serviceController.startCommand(0, 0) // Using startCommand directly is common in Robolectric tests

        // Assert
        assertNotNull(service.getForegroundNotification(), "Foreground notification should be created")
        assertTrue(shadowApplication.isForegroundService, "Service should be running in foreground")
        verify(mockRecognizer).startListening() // Verify recognizer interaction
    }

    @Test
    @DisplayName("testServiceStopsCorrectly")
    fun testServiceStopsCorrectly() {
        // Arrange
        val stopIntent = Intent(ApplicationProvider.getApplicationContext(), WakeWordService::class.java)
        stopIntent.action = WakeWordService.ACTION_STOP_LISTENING
        serviceController.startCommand(0, 0) // Start it first to ensure it's running

        // Act
        service.onStartCommand(stopIntent, 0, 1) // Send stop intent to the running service instance

        // Assert
        verify(mockRecognizer).stopListening()
        verify(mockRecognizer).release() // Ensure resources are released on stop
        // Robolectric might automatically call onDestroy after stopSelf, or you might need serviceController.destroy()
        // You could add a flag in onDestroy and check it: assertTrue(service.isDestroyed)
        assertFalse(shadowApplication.isForegroundService, "Service should not be in foreground after stop")
    }

    @Test
    @DisplayName("whenWakeWordDetected_shouldTriggerAction (e.g., Start Activity)")
    fun whenWakeWordDetected_shouldTriggerAction() {
        // Arrange
        serviceController.startCommand(0, 0) // Start the service
        val listenerCaptor = argumentCaptor<WakeWordListener>()
        // Verify setListener was called during service init and capture the listener
        verify(mockRecognizer).setListener(listenerCaptor.capture())
        val capturedListener = listenerCaptor.firstValue

        // Act
        capturedListener.onWakeWordDetected() // Simulate detection by invoking the listener callback

        // Assert
        // Verify the action taken - e.g., starting an activity
        val expectedIntent = Intent(service, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            // If you add extras, check them too:
            // putExtra("WAKE_WORD_TRIGGERED", true)
        }
        val actualIntent = shadowApplication.nextStartedActivity // Get the intent used to start an activity

        assertNotNull(actualIntent, "An Activity should have been started")
        assertEquals(expectedIntent.component, actualIntent.component, "MainActivity should have been started")
        // assertEquals(expectedIntent.getBooleanExtra("WAKE_WORD_TRIGGERED", false), actualIntent.getBooleanExtra("WAKE_WORD_TRIGGERED", false))

        // Or verify a broadcast was sent, etc.
    }

    @Test
    @DisplayName("whenRecognizerError_shouldStopServiceOrHandle")
    fun whenRecognizerError_shouldStopServiceOrHandle() {
        // Arrange
        serviceController.startCommand(0, 0) // Start the service
        val listenerCaptor = argumentCaptor<WakeWordListener>()
        verify(mockRecognizer).setListener(listenerCaptor.capture())
        val capturedListener = listenerCaptor.firstValue
        val testError = RuntimeException("Recognizer failed spectacularly")

        // Act
        capturedListener.onError(testError) // Simulate error via the listener

        // Assert
        // Verify appropriate action (e.g., logging, stopping service)
        // Based on current impl, it should stop listening, release, and stop self
        verify(mockRecognizer).stopListening()
        verify(mockRecognizer).release()
        // Check if stopSelf was called (might need ShadowService from Robolectric)
        // val shadowService = shadowOf(service)
        // assertTrue(shadowService.isStoppedBySelf)
        assertFalse(shadowApplication.isForegroundService, "Service should stop on recognizer error")
    }
}
