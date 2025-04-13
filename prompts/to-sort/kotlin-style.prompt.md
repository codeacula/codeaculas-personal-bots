```plaintext
When working in Kotlin/Android projects:

- **Architecture:**
  - Use Jetpack Compose for UI when applicable.
  - Maintain separation of concerns via ViewModels and clean architecture principles.
  - Use sealed classes or enums to represent UI and business state.

- **Asynchronous Work:**
  - Use coroutines and flows instead of callbacks or blocking calls.
  - Always launch coroutines with proper scope and error handling.

- **Code Style:**
  - Use modern Kotlin features: extension functions, null safety, smart casts, scoped functions (`let`, `run`, `with`, etc.).
  - Keep functions small, focused, and ideally pure.
  - Prefer immutability and expression-based coding where practical.

- **Testing:**
  - Write unit tests for ViewModels and core logic.
  - Use JUnit, MockK, and Compose testing APIs.

- **Resource Handling:**
  - Centralize strings, colors, and dimensions in `res/values`.
  - Avoid hardcoded strings or styles in layout or Compose files.
```