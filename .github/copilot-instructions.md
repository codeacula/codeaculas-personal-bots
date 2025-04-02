# GitHub Copilot Prompts for Python Projects

## Python Best Practices

- Create a clean Python project structure with standard directories (e.g., src, tests, docs, scripts)
- Set up a Python virtual environment and a clear, minimal `requirements.txt`
- Organize your code logically into modules and packages, ensuring each has a clear responsibility and minimal interdependencies.
- Implement structured logging using Python's built-in logging module with levels, timestamps, and rotating log files
- Write unit tests using pytest following test-driven development (TDD) practices
- Apply consistent code formatting
- Clearly handle exceptions and errors, providing meaningful error messages and avoiding broad exception clauses
- Document code with clear docstrings and comments following PEP 257 conventions
- Remove unused imports and variables, and ensure no dead code remains in the repository
- Use type hints and static type checking with mypy to improve code readability and maintainability
- Leave comments in the code to explain complex logic or algorithms, but avoid over-commenting simple or self-explanatory code
- Ensure the code builds correctly when done, and that all tests pass before committing changes

## AI-Specific Practices

- Clearly separate model loading, inference, and utility functions, using descriptive function and variable names
- Responsibly manage GPU resources by implementing checks before resource-intensive operations
- Provide clear, modular, and asynchronous (when appropriate) FastAPI endpoints for AI model inference
