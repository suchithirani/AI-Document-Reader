# AI Document Reader

> Master Project Context
>
> Every AI assistant working on this repository **must read this file before generating or modifying code**.

---

# 1. Project Overview

## Project Name

AI Document Reader

## Goal

Build a production-ready AI Document Intelligence Platform capable of processing different document types using OCR and Large Language Models.

The application should provide:

- Secure authentication
- Document upload
- OCR extraction
- AI-powered information extraction
- AI summaries
- AI document chat
- Semantic search
- Background processing
- Dashboard and analytics

This project is intended to demonstrate production-level backend engineering rather than tutorial-level implementation.

---

# 2. Tech Stack

## Frontend

- React
- Vite
- Tailwind CSS
- Axios

---

## Backend

- FastAPI
- Python 3.13
- uv package manager

---

## Database

MongoDB

Driver:

PyMongo AsyncMongoClient

Do NOT use Motor.

---

## Authentication

JWT

Algorithm:

RS256

Phone authentication

OTP verification

Refresh Tokens

Password Hashing

bcrypt

---

## OCR

PaddleOCR

OpenCV preprocessing

---

## AI

Google Gemini

Future support:

- OpenAI
- Claude
- Ollama

The application must use an abstraction layer so providers can be swapped easily.

---

## Background Processing

Redis

Celery

---

## Storage

Current

Local Storage

Future

Amazon S3

---

## Vector Search

FAISS

---

## Deployment

Docker

Docker Compose

GitHub Actions

Render

Vercel

AWS (Future)

---

# 3. Architecture

Architecture Style

Feature-Based Modular Monolith

The backend is divided into feature modules.

Example

Authentication

Documents

Users

Chat

Notifications

Dashboard

Admin

Every feature contains its own router, service, repository, schemas and models.

---

# 4. Layer Responsibilities

Request

↓

Router

↓

Service

↓

Repository

↓

MongoDB

Router

- Receives requests
- Validates request
- Calls service
- Returns response

No business logic.

Service

Contains all business logic.

Repository

Responsible only for database access.

No business logic.

---

# 5. Folder Structure

backend/

app/

core/

common/

database/

modules/

auth/

documents/

users/

chat/

notifications/

dashboard/

admin/

health/

workers/

storage/

ai/

tests/

---

# 6. API Design

Base URL

/api/v1

Example

GET /api/v1/documents

POST /api/v1/auth/login

GET /api/v1/users/me

POST /api/v1/chat

Use REST conventions.

---

# 7. Database

Database

ai_document_platform

Collections

users

documents

chat_sessions

notifications

otp_verifications

refresh_tokens

audit_logs

settings

---

# 8. Coding Principles

Always write production-quality code.

Never write tutorial code.

Avoid unnecessary comments.

Prefer readable code over clever code.

Follow SOLID principles.

Follow DRY.

Follow KISS.

---

# 9. Python Rules

Python 3.13

Type hints required.

Async programming everywhere.

Never block the event loop.

Use Pydantic v2.

Use dependency injection.

---

# 10. FastAPI Rules

Use lifespan.

Do NOT use @app.on_event.

Routers stay thin.

Business logic stays inside services.

Repositories only communicate with MongoDB.

---

# 11. MongoDB Rules

Use

AsyncMongoClient

Never use Motor.

Use indexes where appropriate.

Prefer references instead of massive embedded documents.

---

# 12. Logging

Never use print().

Always use logger.

Every exception should be logged.

---

# 13. Security

Use RS256 JWT.

Private key

keys/private.pem

Public key

keys/public.pem

Never commit private.pem.

Hash passwords.

Validate every request.

Protect every endpoint.

---

# 14. Error Handling

Always raise custom exceptions.

Never return raw tracebacks.

Return consistent API responses.

---

# 15. API Response Format

Success

{
    "success": true,
    "message": "",
    "data": {}
}

Error

{
    "success": false,
    "message": "",
    "errors": []
}

---

# 16. Git Strategy

Feature branches

feature/authentication

feature/documents

feature/chat

Commit messages

feat:

fix:

docs:

refactor:

test:

ci:

build:

---

# 17. Current Phase

Phase 1

Backend Foundation

Tasks

Project initialization

Configuration

Logging

MongoDB connection

Health endpoint

Docker

GitHub

After Phase 1

Authentication

Document Upload

OCR

AI

Chat

Search

Dashboard

---

# 18. AI Instructions

If you are an AI assistant working on this repository:

1. Read this file completely.
2. Follow the architecture strictly.
3. Do not invent new folder structures.
4. Do not change architecture without explanation.
5. Always write production-ready code.
6. Keep routers thin.
7. Keep business logic inside services.
8. Keep repositories responsible only for database access.
9. Prefer modular code.
10. If uncertain, preserve existing architecture instead of introducing a new pattern.

---

# 19. Project Vision

The goal is not just to build a working application.

The goal is to build software that resembles what an experienced backend engineer would develop for production.

Every design decision should prioritize:

- Maintainability
- Scalability
- Readability
- Security
- Performance
- Testability