# MOT Saudi Demo Submission App

A simple Streamlit app to inject demo messages into the Anecdote public API for the MOT Saudi project.

## Features

- Submit a single message
- Automatically generates:
  - `unique_id`
  - `ticket_id`
  - UTC timestamp
- Supports:
  - optional source override
  - optional key/value filters
- Uses Streamlit secrets for the API token

## Project configuration

The app is configured with:

- `PROJECT_ID = "mot-saudi"`
- `TAXONOMY_ID = "default"`
- `SKIP_STEPS = {}`
- `API_URL = "https://public-api.anecdoteai.com/inject"`
- `DEFAULT_SOURCE = "demo"`

## Local setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add your Streamlit secret

Create a local file at `.streamlit/secrets.toml` and add:

```toml
ANECDOTE_API_TOKEN = "your_real_token_here"
```

### 3. Run the app

```bash
streamlit run app.py
```

## Deploying on Streamlit Cloud

In your app settings, add this secret:

```toml
ANECDOTE_API_TOKEN = "your_real_token_here"
```

## Payload format

Each submission sends:

```json
{
  "project_id": "mot-saudi",
  "taxonomy_id": "default",
  "skip_steps": {},
  "batch": [
    {
      "message": "example message",
      "ds": "2026-04-26T12:00:00Z",
      "unique_id": "msg-xxxxxxxxxxxxxxxx",
      "ticket_id": "msg-xxxxxxxxxxxxxxxx",
      "source": "demo",
      "filters": {
        "platform": "iOS"
      }
    }
  ]
}
```
