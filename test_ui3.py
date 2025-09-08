import os
import json
import streamlit as st
import urllib.parse
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"


def get_credentials() -> Optional[Credentials]:
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
            return creds
        except Exception as e:
            st.warning(f"Token refresh failed, please sign in again. Details: {e}")

    # Need user sign-in using secrets-based web client
    try:
        web = st.secrets.get("web")
        auth_cfg = st.secrets.get("auth")
        if not web or not auth_cfg:
            st.error(
                "Missing OAuth client in secrets. Please set [web] and [auth] in .streamlit/secrets.toml."
            )
            return None

        client_config = {
            "web": {
                "client_id": web.get("client_id"),
                "project_id": web.get("project_id"),
                "auth_uri": web.get("auth_uri"),
                "token_uri": web.get("token_uri"),
                "auth_provider_x509_cert_url": web.get("auth_provider_x509_cert_url"),
                "client_secret": web.get("client_secret"),
                "redirect_uris": [auth_cfg.get("redirect_uri")],
                "javascript_origins": [],
            }
        }

        flow_key = "oauth_flow"
        url_key = "oauth_auth_url"

        if flow_key not in st.session_state:
            st.session_state[flow_key] = Flow.from_client_config(
                client_config, scopes=SCOPES, redirect_uri=auth_cfg.get("redirect_uri")
            )
            auth_url, _ = st.session_state[flow_key].authorization_url(
                access_type="offline", include_granted_scopes="true", prompt="consent"
            )
            st.session_state[url_key] = auth_url

        st.info("1) Click to authorize Gmail read-only access.")
        st.markdown(
            f"[Authorize with Google]({st.session_state[url_key]})",
            unsafe_allow_html=True,
        )
        # Auto-complete if the browser redirected back with ?code=...
        try:
            params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
        except Exception:
            params = {}

        if isinstance(params, dict) and params.get("code"):
            # Reconstruct full authorization_response to match redirect_uri
            query = urllib.parse.urlencode({k: v if isinstance(v, str) else v[0] for k, v in params.items()})
            auth_response_url = f"{auth_cfg.get('redirect_uri')}?{query}"
            st.session_state[flow_key].fetch_token(authorization_response=auth_response_url)
            creds = st.session_state[flow_key].credentials
            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
            for k in (flow_key, url_key):
                if k in st.session_state:
                    del st.session_state[k]
            st.success("Authorized. Read-only Gmail access granted and saved.")
            st.rerun()
        else:
            # Manual fallback: let user paste either the full redirect URL or just the 'code'
            st.info("2) If you are not redirected here, paste the full redirect URL or just the authorization 'code' value below and click Complete.")
            user_input = st.text_input("Redirect URL or 'code' value")
            if st.button("Complete Sign-in") and user_input:
                # Accept either full URL or raw code
                if user_input.startswith("http"):
                    auth_response_url = user_input
                    st.session_state[flow_key].fetch_token(authorization_response=auth_response_url)
                else:
                    st.session_state[flow_key].fetch_token(code=user_input)
                creds = st.session_state[flow_key].credentials
                with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
                for k in (flow_key, url_key):
                    if k in st.session_state:
                        del st.session_state[k]
                st.success("Authorized. Read-only Gmail access granted and saved.")
                st.rerun()
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

    return None
st.set_page_config(page_title="Gmail Read-Only Login", layout="centered")
st.title("Sign in with Google (Gmail Read-Only)")

creds = get_credentials()

if creds and creds.valid:
    st.success("Already authorized for Gmail read-only.")
    if st.button("Reset authorization"):
        try:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            st.info("Removed saved credentials. Please sign in again.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to remove token: {e}")
else:
    st.info("Sign in to grant read-only access to your Gmail.")
