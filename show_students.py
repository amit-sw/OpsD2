import streamlit as st

import pandas as pd

from supabase_integration import get_supabase_client, get_student_emails_from_db
from show_events import show_events_one_student

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

@st.cache_data()
def get_student_information():
    supabase = get_supabase_client()
    student_email_list=get_student_emails_from_db(supabase)
    return student_email_list

def process_selected_rows(selected_row):

    if selected_row:
        #st.success(f"Got selected row: {selected_row}")
        pass
    else:
        st.error("Got empty row")
    student_name=selected_row['full_name']
    student_email=selected_row['primary_student_email']
    parent_email=selected_row['primary_parent_email']
    st.success(f"Now choosing: {student_name=}, {student_email=}, {parent_email=}")
    show_events_one_student(selected_row)

def choose_student_show_events():
    student_email_list = get_student_information()
    student_email_list_subset=student_email_list[:3]
    #print(f"Debug: {student_email_list_subset}")
    df = pd.DataFrame(student_email_list)
    df=df.drop(columns=["id","student_emails","parent_emails"])
    # UI
    search_text = st.text_input("Search", key="grid_q1", placeholder="Search across all columns…", label_visibility="hidden")
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(filter=True, sortable=True, resizable=True, flex=1, minWidth=120)
    gb.configure_grid_options(floatingFilter=True, animateRows=True)
    gb.configure_grid_options(quickFilterText=search_text, cacheQuickFilter=True)
    gb.configure_selection('single', use_checkbox=False, rowMultiSelectWithClick=False, suppressRowDeselection=False)
    grid_options = gb.build()
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        height=200,
        use_container_width=True,
        allow_unsafe_jscode=False,
        fit_columns_on_grid_load=True,
    )
        
    selected_rows_raw = grid_response.get("selected_rows", [])
    # st_aggrid may return a list[dict] or a pandas.DataFrame depending on version/config
    if isinstance(selected_rows_raw, pd.DataFrame):
        selected_rows = selected_rows_raw.to_dict(orient="records")
    elif isinstance(selected_rows_raw, list):
        selected_rows = selected_rows_raw
    else:
        selected_rows = []
    if selected_rows:
        process_selected_rows(selected_rows[0])