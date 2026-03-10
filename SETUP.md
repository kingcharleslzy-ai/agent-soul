# SETUP.md — Human Setup Guide

This file is for the human. Your AI agent will handle the rest after these steps.

Estimated time: **10 minutes**

---

## Step 1 — Create a private GitHub repository

1. Go to [github.com/new](https://github.com/new)
2. Name it anything (e.g. `my-agent-memory`, `agent-hub`, `brain`)
3. Set visibility to **Private**
4. Do not initialize with a README
5. Click **Create repository**

---

## Step 2 — Clone this template and push to your private repo

```bash
git clone https://github.com/kingcharleslzy-ai/agent-soul.git my-agent-memory
cd my-agent-memory
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

---

## Step 3 — Enable GitHub Actions

In your private repo on GitHub:

1. Go to **Settings → Actions → General**
2. Under "Actions permissions", select **Allow all actions and reusable workflows**
3. Click **Save**

---

## Step 4 — Fill in the persona files

Open these four files and fill them in. They define who your assistant is:

- **`SOUL.md`** — Core values and identity contract. Replace `[USER]` with the user's name.
- **`IDENTITY.md`** — Assistant's name, role, and vibe.
- **`USER.md`** — Who the user is and how to relate to them.
- **`VOICE.md`** — Communication style and tone.

Commit and push when done:

```bash
git add SOUL.md IDENTITY.md USER.md VOICE.md
git commit -m "chore: fill in persona files"
git push origin main
```

---

## Step 5 — Give the AI access

Your AI agent needs to be able to `git clone` and `git push` to your private repo.

**Option A: Personal access token (simplest)**

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with `repo` scope
3. Give the token to your AI agent and tell it to use:
   ```
   https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   ```

**Option B: SSH key**

1. Generate an SSH key on the machine where your AI runs:
   ```bash
   ssh-keygen -t ed25519 -C "agent-soul"
   ```
2. Add the public key to GitHub: **Settings → SSH and GPG keys → New SSH key**
3. Clone using the SSH URL: `git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git`

---

## Step 6 — Tell the AI

Give your AI agent:

1. The absolute path to the cloned repo
2. Its assigned `source` id (e.g. `windows-claude`, `macos-codex`)

Then say: **"Follow JOIN.md to complete your onboarding."**

The AI handles everything from here.

---

## That's it

From this point on, your AI agent manages its own memory:

- reads shared memory at session start
- writes new events after important work
- pushes back to keep all your agents in sync

No further human intervention needed for memory operations.
