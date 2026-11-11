import streamlit as st

if "user" not in st.session_state:
    st.warning("Please login first")
    st.stop()

st.set_page_config(layout="wide")

st.title(f"Welcome {st.session_state['user']} 👋")

c1,c2,c3,c4=st.columns(4)

c1.metric("Buildings","10")

c2.metric("Departments","6")

c3.metric("Faculty","120")

c4.metric("Students","3500")

st.divider()

col1,col2,col3=st.columns(3)

if col1.button("🗺 Campus Navigation",use_container_width=True):
    st.switch_page("pages/4_Campus_Map.py")

if col2.button("📚 Study Planner",use_container_width=True):
    st.switch_page("pages/7_Study_Planner.py")

if col3.button("🤖 AI Assistant",use_container_width=True):
    st.switch_page("pages/8_AI_Assistant.py")