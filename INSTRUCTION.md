# Skyline - Complete Beginner's Setup & Usage Guide

This guide assumes you have **never** used Python, Git, VS Code, a terminal, or an API key before. Follow the steps in order and don't skip anything - every step is required exactly once.

By the end, you'll have a working weather app in your browser that uses AI to explain the weather in plain language.

---

## Table of contents

1. [Install Python](#1-install-python)
2. [Install Git](#2-install-git-optional-but-recommended)
3. [Install Visual Studio Code](#3-install-visual-studio-code)
4. [Install the recommended VS Code extension](#4-install-the-recommended-vs-code-extension)
5. [Open the project in VS Code](#5-open-the-project-in-vs-code)
6. [Open a terminal inside VS Code](#6-open-a-terminal-inside-vs-code)
7. [Create a virtual environment](#7-create-a-virtual-environment)
8. [Activate the virtual environment](#8-activate-the-virtual-environment)
9. [Install dependencies](#9-install-dependencies)
10. [Create your `.env` file](#10-create-your-env-file)
11. [Get your API keys](#11-get-your-api-keys)
12. [Run the application](#12-run-the-application)
13. [Test that everything works](#13-test-that-everything-works)
14. [Using every feature](#14-using-every-feature)
15. [Troubleshooting](#15-troubleshooting)
16. [FAQ](#16-faq)
17. [Common mistakes](#17-common-mistakes)
18. [Security recommendations](#18-security-recommendations)
19. [Next learning steps](#19-next-learning-steps)

---

## 1. Install Python

Python is the programming language this app is written in. You need it installed on your computer before anything else will work.

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow "Download Python 3.x.x" button (any version 3.10 or newer works).
3. Run the installer.
   - **Windows:** On the very first installer screen, check the box that says **"Add python.exe to PATH"** before clicking Install. This step is easy to miss and causes most beginner problems later.
   - **macOS:** Run the downloaded `.pkg` file and click through the installer (default options are fine).
4. When installation finishes, confirm it worked:
   - **Windows:** Press the Windows key, type `cmd`, press Enter, then type:
     ```
     python --version
     ```
   - **macOS:** Open **Terminal** (press `Cmd+Space`, type "Terminal", press Enter), then type:
     ```
     python3 --version
     ```
   You should see something like `Python 3.12.1`. If you see an error instead, see [Troubleshooting](#15-troubleshooting).

---

## 2. Install Git (optional, but recommended)

Git lets you download and manage code projects, and is required if you ever want to put this project on GitHub. It is **not** required just to run the app.

1. Go to **https://git-scm.com/downloads**
2. Download and run the installer for your operating system.
3. On Windows, the default options in the installer are fine - just keep clicking "Next".
4. Confirm it worked by opening a terminal and typing:
   ```
   git --version
   ```

---

## 3. Install Visual Studio Code

Visual Studio Code (VS Code) is the free code editor you'll use to open and run this project.

1. Go to **https://code.visualstudio.com/**
2. Click **Download**.
3. Run the installer and accept the default options.
4. Open VS Code once to confirm it launches.

---

## 4. Install the recommended VS Code extension

1. Open VS Code.
2. Click the **Extensions** icon in the left sidebar (it looks like four squares, one detached).
3. Search for **"Python"** (published by Microsoft).
4. Click **Install**.

This extension lets VS Code understand Python files, run them, and manage virtual environments for you.

---

## 5. Open the project in VS Code

1. Unzip the project folder (`weather-ai`) somewhere easy to find, like your Desktop.
2. In VS Code, go to **File -> Open Folder...**
3. Select the `weather-ai` folder and click **Select Folder** (or **Open**).

You should now see files like `app.py`, `config.py`, and `README.md` in the sidebar on the left.

---

## 6. Open a terminal inside VS Code

You'll type all the setup commands into VS Code's built-in terminal, so you don't need to switch windows.

- Go to **Terminal -> New Terminal** in the top menu, **or**
- Press `` Ctrl+` `` (Windows/Linux) or `` Cmd+` `` (macOS).

A terminal panel opens at the bottom of VS Code. All commands below are typed here.

---

## 7. Create a virtual environment

A "virtual environment" is an isolated Python installation just for this project, so its dependencies don't clash with anything else on your computer. Think of it as a clean, private toolbox for this project only.

In the terminal, type:

```bash
python -m venv venv
```

(On macOS, if `python` isn't recognized, use `python3 -m venv venv` instead.)

This creates a new folder called `venv` inside your project. Nothing visible happens yet - that's expected.

---

## 8. Activate the virtual environment

"Activating" tells your terminal to use the project's private Python toolbox instead of your computer's main one.

- **Windows (PowerShell - the default VS Code terminal):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
  If you get a red error mentioning "execution policy," run this once, then try activating again:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  ```

- **Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```

- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

**How to know it worked:** your terminal prompt now starts with `(venv)`, like:
```
(venv) C:\Users\you\weather-ai>
```

You'll need to repeat this activation step **every time** you open a new terminal to work on this project (but you only create the `venv` folder once, in step 7).

---

## 9. Install dependencies

"Dependencies" are the external code libraries this project needs (Flask, requests, OpenAI/Anthropic SDKs, etc.). With your virtual environment still activated, type:

```bash
pip install -r requirements.txt
```

This downloads and installs everything listed in `requirements.txt`. It may take a minute or two. When it finishes without red error text, you're done.

---

## 10. Create your `.env` file

The `.env` file holds your personal secret keys. It must never be shared or uploaded anywhere public.

1. In the VS Code file explorer, find `.env.example`.
2. Copy it and rename the copy to exactly `.env` (no `.example`). You can do this in the terminal:
   - **Windows:** `copy .env.example .env`
   - **macOS/Linux:** `cp .env.example .env`
3. Open `.env` by clicking it in the VS Code sidebar. You'll fill in real values in the next step.

---

## 11. Get your API keys

This app needs **three** pieces of secret configuration in `.env`: a Flask secret key, a weather API key, and an AI provider key.

### 11.1 Generate the Flask `SECRET_KEY`

In your terminal (with `venv` still activated), run:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the long string it prints out, and paste it as the value of `SECRET_KEY` in `.env`:

```
SECRET_KEY=paste_the_generated_string_here
```

### 11.2 Get a free OpenWeatherMap key

1. Go to **https://openweathermap.org/api**
2. Click **Sign Up**, create a free account, and confirm your email.
3. Log in, then go to the **API keys** tab on your account page.
4. Copy your key and paste it into `.env`:
   ```
   WEATHER_API_KEY=paste_your_key_here
   ```

> ⚠️ New OpenWeatherMap keys can take up to a couple of hours to activate. If you get a "401 rejected" error immediately after signing up, wait a bit and try again.

### 11.3 Get an AI provider key (choose ONE)

You only need **one** of these two - pick whichever you have access to.

**Option A - OpenAI:**
1. Go to **https://platform.openai.com/api-keys**
2. Log in (or sign up), click **Create new secret key**, and copy it immediately (you won't be able to see it again).
3. In `.env`, set:
   ```
   AI_PROVIDER=openai
   OPENAI_API_KEY=paste_your_key_here
   ```

**Option B - Anthropic (Claude):**
1. Go to **https://console.anthropic.com/settings/keys**
2. Log in (or sign up), click **Create Key**, and copy it.
3. In `.env`, set:
   ```
   AI_PROVIDER=anthropic
   ANTHROPIC_API_KEY=paste_your_key_here
   ```

Both providers typically require adding billing details to their platform before API calls will succeed, even for small amounts of usage - check each provider's dashboard.

### 11.4 Save the file

Press `Ctrl+S` (or `Cmd+S` on macOS) in VS Code to save `.env`. Double check:
- There's only **one** line for each key (no duplicates).
- None of the values still say `your_..._api_key_here` - those are placeholders and must be replaced.

---

## 12. Run the application

With your virtual environment activated (prompt shows `(venv)`), type:

```bash
python app.py
```

You should see log lines ending with something like:
```
* Running on http://127.0.0.1:1020
```

Hold `Ctrl` and click that link, or manually open **http://127.0.0.1:1020** in your web browser.

**To stop the app:** click back into the terminal and press `Ctrl+C`.

---

## 13. Test that everything works

1. With the app running and open in your browser, type a city name (e.g. `London`) into the search box and press Enter.
2. You should see live weather data appear, followed by AI-generated sections (explanation, clothing, travel, sports, comfort score).
3. If weather data appears but AI sections show an error, double-check your AI provider key in `.env` and restart the app (see [step 12](#12-run-the-application)).
4. Try the chat box at the bottom and ask something like "What should I wear today?"

If all of that works, your setup is complete. 🎉

---

## 14. Using every feature

- **🔍 City search** - type any city name in the main search bar to fetch live weather.
- **🤖 AI explanation** - automatically appears under the weather card in plain language.
- **👕 Clothing recommendation** - tells you what to wear based on current conditions.
- **🧭 Travel recommendation** - advises whether it's a good day to travel or commute.
- **🏃 Sports & activity recommendation** - suggests suitable indoor/outdoor activities.
- **📊 Comfort score** - an animated 0-100 ring showing overall weather pleasantness.
- **🏙️ City comparison** - use the compare form to enter 2-4 cities and get an AI-written comparison.
- **💬 AI chat** - ask open-ended weather questions; if a city is currently loaded, the AI uses its live data as context.
- **✨ Suggested prompt chips** - tap a suggested question to auto-fill the chat box.
- **🌗 Dark / light mode** - use the toggle in the interface to switch themes.
- **🕘 Search history** - previously searched cities are saved locally in your browser (not sent anywhere) for quick re-access.

---

## 15. Troubleshooting

**`'python' is not recognized as an internal or external command` (Windows)**
Python wasn't added to PATH during installation. Reinstall Python from python.org and make sure to check "Add python.exe to PATH" on the first installer screen.

**`source venv/bin/activate` not recognized**
That command is for macOS/Linux. On Windows PowerShell, use `venv\Scripts\Activate.ps1` instead.

**PowerShell execution policy error when activating**
Run this once in the same terminal, then activate again:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

**`No module named 'flask'` (or `openai`, `anthropic`, etc.)**
Your virtual environment probably isn't activated - check that your prompt starts with `(venv)`. If it does and the error persists, run `pip install -r requirements.txt` again.

**`Weather API key was rejected by the provider (401)`**
Your `.env` still has the placeholder text, has a duplicate `WEATHER_API_KEY=` line, the key hasn't finished activating yet (can take up to ~2 hours after signup), or you didn't restart the app after editing `.env`.

**"AI insights unavailable" appears in the app**
Check the terminal running the app for a line starting with `[WARNING] weather-ai: AI insights failed for...` - it names the exact problem (bad key, no billing set up, wrong model name).

**Changes to `.env` don't seem to apply**
`.env` is only read when the app starts. After editing it: click the terminal, press `Ctrl+C` to stop the app, then run `python app.py` again.

**The page loads but looks unstyled / broken**
Make sure `templates/index.html`, `static/css/style.css`, and `static/js/app.js` are still in their original folders (`templates/` and `static/`) - Flask expects this exact structure.

**Port 1020 is already in use**
Another program (or a previous run of this app) is using port 1020. Either stop that program, or set a different port in `.env`:
```
PORT=5001
```
Then open `http://127.0.0.1:5001` instead.

---

## 16. FAQ

**Do I need both an OpenAI key and an Anthropic key?**
No - only one, matching whatever you set `AI_PROVIDER` to.

**Is this app free to run?**
OpenWeatherMap has a free tier sufficient for personal use. OpenAI and Anthropic charge per API call (usually fractions of a cent per request for this app's usage), and both generally require billing details on file even to start.

**Can I run this without VS Code?**
Yes - VS Code is just a convenient editor. Any terminal and text editor will work; the terminal commands are the same.

**Do I need to reinstall dependencies every time I open the project?**
No. `pip install -r requirements.txt` only needs to be run once (or again if `requirements.txt` changes). You do need to **activate** the virtual environment every time you open a new terminal, though.

**Why does the app say weather works but AI doesn't (or vice versa)?**
Weather and AI are two independent services. It's normal for one to work while the other is misconfigured - the error message will tell you which one and why.

---

## 17. Common mistakes

- Forgetting to check "Add python.exe to PATH" during Python installation (Windows).
- Forgetting to activate the virtual environment before running `pip install` or `python app.py`.
- Leaving placeholder text (`your_..._api_key_here`) in `.env` instead of a real key.
- Editing `.env` while the app is running, then expecting changes to apply without restarting.
- Renaming `.env.example` incorrectly (must become exactly `.env`, not `.env.example.env` or similar).
- Moving `index.html`, `style.css`, or `app.js` out of their `templates/`/`static/` folders.
- Committing or sharing the real `.env` file (see [Security recommendations](#18-security-recommendations)).

---

## 18. Security recommendations

- **Never share your `.env` file or its contents** - it contains secret API keys tied to your accounts and potential billing.
- **Never commit `.env` to Git/GitHub.** The project's `.gitignore` already excludes it, but always double-check before pushing.
- If you ever accidentally expose a key (e.g. pasted it in a public chat or committed it), **revoke/regenerate it immediately** on the provider's dashboard (OpenWeatherMap, OpenAI, or Anthropic) - treat it like a leaked password.
- Only run the app with `FLASK_DEBUG=true` on your own machine for local development. Never enable debug mode on a version of the app that's reachable by the public internet - it allows remote code execution.
- Don't remove or weaken the city-name/message-length validation already built into `weather_service.py` and `app.py`; it protects both your API usage costs and the AI prompts from malformed input.

---

## 19. Next learning steps

Once you're comfortable running the app, here are natural next steps:

1. **Read `app.py` top to bottom** - it's the shortest file that touches every part of the app (routes, error handling, service wiring), making it a good map of the whole project.
2. **Learn Flask basics** - the official tutorial at https://flask.palletsprojects.com/ explains routes, templates, and JSON responses used throughout this project.
3. **Learn about environment variables and `.env` files** - understanding *why* secrets live outside your code is a foundational skill for every real-world project.
4. **Try modifying a prompt** in `prompt.py` and restart the app to see how it changes the AI's tone or output - a safe, contained way to experiment.
5. **Learn Git basics** (`git init`, `git add`, `git commit`, `git push`) so you can version-control your own changes and eventually publish the project.
6. **Explore adding automated tests** with `pytest` - see `PROJECT_REVIEW.md` for specific suggestions on what to test first.
