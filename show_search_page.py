import streamlit as st
from google_gmail import get_gmail_service, search_gmail

def show_search_page():
    st.title("Search Gmail")

    # Create the search form
    with st.form(key='search_form'):
        query = st.text_input("Search query")
        days = st.number_input("Number of days", min_value=1, value=7)
        submit_button = st.form_submit_button(label='Search')

    if submit_button:
        if not query:
            st.warning("Please enter a search query.")
            return

        # Get the Gmail service
        service = get_gmail_service()

        if service:
            # Search for messages
            with st.spinner("Searching..."):
                messages = search_gmail(service, query, days)

            if messages:
                st.success(f"Found {len(messages)} messages.")
                # Display the messages
                for message in messages:
                    with st.expander(f"Subject: {next((header['value'] for header in message['payload']['headers'] if header['name'] == 'Subject'), 'No Subject')}"):
                        st.write(f"From: {next((header['value'] for header in message['payload']['headers'] if header['name'] == 'From'), 'N/A')}")
                        st.write(f"Date: {next((header['value'] for header in message['payload']['headers'] if header['name'] == 'Date'), 'N/A')}")
                        st.write("---")
                        st.write(message['snippet'])
            else:
                st.info("No messages found.")
