# Contributing to HIreAI Agent

Thank you for choosing to contribute to the HIreAI Resume Screening Agent repository! We welcome help in refactoring parsers, adding metrics checks, or refining our React UI.

## Getting Started

1. Fork this repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/HIreAI_Test.git
   cd HIreAI_Test
   ```
3. Set up the Python virtual environment and node dependencies (cross-platform):

  Windows (PowerShell):
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt

  cd frontend
  npm install
  ```

  macOS / Linux (bash):
  ```bash
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt

  cd frontend
  npm install
  ```

## Development Guidelines

- **Code Quality**: All Python code must be formatted and pass Ruff and MyPy checks:
  ```bash
  ruff check .
  mypy app main.py
  ```
- **Pre-commit Hooks**: We use pre-commit to check trailing spaces, EOF markers, and formatting. Enable hooks using:
  ```bash
  pre-commit install
  ```
- **Unit Testing**:
  - Run backend pytests: `pytest tests/`
  - Run frontend Vitest tests: `npm run test` inside `frontend/`

## Making a Pull Request

1. Create a descriptive branch (e.g. `feature/spacy-optimizations`).
2. Implement your changes and write companion tests.
3. Commit your changes and push them to your fork.
4. Open a Pull Request against the main branch of this repository. Ensure your PR description lists what changed and references any open issues.
