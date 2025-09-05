import streamlit as st
st.set_page_config(layout="wide")

from supabase_integration import get_supabase_client, get_user_from_db, get_students_from_db
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from google_calendar import get_calendar_service, get_events_for_emails


from show_events import show_events_all
from show_students_ag import choose_student_show_events
from show_students_page import show_students_page




def show_ui_core(user):
    name = user.get("name", "Unknown User")
    email = user.get("email", "Unknown Email")
    picture = user.get("picture", "")
    email_verified = user.get("email_verified", False)
    
    # Initialize session state for active tab if not exist
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Students"  # Make Students the default tab
    
    # Process URL parameters to set the active tab
    if "tab" in st.query_params and st.query_params["tab"] in ["Calendar", "Students", "Student Events"]:
        st.session_state.active_tab = st.query_params["tab"]
    elif "student" in st.query_params and st.query_params["student"]:
        # If student parameter is present but no tab, default to Students tab
        st.session_state.active_tab = "Students"

    with st.sidebar:
        st.text(f"Welcome {name}\n {email}")
        if email_verified:
            st.success("Email is verified.")
        else:
            st.warning("Email is not verified.")
        if picture:
            st.image(picture, width=100)
            
        # Navigation tabs - use the session state to set the default
        st.subheader("Navigation")
        tab = st.radio("Select Page", ["Calendar", "Students","Student Events"], 
                      index=["Calendar", "Students","Student Events"].index(st.session_state.active_tab),
                      label_visibility="collapsed")
        
        # Update the session state when tab changes via the sidebar
        if tab != st.session_state.active_tab:
            st.session_state.active_tab = tab
        
        if st.button("Log out"):
            st.logout() 
    if tab == "Calendar":
        st.title("Club Ops Calendar Events")
        show_events_all()
    elif tab == "Students":
        show_students_page()
    elif tab == "Student Events":    
        choose_student_show_events()

def show_ui_admin(user):
    #st.title("Admin Panel")
    #st.write("This is the admin panel. More features coming soon!")
    show_ui_core(user)

def show_ui_guest(user):
    st.title("Guest Access")
    st.write(f"You do not have access. Please reach out to System Administrator with your information\n Email: {user.get("email", "Unknown Email")}.")
    if st.button("Log out"):
        st.logout()
    #show_ui_core(user)

def show_ui_user(user):
    #st.title("User Access")
    #st.write("Welcome to the user panel. More features coming soon!")
    show_ui_core(user)

def show_ui(user):
    if user and user.get("email_verified", False):
        supabase = get_supabase_client()
        if supabase:
            user_record = get_user_from_db(supabase, user['email'])
            if not user_record:
                role = "guest"
                show_ui_guest(user)
                return
            role= user_record.get("role", "guest")
            if role == "admin":
                show_ui_admin(user)
            elif role == "user":
                show_ui_user(user)
            elif role == "guest":
                show_ui_guest(user)
            else:
                st.error(f"Unknown role: {role}. Please contact the administrator.")
        else:
            st.error("Could not connect to Supabase.")
    else:
        st.warning("Please log in with a verified email to access the app.")