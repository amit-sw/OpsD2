# basic_auth0 — Streamlit Starter

This repository is initialized as a minimal Streamlit project with Google Authentication.

Getting started

0. Set up credentials from Google Cloud project as per https://docs.streamlit.io/develop/tutorials/authentication/google

1. Create and activate a virtual environment (macOS / zsh):

```
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Run the app:

```
streamlit run app.py
```

## Google Calendar Integration Setup

To use the Google Calendar integration, you need to configure a service account with access to the calendar you want to display.

### 1. Create a Google Cloud Project

If you don't have one already, create a new project in the [Google Cloud Console](https://console.cloud.google.com/).

### 2. Enable the Google Calendar API

- In your Google Cloud project, go to the "APIs & Services" > "Library" page.
- Search for "Google Calendar API" and enable it.

### 3. Create a Service Account

- Go to "APIs & Services" > "Credentials".
- Click "Create Credentials" and select "Service account".
- Fill in the service account details and grant it the "Viewer" role.
- After creating the service account, click on it to open its details.
- Go to the "Keys" tab, click "Add Key", and select "Create new key".
- Choose "JSON" as the key type and click "Create". A JSON file with the credentials will be downloaded.

### 4. Share Your Calendar

- Go to your Google Calendar settings.
- Under "Settings for my calendars", select the calendar you want to share.
- Click on "Share with specific people" and add the service account's email address (from the JSON file, `client_email`).
- Make sure to give it "See all event details" permissions.

### 5. Add Credentials to Streamlit Secrets

- Open your Streamlit Cloud project settings and go to the "Secrets" section.
- Add the following secrets, copying the values from the downloaded JSON file:
  - `gcp_service_account_type`
  - `gcp_service_account_project_id`
  - `gcp_service_account_private_key_id`
  - `gcp_service_account_private_key` (copy the entire key, including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines)
  - `gcp_service_account_client_email`
  - `gcp_service_account_client_id`
  - `gcp_service_account_auth_uri`
  - `gcp_service_account_token_uri`
  - `gcp_service_account_auth_provider_x509_cert_url`
  - `gcp_service_account_client_x509_cert_url`

### 6. Set up Supabase

You will also need to set up a Supabase project and create a table named `calendar_events` with the following columns:
- `event_id` (text, primary key)
- `summary` (text)
- `start_time` (timestamp with time zone)
- `end_time` (timestamp with time zone)

Add your Supabase URL and Key to the Streamlit secrets as `SUPABASE_URL` and `SUPABASE_KEY`.

