import streamlit as st

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
        
def show_events_all():
    calendar_service = get_calendar_service()
    if calendar_service:
        refreshed_events = get_calendar_events(calendar_service)
        show_events(refreshed_events)
    else:
        st.error("calendar service not available")