# Contributing to ReviewPilot

Thanks for taking the time to contribute. Bug reports, documentation
improvements, and focused code changes are welcome.

## Before you start

- Check existing issues and pull requests to see whether the work is already
  being discussed.
- For a substantial change, open an issue first so the approach can be
  discussed before implementation.
- Keep each contribution focused; avoid unrelated formatting or refactoring.

## Local setup

Follow the [README setup instructions](./README.md#getting-started). For local
development, use `USE_CELERY=false` to run reviews directly without Redis. You
will still need PostgreSQL, GitHub credentials, and a Groq chat-completions
model configured in `backend/.env`.

Never include API keys, passwords, `.env` files, or private pull-request
content in commits, issues, or screenshots.

## Make and verify changes

- Follow existing Python, React, and CSS patterns.
- Add or update tests when behavior changes.
- Run the frontend tests and production build:

  ```powershell
  cd frontend
  npm test -- --watchAll=false --runInBand
  npm run build
  ```

- Check backend Python syntax:

  ```powershell
  cd backend
  python -m compileall -q app
  ```

- In your pull request, list the checks you ran and explain any checks you
  could not run.

## Pull requests

- Use a clear title and describe the problem and solution in plain language.
- Include screenshots for visible UI changes when helpful.
- Call out configuration changes and document new environment variables.
- Confirm that credentials, local settings, generated files, and unrelated
  changes are not included.

By participating, you agree to follow the [Code of Conduct](./CODE_OF_CONDUCT.md).
