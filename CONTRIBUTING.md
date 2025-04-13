# Contributing to Codeacula's Personal Bots

Hey friend—thanks for considering a contribution. Whether you're fixing bugs, improving docs, building new tools, or just dropping by with ideas, you're welcome here.

## 💡 How to Get Started

1. **Read the README** – Understand the purpose of the repo and what each folder does.
2. **Join the Community** – Come say hi on [Twitch](https://twitch.tv/codeacula) or [Discord](https://discord.gg/jjA2svbKxZ).
3. **Find a Good First Task** – Look for issues labeled `good first issue` or `help wanted`, or check the project board.

## 🛠 Local Setup

### For Python projects (e.g., `transcribe_meeting`)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r src/requirements.txt
```

### For C# projects (e.g., `Maestro`)

```bash
dotnet restore
```

### For Android projects (e.g., `MaestroAssistantApp`)

Open with **Android Studio** and sync Gradle. Make sure to enable Kotlin and Jetpack Compose support.

## 🧪 Running Tests

- Python: `pytest`
- C#: `dotnet test`
- Android: Use Android Studio’s built-in test runner

## 🧾 Making a Contribution

1. **Fork the repo** and create a new branch (`feature/your-feature-name`)
2. **Write clear, focused commits** – keep them small and readable
3. **Write or update tests** as needed
4. **Submit a pull request** – Fill out the PR template when you open it

## 💬 Commit Guidelines

Use meaningful commit messages:

```plaintext
fix(transcription): handle blank audio edge case
feat(maestro): add websocket ping handling
chore: update VS Code settings
```

## 🧭 Contributor Principles

- Ask questions – no judgment.
- Code with empathy – imagine the next person who reads your work is tired or new.
- Keep it accessible – document things clearly, use inclusive language.
- Respect people’s time – PRs should include enough context to review without guessing.

## 💖 Our Values

We prioritize safety, kindness, and equity. All contributors are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

If you're not sure where to start or just want to jam on an idea, hit me up on stream or Discord. Let’s build something rad together.

– **Codeacula**
