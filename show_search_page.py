import streamlit as st
from typing import Dict, List, Optional, Tuple

import os
import json
import urllib.parse
import time


from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build


from supabase_integration import get_supabase_client, get_token_from_db



SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
TOKEN_FILE = "token.json"

def get_saved_credentials() -> Optional[Credentials]:
    if not os.path.exists(TOKEN_FILE):
        supabase_client = get_supabase_client()
        token_db = get_token_from_db(supabase_client)
        token=token_db["token"]
        st.success(token)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(token,f)
    try:
        return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except Exception:
        return None
    
def refresh_if_needed(creds: Credentials) -> Optional[Credentials]:
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            return creds
        except Exception as e:
            msg = str(e)
            if "invalid_scope" in msg or "invalid_grant" in msg:
                try:
                    if os.path.exists(TOKEN_FILE):
                        os.remove(TOKEN_FILE)
                except Exception:
                    pass
                st.warning("Saved token is no longer valid for the current scopes. Please sign in again.")
                return None
            st.warning(f"Token refresh failed: {e}")
    return None

def gmail_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_message_ids(service, query: str, limit: int, fetch_all: bool = False, cap: int = 1000) -> Tuple[List[str], int]:
    ids, token, est = [], None, 0
    target = cap if fetch_all else limit
    while len(ids) < target:
        resp = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=min(100, target - len(ids)),
                pageToken=token,
            )
            .execute()
        )
        est = resp.get("resultSizeEstimate", est)
        msgs = resp.get("messages", [])
        if not msgs:
            break
        ids.extend([m["id"] for m in msgs])
        token = resp.get("nextPageToken")
        if not token:
            break
    return (ids[:target], est)

def fetch_metadata(service, msg_id: str) -> Dict[str, str]:
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=msg_id, format="metadata", metadataHeaders=["From", "To", "Subject", "Date"])
        .execute()
    )
    headers = {h["name"]: h.get("value", "") for h in msg.get("payload", {}).get("headers", [])}
    return {
        "Subject": headers.get("Subject", ""),
        "From": headers.get("From", ""),
        "Date": headers.get("Date", ""),
        "Snippet": msg.get("snippet", ""),
        "Message ID": msg.get("id", ""),
        "Thread ID": msg.get("threadId", ""),
    }

def gmail_search(creds: Credentials, query: str, limit: int, fetch_all: bool = False) -> Tuple[List[Dict[str, str]], int]:
    try:
        svc = gmail_service(creds)
        ids, est = list_message_ids(svc, query, limit, fetch_all)
        return ([fetch_metadata(svc, i) for i in ids], est)
    except HttpError as e:
        raise RuntimeError(f"Gmail API error: {e}")

def search_ui(creds: Credentials, query_term=None) -> None:
    search_expression = "in:inbox newer_than:7d"
    if query_term:
        search_expression = query_term + search_expression
    st.subheader("Mail messages for Coordinator")
    limit = st.sidebar.slider("Max results", min_value=100, max_value=1000, value=200, step=100)
    fetch_all = False
    q = st.text_input("Gmail search query", value=search_expression, label_visibility="hidden")

    run = st.button("Search")
    if run:
        start = time.perf_counter()
        with st.spinner("Fetching results from Gmail API…", show_time=True):
            rows, est = gmail_search(creds, q, limit, fetch_all)
        elapsed = time.perf_counter() - start
        duration = f"{elapsed*1000:.0f} ms" if elapsed < 1 else f"{elapsed:.2f} s"
        if not rows:
            st.info("No messages found.")
            st.caption(f"Completed in {duration}")
            return
        st.write(f"Showing {len(rows)} of ~{est} message(s).")
        if est > len(rows) and not fetch_all:
            st.info("Increase Max results or enable 'Fetch all'.")
        st.dataframe(rows, use_container_width=True)
        st.sidebar.caption(f"Last fetch took {duration}")
    
def show_search_page(query_term=None) -> None:
    creds = get_saved_credentials()
    creds = refresh_if_needed(creds) if creds else None
    if creds and creds.valid:
        search_ui(creds,query_term=query_term)
        return
    else:
        st.error("Invalid credentials")


if __name__ == "__main__":
    show_search_page()  
