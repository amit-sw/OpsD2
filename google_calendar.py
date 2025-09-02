import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

def get_calendar_service():
    """Creates and returns a Google Calendar service object."""
    try:
        creds_json = {
            "type": st.secrets.get("gcp_service_account_type"),
            "project_id": st.secrets.get("gcp_service_account_project_id"),
            "private_key_id": st.secrets.get("gcp_service_account_private_key_id"),
            "private_key": st.secrets.get("gcp_service_account_private_key"),
            "client_email": st.secrets.get("gcp_service_account_client_email"),
            "client_id": st.secrets.get("gcp_service_account_client_id"),
            "auth_uri": st.secrets.get("gcp_service_account_auth_uri"),
            "token_uri": st.secrets.get("gcp_service_account_token_uri"),
            "auth_provider_x509_cert_url": st.secrets.get("gcp_service_account_auth_provider_x509_cert_url"),
            "client_x509_cert_url": st.secrets.get("gcp_service_account_client_x509_cert_url"),
        }
        creds = service_account.Credentials.from_service_account_info(creds_json)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Error creating Google Calendar service: {e}")
        print(f"Error creating Google Calendar service: {e}")
        return None

def get_calendar_events(service):
    """Fetches events from the primary calendar."""
    if not service:
        print(f"ERROR: No valid Google Calendar service provided.")
        return []
    try:
        one_month_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='coordinator@pyxeda.ai',
            timeMin=one_month_ago,
            maxResults=3000, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        print(f"Fetched {len(events)=} events from Google Calendar.")
        return events
    except Exception as e:
        st.error(f"Error fetching calendar events: {e}")
        print(f"Error fetching calendar events: {e}")
        return []
