
When working in a C# project, follow these guidelines:

- **Build and Test:** Use `dotnet build` and `dotnet test` directly, not IDE-specific tasks or buttons.
- **Programming Style:**
  - Favor data-driven design over heavy object-oriented patterns.
  - Prefer immutability and functional programming techniques where practical.
  - Use expression-bodied members, pattern matching, records, and other modern C# features.
- **Code Structure:**
  - Organize code by domain and responsibility, not by type or layer.
  - Minimize deep inheritance chains—prefer composition and modules.
- **Language Features:** Use the latest stable language features available in the .NET SDK target (e.g., nullable reference types, top-level statements, switch expressions).
- **Testing:** Write focused unit tests using xUnit, NUnit, or MSTest. Use fluent assertions where possible.
