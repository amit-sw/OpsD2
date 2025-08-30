import streamlit as st
from supabase import create_client, Client



def get_supabase_client():
    """Creates and returns a Supabase client."""
    SUPABASE_URL = st.secrets.get("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        print(f"Error connecting to Supabase: {e}")
        return None

def add_to_waitlist(supabase, email):
    """
    Adds a user's email to the 'waitlist' table in Supabase.

    INCOMPLETE: This function assumes a table named 'waitlist' with an 'email' column.
    """
    if not supabase:
        return
    try:
        supabase.table('waitlist').insert({'email': email}).execute()
        st.success("You have been added to the waitlist. We will notify you once you have access.")
    except Exception as e:
        st.error(f"Error adding to waitlist: {e}")
        print(f"Error adding to waitlist: {e}")

def show_waitlist_form(supabase, email):
    """Displays a form to add the user's email to the waitlist."""
    if st.button("Join Waitlist"):
        add_to_waitlist(supabase, email)


def show_waitlist(supabase):
    """Displays the waitlist screen."""
    waitlist = supabase.table('waitlist').select('*').execute().data
    st.title("Waitlist")
    st.write("You are currently on the waitlist. Here are the current entries:")
    for entry in waitlist:
        st.write(f"- {entry}")    
    st.write("We will notify you once you have access.")