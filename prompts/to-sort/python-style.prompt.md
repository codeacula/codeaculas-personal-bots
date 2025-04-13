```plaintext
When working in Python projects:

- **Formatting & Linting:**
  - Use `black` with a line length of 120 characters (do not enforce 80).
  - Use `isort` for import sorting and `flake8` for linting.
- **Type Safety:**
  - Use type hints where appropriate and validate them with `mypy`.
- **Testing:**
  - Write tests using `pytest`, with fixtures and mocks when necessary.
- **Structure:**
  - Organize code using a `src/` and `tests/` layout.
  - Keep modules and functions focused and purposeful.
- **Exceptions:**
  - Catch specific exceptions, avoid `except Exception`.
- **Code Style:**
  - Prefer clarity and explicitness over cleverness.
  - Use data-centric and functional patterns when applicable.
```