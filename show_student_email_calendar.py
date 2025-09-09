import streamlit as st
import pandas as pd
import time

from supabase_integration import get_supabase_client, get_student_emails_from_db
from google_calendar import get_calendar_service, get_calendar_events

def create_information_table():
    supabase = get_supabase_client()
    student_emails=get_student_emails_from_db(supabase)
    calendar_service = get_calendar_service()
    if calendar_service:
        events = get_calendar_events(calendar_service)
    return student_emails, events

def process_time_record(event_record):
    if event_record.get("date"):
        return event_record.get("date"),"Unknown timezone"
    if event_record.get("dateTime"):
        return event_record.get("dateTime"),event_record.get("timeZone")
    
def process_attendee_record(attendee_record):
    email_list = [r.get('email') for r in attendee_record]
    return email_list
        
def match_attendee(name,event_title):
    name_parts=[w.lower() for w in name.split()]
    all_present = all(w in event_title.lower() for w in name_parts)
    return all_present

def match_email_list(list1,list2):
    matched=any(elem in list2 for elem in list1)
    return matched
    
def match_one_student_to_one_event(student_email_record,event,parent_match):
    student_full_name=student_email_record.get("full_name","")
    student_main_email=student_email_record.get("primary_sudent_email","")
    student_all_emails=student_email_record.get("student_emails",[])
    student_all_emails+=student_email_record.get("parent_emails",[])
    event_start_record=event.get("start",{})
    event_title=event.get("summary","")
    event_attendees_record=event.get("attendees",[])
    event_start_date, event_start_tz=process_time_record(event_start_record)
    event_attendees=process_attendee_record(event_attendees_record)
    match_name=match_attendee(student_full_name,event_title)
    match_student_email=match_email_list([student_main_email],event_attendees)
    match_parent_email=match_email_list(student_all_emails,event_attendees)
    
    return match_name, match_student_email, match_parent_email, event_start_date, event_start_tz, student_full_name,event_title

def match_one_student_to_events(student_email,events,parent_match):
    #st.write(f"Matching event for student {student_email}")
    for event in events:
        mn,mse,mpe,esd,est,sfn,et=match_one_student_to_one_event(student_email,event,parent_match)
        one_match=mn or mse
        if parent_match:
            one_match = one_match or mpe
            
        if one_match:
            match_value={}
            match_value["student"]=sfn
            match_value["event"]=et
            match_value["start_time"]=esd
            match_value["start_tz"]=est
            return match_value

def match_students_events(student_emails,events,parent_match=False):
    st.write("Matching in progress...")  
    matched_students=[]
    unmatched_students=[]
    for student_email in student_emails:
        one_match=match_one_student_to_events(student_email,events,parent_match)
        if one_match:
            matched_students.append(one_match)
        else:
            unmatched_students.append(student_email)
    return matched_students, unmatched_students

def show_student_email_calendar():
    start = time.perf_counter()
    with st.spinner("Fetching results from Calendar API…", show_time=True):
        student_emails,events=create_information_table()
    elapsed = time.perf_counter() - start
    duration = f"{elapsed*1000:.0f} ms" if elapsed < 1 else f"{elapsed:.2f} s"
    st.sidebar.write(f"Data fetch took {duration}")
    with st.expander("Student Events"):
        st.dataframe(student_emails)
        st.dataframe(events)
        for event in events[:5]:
            st.write(f"{event=}")
    start = time.perf_counter()
    with st.spinner("Fetching results from Calendar API…", show_time=True):
        matches,nonmatches=match_students_events(student_emails,events)
    elapsed = time.perf_counter() - start
    duration = f"{elapsed*1000:.0f} ms" if elapsed < 1 else f"{elapsed:.2f} s"
    st.sidebar.write(f"Match took {duration}")
    df_m=pd.DataFrame(matches)
    df_n=pd.DataFrame(nonmatches)
    df_m["URL"]="/show_search_page?q="+df_m['student']
    df_n["URL"]="/show_search_page?q="+df_n['full_name']
    
    with st.expander("Matches"):
        st.dataframe(df_m, column_config={"URL": st.column_config.LinkColumn("Pro page", display_text="GO to pro")})
    with st.expander("Non-Matches"):
        st.dataframe(df_n, column_config={"URL": st.column_config.LinkColumn("Pro page", display_text="GO to pro")})

    
    
if __name__ == "__main__":
    show_student_email_calendar()