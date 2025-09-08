import streamlit as st
import os
import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scopes required to read email data
# For security, always use the narrowest scope possible.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Define the path for the token file
TOKEN_FILE = 'token.json'

# --- Streamlit App UI ---
st.set_page_config(page_title="Streamlit Gmail Access", layout="wide")
st.title("Secure Gmail Access with Python")
st.write("This app demonstrates how to securely access a single, pre-configured Gmail account using OAuth 2.0 and Streamlit.")

# Function to get Gmail API credentials and handle authentication
def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            st.info("Your token has expired. Refreshing...")
            creds.refresh(Request())
        else:
            st.info("You need to authorize this app to access your Gmail account.")
            
            # Use Streamlit to get the credentials from the user securely
            st.warning("Please paste the contents of your `client_secret.json` or `credentials.json` file below:")
            credentials_input = st.text_area("JSON Credentials", height=200)

            if credentials_input:
                try:
                    client_config = json.loads(credentials_input)
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    
                    st.info("Please follow the authorization link below:")
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    st.markdown(f"[Authorize App]({auth_url})", unsafe_allow_html=True)

                    auth_code = st.text_input("After authorizing, paste the URL from your browser's address bar here:")
                    if auth_code:
                        flow.fetch_token(authorization_response=auth_code)
                        creds = flow.credentials
                        # Save the credentials for the next run
                        with open(TOKEN_FILE, 'w') as token:
                            token.write(creds.to_json())
                        st.success("Authentication successful! You can now proceed.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Authentication failed: {e}. Please check your credentials and try again.")
    return creds

# Function to fetch emails from the Gmail API
def get_emails(creds):
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Call the Gmail API to fetch the list of messages
        results = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            st.info("No messages found in your inbox.")
            return []

        email_data = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
            
            # Extract relevant headers for display
            headers = msg['payload']['headers']
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'N/A')
            subject_header = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date_header = next((h['value'] for h in headers if h['name'] == 'Date'), 'N/A')

            email_data.append({
                'id': msg['id'],
                'from': from_header,
                'subject': subject_header,
                'date': date_header
            })
        return email_data
    except HttpError as error:
        st.error(f'An HTTP error occurred: {error}')
        return []

# Main application logic
creds = get_credentials()

if creds and creds.valid:
    if st.button("Fetch Emails"):
        with st.spinner("Fetching emails..."):
            emails = get_emails(creds)
            if emails:
                st.subheader("Your Latest Emails")
                for email in emails:
                    st.markdown(
                        f"""
                        <div style="padding: 1rem; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);">
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.875rem; color: #6b7280;">
                                <span>{email['date']}</span>
                                <span>{email['from']}</span>
                            </div>
                            <h3 style="font-weight: 600; font-size: 1.25rem; color: #1f2937; margin-top: 0.5rem;">{email['subject']}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("No emails to display or an error occurred.")

# Instructions for the user
st.markdown("---")
st.markdown("""
### How to run this application:

1.  **Save this code:** Save the content above as a Python file (e.g., `app.py`).
2.  **Install dependencies:** Open your terminal and run the following command:
    `pip install streamlit google-api-python-client google-auth-oauthlib google-auth-httplib2`
3.  **Run the app:** In your terminal, navigate to the directory where you saved the file and run:
    `streamlit run app.py`
4.  **Follow the on-screen instructions:** The app will prompt you to paste your credentials and then guide you through the authorization process in your browser.
""")