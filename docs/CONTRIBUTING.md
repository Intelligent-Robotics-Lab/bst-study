# Contributing Guide

## Outline

1. [Core Principles](#core-principles)
2. [Branch Naming](#branch-naming)
3. [Development Workflow](#development-workflow)
4. [Commit Changes](#commit-changes)
5. [Push Changes](#push-changes)
6. [Common Recovery Commands](#common-recovery-commands)

Thank you for contributing to the BST Study Interaction Framework.

This project follows a simple Git workflow based on short-lived feature branches, focused pull requests, and modular development practices. The goal is to keep the codebase maintainable, testable, and easy for future researchers to understand.

---

# Core Principles

* Keep `main` stable and deployable.
* NEVER develop or commit directly on `main`.
* Keep changes small and focused.
* Open a pull request for all code changes.
* Follow the existing project architecture.
* Prefer readability over complexity.
* Delete feature branches after merging.

---

# Branch Naming

Create a dedicated branch for each feature, bug fix, or documentation update.

Format:

```text
<scope>/<type>/<short-description>
```

## Scopes

| Scope      | Description                          |
| ---------- | ------------------------------------ |
| logic      | Interaction flow and study logic     |
| perception | ASR, gesture, and emotion processing |
| agent      | Robot-specific execution layers      |
| expression | Behavior packet generation           |
| data       | Study content and JSON files         |
| docs       | Documentation                        |
| test       | Testing and validation               |

## Types

| Type    | Description                |
| ------- | -------------------------- |
| feature | New functionality          |
| fix     | Bug fixes                  |
| chore   | Refactoring or maintenance |
| docs    | Documentation-only changes |

## Examples

```text
logic/feature/navigation-system
perception/fix/asr-timeout
agent/feature/led-control
docs/chore/readme-update
```

---

# Development Workflow

## Create a Branch

```bash
git checkout main
git pull origin main
git checkout -b logic/feature/my-feature
```

 > **Important:** Do not make development changes directly on `main`. Always create a new branch before modifying code, documentation, study content, or configuration files.

## Check Status and Review Changes

Before committing or pushing, verify your current branch and review pending changes.

Check your branch and file status:

```bash
git status
```

Review unstaged code changes:

```bash
git diff
```

Review staged changes:

```bash
git diff --staged
```

> Tip: Always confirm you are working on the correct feature branch and not on main.

## Commit Changes

```bash
git add .
git commit -m "feat(logic): add navigation handling"
```

## Push Changes

The first time a branch is pushed, set the upstream tracking branch:

```bash
git push --set-upstream origin logic/feature/my-feature
```

or equivalently:

```bash
git push -u origin logic/feature/my-feature
```

After the initial push, future pushes can be performed with:

```bash
git push
```

## Common Recovery Commands

If you need to recover from a mistake, the following commands may be useful.

> **Note:** these commands are not exhaustive and other resources may be necessary for understanding.

Discard local changes to a specific file:

```bash
git restore <file>
```

Discard all uncommitted changes:

```bash
git restore .
```

Undo the most recent commit while keeping the changes locally:

```bash
git reset --soft HEAD~1
```

Reset your branch to match the latest version of main:

```bash
git fetch origin
git reset --hard origin/main
```

> **Warning:** git reset --hard permanently removes uncommitted local changes. Use it carefully.

## Open a Pull Request

Pull requests should include:

* Summary of changes
* Reason for the change
* Testing performed
* Screenshots or logs (if applicable)

## After Merge

Once your pull request has been merged into `main`, delete the feature branch to keep the repository organized.

Delete the local branch:

```bash
git branch -d logic/feature/my-feature
```

Delete the corresponding remote branch on GitHub:

```bash
git push origin --delete logic/feature/my-feature
```

> **Note:** The first command removes the branch from your local machine. The second command removes the branch from the remote repository.

Update your local copy of `main`:

```bash
git checkout main
git pull origin main
```

When starting new work, create a new branch from the updated `main` branch:

```bash
git checkout -b logic/feature/my-next-feature
```

> **Important:** Never develop directly on `main`. All features, bug fixes, documentation updates, and experiments should be completed on dedicated branches and merged through a pull request.

# Project Architecture Guidelines

Follow the existing system architecture when adding new functionality.

```text
Perception → Logic → Expression Module → Agent Layer
```

For more detailed information on this structure see: [Architecture Guide](docs/ARCHITECTURE.md)

## Logic Layer

Place interaction flow and study behavior in:

```text
logic/
```

Examples:

* Tutorial flow
* Instruction flow
* Modeling flow
* DTT logic
* Navigation handling

## Perception Layer

Place perception processing and event handling in:

```text
Perception/
```

Examples:

* Speech recognition integration
* Emotion processing
* Gesture recognition
* Event routing

## Expression Module

Place robot-independent behavior definitions in:

```text
expression_module/
```

Examples:

* Speech packets
* Gesture packets
* Facial expressions
* Attention targets

## Agent Layer

Place robot-specific execution code in:

```text
agent_layer/
```

Examples:

* Furhat API integration
* Behavior translation
* Robot execution
* Connection management

## Study Content

Keep study content data-driven through:

```text
data/
```

---

# Clean Code Reference

This project aims to follow general clean code principles to promote readability, maintainability, and long-term usability.

Contributors are encouraged to review the following reference before making substantial code changes:

https://gist.github.com/wojteklu/73c6914cc446146b8b533c0988cf8d29

The summary provides quick practical guidelines for writing code that is easy to understand, modify, and extend.

Key principles include:

* Functions should do one thing well.
* Use clear and descriptive names.
* Prefer readability over cleverness.
* Avoid duplicated logic.
* Minimize side effects.
* Keep modules focused on a single responsibility.
* Write comments to explain *why*, not *what*.
* Leave the codebase cleaner than you found it.

These principles should guide development across all project layers, including perception, logic, expression, and agent execution.

---

# Code Quality Expectations

Contributions should:

* Follow the clean code principles described above.
* Follow existing project architecture and coding patterns.
* Keep functions and classes focused on a single responsibility.
* Use descriptive names and consistent formatting.
* Avoid duplicated logic and unnecessary complexity.
* Prefer reusable solutions over hard-coded implementations.
* Remove unused code, imports, and debugging artifacts before submitting.

Code should be understandable and maintainable by future researchers and developers who may not be familiar with the original implementation.

---

# Testing

Before submitting a pull request:

* Verify the code runs successfully.
* Test affected functionality.
* Check for console errors and warnings.
* Validate robot behaviors when applicable.
* Confirm study content loads correctly.

---

# Pull Request Checklist

Before requesting review, confirm the following:

* Code builds and runs successfully
* Changes have been tested
* Documentation has been updated if needed
* No unrelated changes are included
* Project architecture has been followed
* Clean code principles have been considered

---

# Questions

If you are unsure where a change belongs, review the existing project structure and follow the architecture:

```text
Perception → Logic → Expression Module → Agent Layer
```

If you are still unsure where a change belongs, need architectural guidance, or discover a bug, please open an issue:

https://github.com/Intelligent-Robotics-Lab/bst-study/issues