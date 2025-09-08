import streamlit as st

#print(f"DEBUG: {st.secrets}")

for k in st.secrets:
    v=st.secrets[k]
    print(f"Debug {k=}, {v=}")