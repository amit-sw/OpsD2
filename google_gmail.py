import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta

def get_gmail_service():
    """Creates and returns a Gmail API service object."""
    try:
        creds_json = {
            "type": st.secrets.get("gmail_service_account_type"),
            "project_id": st.secrets.get("gmail_service_account_project_id"),
            "private_key_id": st.secrets.get("gmail_service_account_private_key_id"),
            "private_key": st.secrets.get("gmail_service_account_private_key"),
            "client_email": st.secrets.get("gmail_service_account_client_email"),
            "client_id": st.secrets.get("gmail_service_account_client_id"),
            "auth_uri": st.secrets.get("gmail_service_account_auth_uri"),
            "token_uri": st.secrets.get("gmail_service_account_token_uri"),
            "auth_provider_x509_cert_url": st.secrets.get("gmail_service_account_auth_provider_x509_cert_url"),
            "client_x509_cert_url": st.secrets.get("gmail_service_account_client_x509_cert_url"),
        }
        print(f"DEBUG: {st.secrets=}")
        print(f"DEBUG: Created creds_json {creds_json}")
        creds = service_account.Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/gmail.readonly'])
        print("DEBUG: Created credentials")
        # Impersonate a user
        delegated_creds = creds.with_subject(st.secrets.get("gmail_delegated_user_email"))
        print("DEBUG: Created delegated credentials")
        service = build('gmail', 'v1', credentials=delegated_creds)
        print("DEBUG: Created build for credentials")
        return service
    except Exception as e:
        st.error(f"Error creating Gmail service: {e}")
        print(f"Error creating Gmail service: {e}")
        return None

def search_gmail(service, query, days):
    """Searches for messages in the last n days."""
    if not service:
        return []

    try:
        # Calculate the date n days ago
        date_n_days_ago = datetime.now(timezone.utc) - timedelta(days=days)
        after_date = date_n_days_ago.strftime('%Y/%m/%d')

        # Add the date to the query
        full_query = f"{query} after:{after_date}"

        # Call the Gmail API
        result = service.users().messages().list(userId='me', q=full_query).execute()
        messages = []
        if 'messages' in result:
            messages.extend(result['messages'])

        # Get message details
        message_details = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            message_details.append(msg)

        return message_details
    except Exception as e:
        st.error(f"Error searching Gmail: {e}")
        print(f"Error searching Gmail: {e}")
        return []
