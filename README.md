# Recitation2 — Arabic Text Study Prototype

Recitation2 is an early prototype for exploring Arabic text and study workflows. The repository includes a SvelteKit interface and a FastAPI backend with initial book, author, project, review, and AI-configuration routes. The wider product requirements are exploratory; this repository should be understood as a scaffold, not as a completed research platform.

## Stack

- SvelteKit, Svelte, TypeScript, and Vite
- FastAPI and Python
- Local development storage and user-configured AI provider integrations

## Local setup

Requirements: Python 3.10+, Node.js, and npm.

1. In `backend`, create a virtual environment, activate it, install `requirements.txt`, copy `.env.example` to `.env`, and set `SECRET_KEY` to a long random value before starting the API with `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.
2. In a second terminal, run `npm install` and `npm run dev` from `frontend`.
3. Open the local URL reported by Vite.

This portfolio copy omits the original local database, uploaded files, virtual environment, logs, and internal agent configuration. The AI configuration and extraction workflow are incomplete and need further testing; no performance or research-accuracy claims are made.
