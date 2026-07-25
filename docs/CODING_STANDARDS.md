# Coding Standards

> This document defines the coding standards for the AI Document Reader project.
>
> Every contributor and AI coding assistant must follow these rules.

---

# 1. General Principles

The codebase should prioritize:

- Readability over cleverness
- Maintainability over shortcuts
- Simplicity over unnecessary abstractions
- Consistency across all modules
- Production-ready quality

Follow:

- SOLID
- DRY
- KISS
- Separation of Concerns

---

# 2. Python Version

Use:

Python 3.13+

Do not use deprecated Python features.

---

# 3. Package Management

Use:

uv

Never use:

- pip install
- requirements.txt

Dependencies are managed only through:

pyproject.toml

---

# 4. Async Programming

Use async for all:

- Routers
- Services
- Repositories
- Database operations
- HTTP requests

Avoid blocking operations inside async code.

Never use time.sleep().

Use:

await asyncio.sleep()

when appropriate.

---

# 5. Type Hints

Every function must include type hints.

Example:

def get_user(user_id: str) -> UserResponse:

Avoid using Any unless absolutely necessary.

---

# 6. Naming Conventions

## Variables

snake_case

Example

user_id

document_name

invoice_number

---

## Functions

snake_case

Example

create_document()

verify_otp()

generate_summary()

---

## Classes

PascalCase

Example

DocumentService

UserRepository

HealthRouter

---

## Constants

UPPER_CASE

Example

MAX_FILE_SIZE

JWT_EXPIRATION_MINUTES

---

## Private Members

Prefix with underscore.

Example

_load_keys()

---

# 7. Imports

Import order:

1. Standard Library

2. Third-party Packages

3. Local Imports

Example

import asyncio

from fastapi import APIRouter

from app.core.config import settings

Never use wildcard imports.

---

# 8. Docstrings

Public classes and functions should include Google-style docstrings.

Example

"""
Create a new document.

Args:
    user_id: Owner of the document.
    request: Document creation payload.

Returns:
    Created document.
"""

---

# 9. Comments

Write comments only when they explain "why."

Do not explain obvious code.

Good

# Retry because external API occasionally times out.

Bad

# Increment i

---

# 10. FastAPI Rules

Routers must only:

- Receive request
- Validate request
- Call service
- Return response

Never:

- Query MongoDB
- Contain business logic
- Contain AI logic

---

# 11. Service Rules

Services contain:

Business logic

Validation

Transactions

Workflow

External integrations

Services must never return raw database models.

---

# 12. Repository Rules

Repositories:

Read database

Write database

Delete data

Update data

Nothing else.

Repositories should not:

Validate business rules

Send emails

Call AI

Generate JWT

---

# 13. MongoDB Rules

Use:

AsyncMongoClient

Never use Motor.

Prefer references over deeply nested documents.

Create indexes for:

Email

Phone

Document owner

Created date

Status

---

# 14. API Design

Base URL

/api/v1

Plural resource names.

Examples

/users

/documents

/notifications

Use nouns instead of verbs.

---

# 15. Response Format

Every endpoint returns:

Success

{
    "success": true,
    "message": "",
    "data": {}
}

Failure

{
    "success": false,
    "message": "",
    "errors": []
}

Never return inconsistent response structures.

---

# 16. Exception Handling

Create custom exceptions.

Never expose stack traces.

Log every unexpected exception.

Return meaningful messages.

---

# 17. Logging

Never use print().

Use logger.

Log:

Application startup

Shutdown

Authentication

Warnings

Errors

External API failures

Database failures

---

# 18. Security

Hash passwords.

Never store plain passwords.

Validate JWT.

Use RS256.

Never expose secrets.

Never commit:

.env

private.pem

---

# 19. File Upload Rules

Validate:

Extension

Content-Type

Maximum size

Scan filenames.

Generate unique filenames.

Never trust client filenames.

---

# 20. AI Integration

AI providers must be abstracted.

Never call Gemini directly from routers.

Use:

AIService

↓

GeminiProvider

Future providers:

OpenAI

Claude

Ollama

should require minimal changes.

---

# 21. Dependency Injection

Avoid global objects.

Inject:

Database

Settings

Services

Repositories

---

# 22. Configuration

Never use:

os.getenv()

inside application code.

Always use:

settings

from app.core.config.

---

# 23. Testing

Every feature should have:

Unit tests

Integration tests

API tests

Tests must not depend on production data.

---

# 24. Docker

Application must run using:

docker compose up

No machine-specific configuration.

---

# 25. Git

Branch naming:

feature/authentication

feature/documents

fix/login

refactor/database

Commit messages:

feat:

fix:

docs:

test:

refactor:

ci:

build:

Examples

feat(auth): implement JWT authentication

fix(upload): validate file extension

docs(api): update authentication endpoints

---

# 26. Folder Structure

Feature-based architecture only.

Every module should contain:

router.py

service.py

repository.py

schemas.py

model.py

exceptions.py

Dependencies should point inward.

No circular imports.

---

# 27. Code Review Checklist

Before merging code verify:

✓ Type hints

✓ Async correctness

✓ Error handling

✓ Logging

✓ Tests

✓ Naming

✓ Architecture

✓ Security

✓ Documentation

✓ Response format

---

# 28. Rules for AI Coding Assistants

If you are an AI assistant:

- Read AI_CONTEXT.md first.
- Follow these coding standards strictly.
- Do not invent new architecture.
- Keep routers thin.
- Keep services responsible for business logic.
- Keep repositories responsible for persistence only.
- Generate production-ready code.
- Prefer maintainability over brevity.
- If unsure, ask for clarification rather than changing established patterns.