import streamlit as st
st.set_page_config(layout="wide")
from supabase_integration import get_supabase_client, get_calendar_events_from_db, update_calendar_events_in_db, get_user_from_db
from google_calendar import get_calendar_service, get_calendar_events
from datetime import datetime
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from st_aggrid.shared import JsCode

def show_events(events):
    #if events:
    #    st.dataframe(events)
    #else:
    #    st.write("No events to display.")
    new_list=[]
    for event in events:
        #st.write(event)
        if event.get("attendees") and len(event["attendees"])>0:
            attendees = ", ".join([attendee.get("email", "N/A") for attendee in event["attendees"]])
            new_list.append({
                "attendees": attendees,
                "Title": event.get("summary", "No Title"),
                "start": event["start"].get("dateTime", event["start"].get("date", "N/A")),
                #"end": event["end"].get("dateTime", event["end"].get("date", "N/A")),

                #"created": event.get("created", "N/A"),
                #"updated": event.get("updated", "N/A"),
                #"id": event.get("id", "N/A"),
            })
    if new_list:
        # Convert to DataFrame for the grid
        df = pd.DataFrame(new_list)

        search_text = st.text_input("Search", key="grid_q", placeholder="Search across all columns…", label_visibility="hidden")

        # Configure AG Grid options
        gb = GridOptionsBuilder.from_dataframe(df)
        # Enable per-column filters, sorting, and resizing
        gb.configure_default_column(filter=True, sortable=True, resizable=True, flex=1, minWidth=120)
        gb.configure_column("attendees", flex=4, minWidth=400)
        gb.configure_column("Title", flex=1, minWidth=100)
        gb.configure_column("start", flex=1, minWidth=50)
        # Enable floating filters (client-side, per-column, live filter input boxes)
        gb.configure_grid_options(floatingFilter=True, animateRows=True)
        row_style = JsCode(
            """
            function(params) {
              try {
                var v = params.data && params.data.start;
                if (!v) { return null; }
                var d = new Date(v);
                if (isNaN(d)) { return null; }
                var now = new Date();
                if (d < now) {
                  return { 'backgroundColor': '#fff6f6' }; // light red for past
                } else {
                  return { 'backgroundColor': '#f6fff6' }; // light green for future
                }
              } catch (e) {
                return null;
              }
            }
            """
        )
        gb.configure_grid_options(getRowStyle=row_style)
        gb.configure_grid_options(quickFilterText=search_text, cacheQuickFilter=True)
        # Optional: set a sensible page size
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100)
        grid_options = gb.build()

        # Render the grid (no server reruns needed for filtering)
        AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            height=400,
            use_container_width=True,
            allow_unsafe_jscode=True,
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
        if st.button("Log out"):
            st.logout()

    st.title("Club Ops Calendar Events")

    supabase = get_supabase_client()

    if st.sidebar.button("Refresh"):
        st.session_state.refreshed_events = None
        start=datetime.now()
        calendar_service = get_calendar_service()
        if calendar_service:
            refreshed_events = get_calendar_events(calendar_service)
            st.session_state.refreshed_events = refreshed_events
            end = datetime.now()
            duration = end - start
            st.sidebar.success(f"Fetched {len(refreshed_events)} in {duration}.")

    if 'refreshed_events' in st.session_state and st.session_state.refreshed_events is not None:
        #st.header("Fresh Events from Google Calendar")
        refreshed_events = st.session_state.refreshed_events
        show_events(refreshed_events)

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