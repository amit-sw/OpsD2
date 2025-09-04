import streamlit as st

from google_calendar import get_calendar_service, get_calendar_events

from datetime import datetime
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from st_aggrid.shared import JsCode


def show_events(events,grid_name='grid_q'):
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

        search_text = st.text_input("Search", key=grid_name, placeholder="Search across all columns…", label_visibility="hidden")

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
        #gb.configure_grid_options(domLayout='autoHeight')
        # Optional: set a sensible page size
        #gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10000)
        grid_options = gb.build()

        # Render the grid (no server reruns needed for filtering)
        AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            # height controlled by autoHeight
            height=400,
            use_container_width=True,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
        )

def filtered_events(event_list, student_info):
    """Filter events to those that match the student's/parent's email or the student's name in the title.

    Args:
        event_list (list[dict]): Each dict has keys like 'attendees' (comma-separated emails), 'Title', 'start'.
        student_info (dict): Has keys 'full_name', 'primary_student_email', 'primary_parent_email'.

    Returns:
        list[dict]: Filtered subset of event_list.
    """
    if not isinstance(event_list, list) or not student_info:
        return event_list

    # Normalize student data
    full_name = (student_info.get("full_name") or "").strip()
    student_email = (student_info.get("primary_student_email") or "").strip().lower()
    parent_email = (student_info.get("primary_parent_email") or "").strip().lower()

    name_words = [w.lower() for w in full_name.split() if w]

    filtered = []
    for ev in event_list:
        #print(f"\nDEBUG10: {ev=}\n{full_name=},{student_email=},{parent_email=},{name_words=}")
        try:
            attendees = ev.get("attendees", "")
            attendee_emails = [a['email'].lower() for a in attendees]

            title = ev.get("summary", "")
            title_lower = title.lower()

            # Rule 1: any attendee email matches student's or parent's email
            email_match = False
            if student_email or parent_email:
                targets = {e for e in (student_email, parent_email) if e}
                email_match = any(a in targets for a in attendee_emails)
            #print(f"DEBUG11: {email_match=},{student_email=},{parent_email=},{targets=},{attendee_emails=}")

            # Rule 2: every word in the student's name appears somewhere in the Title
            name_match = False
            if name_words:
                name_match = all(word in title_lower for word in name_words)
            #print(f"DEBUG12: {name_match=}, {title_lower=}, {name_words=}")

            if email_match or name_match:
                filtered.append(ev)
        except Exception as e:
            # If anything is malformed, just skip filtering for that row and include it only if clearly matched above
            # (No-op here; the event won't be included unless one of the rules set a match)
            #print(f"DEBUG51: Caught exception {e}")
            pass

    return filtered

def show_events_one_student(student_info):
    calendar_service = get_calendar_service()
    if calendar_service:
        refreshed_events = get_calendar_events(calendar_service)
        #refreshed_events = refreshed_events[:5]
        events=filtered_events(refreshed_events,student_info)
        show_events(events,grid_name='grid_21')
        #st.divider()
        #show_events(refreshed_events,grid_name='grid_22')
    else:
        st.error("calendar service not available")
            
def show_events_all():
    calendar_service = get_calendar_service()
    if calendar_service:
        refreshed_events = get_calendar_events(calendar_service)
        show_events(refreshed_events)
    else:
        st.error("calendar service not available")