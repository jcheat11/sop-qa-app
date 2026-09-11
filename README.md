# SOP Q&A

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in
a password and your Anthropic API key:

```
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

`.streamlit/secrets.toml` is gitignored and must never be committed.

Alternatively, the Anthropic key can be set as an environment variable instead
of a secret (useful for local dev without a secrets file):

```
setx ANTHROPIC_API_KEY "your-key-here"
```

(Restart your terminal after `setx`, or use `$env:ANTHROPIC_API_KEY = "..."` for the current PowerShell session only.)

## Run

```
streamlit run app.py
```

Upload a `.docx`, `.pdf`, `.txt`, or `.md` SOP in the sidebar, then ask questions in the chat.
