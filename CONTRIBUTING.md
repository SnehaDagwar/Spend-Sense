# Contributing to Spend Sense

Thank you for your interest in contributing to Spend Sense. This document describes the process for reporting issues, proposing features, and submitting code changes. Following these guidelines helps maintain a consistent and high-quality codebase and makes the review process smooth for everyone involved.

## Code of Conduct

By participating in this project you agree to treat all contributors with respect, engage constructively in discussions, and focus feedback on ideas and code rather than individuals. Contributions that involve harassment, discrimination, or deliberately hostile behavior will not be accepted.

## How to Report a Bug

Before opening a new issue, search the existing issues to see if the problem has already been reported. If you find an existing report that matches your situation, add a comment with any additional details you have rather than opening a duplicate.

When filing a new bug report, include the following information:

- A clear and specific title that summarizes the problem
- Steps to reproduce the issue, described precisely enough that another person can follow them and observe the same behavior
- The expected result and the actual result
- The browser and version you are using
- Screenshots or screen recordings if the problem is visual

Bug reports that do not include enough information to reproduce the issue may be closed without resolution.

## How to Suggest a Feature

Feature requests should be filed as GitHub issues. Before submitting one, consider whether the feature fits the core purpose of the application, which is to help individuals understand and manage their personal spending without requiring a backend server or user accounts.

In your feature request, describe the problem you are trying to solve rather than jumping immediately to a proposed solution. Explain who would benefit from the feature and how often the scenario arises. If you already have a specific implementation approach in mind, you are welcome to describe it, but the problem statement is the more important part.

## Development Setup

Fork the repository and clone your fork locally.

```bash
git clone https://github.com/<your-username>/Spend-Sense.git
cd Spend-Sense
npm install
npm run dev
```

The application will start at `http://localhost:5173` or the next available port.

## Branching Strategy

Create a new branch for every change you want to propose. Branch names should follow the convention below.

- `feat/short-description` for new features
- `fix/short-description` for bug fixes
- `refactor/short-description` for code improvements that do not change behavior
- `docs/short-description` for documentation changes
- `chore/short-description` for build system, dependency, or tooling changes

Never commit directly to the `main` branch.

## Commit Messages

This project follows the Conventional Commits specification. Each commit message should have a short summary line in the format below, optionally followed by a blank line and a longer description.

```
type(scope): short imperative summary

Optional longer description explaining why the change was made,
what problem it solves, and any relevant context for reviewers.
```

Valid types are `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, and `style`. The scope should be the name of the module or feature area being modified, such as `dashboard`, `budget`, `insights`, or `tracker`.

Commit messages should be written in the present tense. For example, write "add category goals panel" rather than "added category goals panel".

## Code Style

This project uses ESLint and TypeScript in strict mode. Run the linter before submitting a pull request.

```bash
npm run lint
```

Additional conventions to follow:

- Use named exports rather than default exports for all components and utilities, except for top-level page components which may use default exports to align with the routing convention.
- Avoid the `any` type. Use specific types or `unknown` when the type is genuinely uncertain.
- Do not leave commented-out code in production files. Remove dead code rather than commenting it out.
- Keep functions small and focused. If a function does more than one thing, consider splitting it.
- Extract shared logic into custom hooks or utility functions rather than duplicating it across components.
- All user-visible text should be plain and direct. Avoid jargon or overly technical language in the UI.

## Submitting a Pull Request

When your changes are ready, push your branch to your fork and open a pull request against the `main` branch of the original repository.

Your pull request description should explain what the change does, why it is needed, and how you tested it. Include screenshots for any visual changes. If your pull request closes an open issue, reference it using the syntax `Closes #123` so the issue is automatically linked.

All pull requests must pass the existing tests before they will be reviewed. If you are adding a new feature, include tests that cover the new behavior. If you are fixing a bug, include a test that would have caught the bug before the fix.

Keep pull requests focused. A pull request that changes one thing is much easier to review than one that changes many unrelated things. If you have several independent improvements, open separate pull requests for each one.

## Running Tests

```bash
npm test
```

Tests are written using Vitest and React Testing Library. Test files are located in the `src/test` directory and alongside the source files they test.

## Questions

If you have a question about the codebase or the contribution process that is not answered by this document, open a GitHub Discussion rather than an issue. Issues are reserved for concrete bugs and actionable feature requests.
