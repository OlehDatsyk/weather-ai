# Skyline - AI-Powered Weather Assistant

Skyline is a full-stack weather assistant that pairs live weather data with
an LLM (OpenAI's Responses API or Claude's Messages API) to explain
conditions in plain language and recommend clothing, travel plans, and
activities - plus a chat interface for open-ended weather questions and a
multi-city comparison tool.

## Features

- 🔍 **Weather search** - live current conditions for any city (OpenWeatherMap)
- 🤖 **AI explanation** - plain-language read of current conditions
- 👕 **AI clothing recommendation**
- 🧭 **AI travel recommendation**
- 🏃 **AI sports & activity recommendation**
- 📊 **AI weather comfort score** (0–100, animated ring)
- 🏙️ **AI city comparison** - compare 2–4 cities at once
- 💬 **AI chat** - ask free-form weather questions, grounded in live data
- ✨ **Modern chat UI** - typing animation, suggested prompt chips, conversation history
- 🌗 **Dark / light mode**
- 📱 **Fully responsive** layout
- 🛡️ **Security** - env-based secrets, strict input validation, structured error handling

## Tech stack

| Layer     | Technology                                   |
|-----------|-----------------------------------------------|
| Backend   | Python 3.10+, Flask                           |
| AI        | OpenAI Responses API **or** Claude Messages API |
| Weather   | OpenWeatherMap Current Weather API            |
| Frontend  | Vanilla JavaScript, HTML5, CSS3 (no build step) |

## Folder structure

```
weather-ai/
├── app.py                 # Flask app factory, routes, error handlers
├── weather_service.py     # Weather API client + data normalization
├── ai_service.py          # AI provider abstraction (OpenAI / Anthropic) + domain logic
├── prompt.py               # All LLM prompt templates
├── config.py               # Environment-based configuration + validation
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html          # Main UI markup
└── static/
    ├── css/
    │   └── style.css       # Design system + responsive styling
    └── js/
        └── app.js          # Frontend logic (search, chat, animations)
```

### Architecture notes

- **Clean separation of concerns**: `weather_service.py` knows nothing about
  AI; `ai_service.py` knows nothing about HTTP requests to OpenWeatherMap;
  `prompt.py` holds every piece of prompt text so it can be tuned without
  touching networking code; `app.py` only wires routes to these services.
- **Provider abstraction**: `AIProvider` is an abstract interface with
  `OpenAIProvider` and `AnthropicProvider` implementations, selected at
  startup via `AI_PROVIDER` in `.env`. Swapping providers requires no code
  changes - just an environment variable.
- **Typed throughout**: dataclasses (`WeatherData`), `TypedDict`s
  (`WeatherInsights`, `ChatMessage`), and type hints on every function
  signature.

## Prerequisites

- Python 3.10 or newer
- A free [OpenWeatherMap](https://openweathermap.org/api) API key
- An [OpenAI](https://platform.openai.com/api-keys) **or**
  [Anthropic](https://console.anthropic.com/settings/keys) API key
- Visual Studio Code (recommended: install the "Python" extension by Microsoft)

## Installation guide (Visual Studio Code)

1. **Open the project folder** in VS Code: `File -> Open Folder... -> weather-ai`

2. **Create a virtual environment** (open a terminal in VS Code with
   `` Ctrl+` ``):

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:

   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     venv\Scripts\Activate.ps1
     ```
   - Windows (cmd.exe):
     ```cmd
     venv\Scripts\activate.bat
     ```

   In VS Code, select this interpreter via `Ctrl+Shift+P` ->
   `Python: Select Interpreter` -> choose `./venv`.

4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## API key setup

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

   (Windows: `copy .env.example .env`)

2. Generate a Flask secret key and paste it into `.env`:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Get a **free** OpenWeatherMap key at
   <https://openweathermap.org/api> -> sign up -> API keys tab, then set:

   ```
   WEATHER_API_KEY=your_key_here
   ```

4. Choose an AI provider and set the matching key in `.env`:

   - **OpenAI** (default):
     ```
     AI_PROVIDER=openai
     OPENAI_API_KEY=your_key_here
     OPENAI_MODEL=gpt-4.1
     ```
   - **Claude**:
     ```
     AI_PROVIDER=anthropic
     ANTHROPIC_API_KEY=your_key_here
     ANTHROPIC_MODEL=claude-sonnet-4-6
     ```

5. Save `.env`. It is already excluded from git via `.gitignore` - **never
   commit real API keys**.

## Run commands

With the virtual environment activated:

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

For a production-style local run with gunicorn:

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## Running / debugging inside VS Code

- Press `F5` (or `Run -> Start Debugging`) with a `launch.json` configured
  for `app.py`, or simply run `python app.py` in the integrated terminal.
- Set breakpoints directly in `app.py`, `weather_service.py`, or
  `ai_service.py` - Flask's debug reloader (`FLASK_DEBUG=true`) will pick up
  code changes automatically.

## Deployment recommendations

- **Platforms**: Render, Railway, Fly.io, or a small VPS all work well for
  this app's size. Any platform supporting Python + environment variables
  is fine.
- **WSGI server**: always run behind `gunicorn` (included in
  `requirements.txt`) in production - never use Flask's built-in dev server.
  Example `Procfile`:
  ```
  web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
  ```
- **Environment variables**: set `SECRET_KEY`, `WEATHER_API_KEY`,
  `AI_PROVIDER`, and the relevant AI key directly in your host's dashboard
  (Render/Railway "Environment" tab) - do not upload `.env`.
- **HTTPS**: terminate TLS at your platform's edge/load balancer (most
  PaaS providers do this automatically).
- **Rate limiting**: consider adding `Flask-Limiter` in front of
  `/api/chat` and `/api/weather` if you expect public traffic, since both
  endpoints call paid third-party APIs.
- **Observability**: the app already logs warnings/errors via Python's
  `logging` module; forward stdout/stderr to your platform's log
  aggregator (built in on Render/Railway/Fly).
- **Scaling**: the app is stateless (no server-side session or database),
  so it scales horizontally with more gunicorn workers or replicas without
  any changes.

## Quick reference: Windows / PowerShell / VS Code

If you're on Windows and just want the exact command sequence to copy and
paste, use this section.

### First-time setup

```powershell
cd "path\to\weather-ai"

python -m venv venv
venv\Scripts\Activate.ps1
```

If activation fails with an execution-policy error, run this once, then
repeat the activate command:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
venv\Scripts\Activate.ps1
```

Your prompt should now start with `(venv)`. Then:

```powershell
pip install -r requirements.txt
pip show openai
copy .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
code .env
```

In the `.env` file that opens, fill in and **save**:

```
SECRET_KEY=<paste the key generated above>
WEATHER_API_KEY=<your real OpenWeatherMap key>
OPENAI_API_KEY=<your real OpenAI key>
OPENAI_MODEL=gpt-4o-mini
```

Make sure there is only **one** `WEATHER_API_KEY=` line, and it is not still
the placeholder text `your_openweathermap_api_key_here`.

Then run and open the app:

```powershell
python app.py
```

Ctrl+click the printed link, or open **http://127.0.0.1:5000** manually.

### Every time you come back later

```powershell
cd "path\to\weather-ai"
venv\Scripts\Activate.ps1
python app.py
```

### If you ever edit `.env`

`.env` is only read at startup, so changes won't apply automatically:

1. Click into the terminal running the app.
2. Press `Ctrl+C` to stop it.
3. Run `python app.py` again.
4. Refresh the browser tab.

### Troubleshooting

**`source venv/bin/activate` not recognized**
That's macOS/Linux syntax. On Windows PowerShell use `venv\Scripts\Activate.ps1` instead.

**`No module named 'openai'`**
Confirm `(venv)` is shown in your prompt, then run `pip install -r requirements.txt` again - this error usually means `pip install` ran against a different Python than the one running `app.py`.

**`Weather API key was rejected by the provider (401)`**
Your `.env` still has the placeholder text, has a duplicate `WEATHER_API_KEY` line, or you didn't restart the server after editing `.env`. Fix `.env`, save it, stop the server (`Ctrl+C`), and run `python app.py` again.

**"AI insights unavailable" in the app**
Check the terminal for a line starting with `[WARNING] weather-ai: AI insights failed for...` - it names the exact problem (bad key, no billing, wrong model name). A common fix is setting `OPENAI_MODEL=gpt-4o-mini` in `.env` and restarting.

**Flat file structure (`index.html`/`style.css`/`app.js` not found by Flask)**
If these ended up directly inside `weather-ai/` instead of `templates/` and `static/`, move them:

```powershell
mkdir templates
mkdir static
mkdir static\css
mkdir static\js
move index.html templates\
move style.css static\css\
move app.js static\js\
```

## Security notes

- No API key is ever hardcoded - all secrets load from environment
  variables via `python-dotenv` / the host environment.
- City names and chat messages are validated and length-limited before
  reaching any external API (`weather_service.py`, `app.py`).
- All external calls (weather + AI) are wrapped in specific exception
  types and translated into clean JSON error responses with appropriate
  HTTP status codes - no stack traces are ever leaked to the client.
- `SECRET_KEY` should be a long random value in any real deployment (see
  API key setup above).

## License

This project is provided as-is for educational and personal use.
