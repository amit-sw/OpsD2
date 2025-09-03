import streamlit as st
st.set_page_config(layout="wide")
from supabase_integration import get_supabase_client, get_user_from_db, get_students_from_db
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from google_calendar import get_calendar_service, get_events_for_emails
from datetime import datetime, timezone

from show_events import show_events_all

def find_closest_future_event(events):
    """Find the closest future event from a list of events.
    
    Args:
        events: List of calendar events
        
    Returns:
        The closest future event, or None if no future events
    """
    if not events:
        return None
        
    # Since we're already fetching only future events, we just need to sort by start time
    events_with_time = []
    
    for event in events:
        # Get event start time
        start_str = event.get('start', {}).get('dateTime')
        if not start_str:
            continue
            
        try:
            # Convert to timezone-aware datetime
            if 'Z' in start_str:
                # UTC time with Z suffix
                start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            elif '+' in start_str or '-' in start_str and 'T' in start_str:
                # Already has timezone info
                start_time = datetime.fromisoformat(start_str)
            else:
                # No timezone info, assume UTC
                start_time = datetime.fromisoformat(start_str).replace(tzinfo=timezone.utc)
                
            events_with_time.append((start_time, event))
        except ValueError:
            # Skip events with invalid datetime format
            continue
    
    # Sort by start time
    if events_with_time:
        events_with_time.sort(key=lambda x: x[0])  # Sort by datetime
        return events_with_time[0][1]  # Return the closest event
    
    return None

def parse_event_datetime(date_str):
    """Parse event datetime string to datetime object."""
    if not date_str:
        return None
        
    try:
        # Handle different datetime formats
        if 'Z' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        elif '+' in date_str or '-' in date_str and 'T' in date_str:
            # Already has timezone info
            dt = datetime.fromisoformat(date_str)
        else:
            # No timezone info, assume UTC
            dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None
        
def calculate_days_until_event(event):
    """Calculate days until event.
    
    Returns:
        int: Number of days until event, or None if no valid event
    """
    if not event:
        return None
        
    start_str = event.get('start', {}).get('dateTime')
    if not start_str:
        return None
        
    start_dt = parse_event_datetime(start_str)
    if not start_dt:
        return None
        
    # Calculate days difference
    now = datetime.now(timezone.utc)
    delta = start_dt - now
    
    # Return days as integer
    return max(0, delta.days)

def format_event_datetime(event):
    """Format event date and time for display."""
    if not event:
        return "None"
        
    start_str = event.get('start', {}).get('dateTime')
    if not start_str:
        return "None"
        
    start_dt = parse_event_datetime(start_str)
    if not start_dt:
        return "None"
        
    return start_dt.strftime('%b %d, %Y - %I:%M %p')

def get_event_title(event):
    """Get event title."""
    if not event:
        return "None"
        
    return event.get('summary', 'Untitled Event')

def show_students_page():
    """Display the Students page content"""
    st.title("Students")
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    if not supabase:
        st.error("Could not connect to the database.")
        return
    
    # Create Google Calendar service
    with st.spinner("Connecting to Google Calendar..."):
        calendar_service = get_calendar_service()
    
    if not calendar_service:
        st.warning("Could not connect to Google Calendar. Event information will not be available.")
    
    # Add refresh button
    if st.button("Refresh Student List"):
        st.session_state.students_refreshed = True
    
    # Fetch student data from database
    with st.spinner("Fetching students from database..."):
        students = get_students_from_db(supabase)
    
    if not students:
        st.info("No students found in the database.")
        return
    
    # Process student data to include closest events
    processed_students = []
    
    # Get all unique emails across all students first
    all_student_emails = set()
    for student in students:
        student_emails = student.get("student_emails", []) or []
        parent_emails = student.get("parent_emails", []) or []
        all_student_emails.update(student_emails + parent_emails)
    
    # Get events for all emails in a single API call
    all_email_events = {}
    with st.spinner("Finding upcoming events for all students..."):
        if calendar_service and all_student_emails:
            # This now only fetches future events for next month
            all_email_events = get_events_for_emails(calendar_service, list(all_student_emails))
    
    # Process each student
    with st.spinner("Processing student data..."):
        for student in students:
            # Extract student and parent emails
            student_emails = student.get("student_emails", []) or []
            parent_emails = student.get("parent_emails", []) or []
            student_specific_emails = student_emails + parent_emails
            
            # Get events for this student
            all_student_events = []
            for email in student_specific_emails:
                if email in all_email_events:
                    all_student_events.extend(all_email_events.get(email, []))
            
            # Find closest future event
            closest_event = find_closest_future_event(all_student_events)
            
            # Add data to processed students with the requested columns
            processed_students.append({
                "full_name": student.get("full_name", "Unknown"),
                "next_class": calculate_days_until_event(closest_event),
                "date_time": format_event_datetime(closest_event),
                "event_name": get_event_title(closest_event)
            })
    
    # Sort students by next_class, with None values at the end
    processed_students.sort(key=lambda x: (x["next_class"] is None, x["next_class"] if x["next_class"] is not None else float('inf')))
    
    # Convert to DataFrame for display
    df = pd.DataFrame(processed_students)
    
    # Configure grid options
    st.subheader(f"Student List ({len(processed_students)} students)")
    
    search_text = st.text_input("Search", key="student_grid_search", placeholder="Search students...", label_visibility="visible")
    
    # Configure AG Grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    # Enable per-column filters, sorting, and resizing
    gb.configure_default_column(filter=True, sortable=True, resizable=True, flex=1)
    gb.configure_column("full_name", headerName="Student Name", width=300)
    gb.configure_column("next_class", headerName="Next Class (Days)", width=150, type=["numericColumn", "numberColumnFilter"])
    gb.configure_column("date_time", headerName="Date and Time", width=200)
    gb.configure_column("event_name", headerName="Event Name", width=250)
    
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