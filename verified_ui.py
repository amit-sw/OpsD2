import streamlit as st
st.set_page_config(layout="wide")
from supabase_integration import get_supabase_client, get_user_from_db, get_students_from_db
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from show_events import show_events_all

def show_students_page():
    """Display the Students page content"""
    st.title("Students")
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    if not supabase:
        st.error("Could not connect to the database.")
        return
    
    # Add refresh button
    if st.button("Refresh Student List"):
        st.session_state.students_refreshed = True
    
    # Fetch student data from database
    students = get_students_from_db(supabase)
    
    if not students:
        st.info("No students found in the database.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(students)
    
    # Configure grid options
    st.subheader(f"Student List ({len(students)} students)")
    
    search_text = st.text_input("Search", key="student_grid_search", placeholder="Search students...", label_visibility="visible")
    
    # Configure AG Grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    # Enable per-column filters, sorting, and resizing
    gb.configure_default_column(filter=True, sortable=True, resizable=True, flex=1)
    gb.configure_column("full_name", headerName="Student Name", width=300)
    
    # Enable floating filters (client-side, per-column, live filter input boxes)
    gb.configure_grid_options(floatingFilter=True, animateRows=True)
    gb.configure_grid_options(quickFilterText=search_text, cacheQuickFilter=True)
    
    # Optional: set a sensible page size
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=25)
    grid_options = gb.build()
    
    # Render the grid
    AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        height=400,
        use_container_width=True,
        fit_columns_on_grid_load=True,
    )

def show_ui_core(user):
    name = user.get("name", "Unknown User")
    email = user.get("email", "Unknown Email")
    picture = user.get("picture", "")
    email_verified = user.get("email_verified", False)

    with st.sidebar:
        st.text(f"Welcome {name}\n {email}")
        if email_verified:
            st.success("Email is verified.")
        else:
            st.warning("Email is not verified.")
        if picture:
            st.image(picture, width=100)
            
        # Navigation tabs
        st.subheader("Navigation")
        tab = st.radio("Select Page", ["Calendar", "Students"], label_visibility="collapsed")
        
        if st.button("Log out"):
            st.logout()
    
    if tab == "Calendar":
        st.title("Club Ops Calendar Events")
        show_events_all()
    elif tab == "Students":
        show_students_page()



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