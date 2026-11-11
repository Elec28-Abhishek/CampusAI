import streamlit as st
import database
from data.campus import load_campus_data

st.set_page_config(page_title="CampusAI", page_icon="🏫", layout="wide")

st.title("🏫 CampusAI")
st.subheader("An Intelligent Campus Navigation & Academic Assistance System")
st.caption("Campus navigation configured for Veer Surendra Sai University of Technology (VSSUT), Burla, Sambalpur, Odisha.")

campus_data = load_campus_data()
campus_places = [
    node for node in campus_data["nodes"]
    if node["id"] != "vssut-campus" and node["category"] != "Road junction"
]
department_count = sum(node["category"] == "Department" for node in campus_places)
verified_pin_count = sum(node.get("coordinates_verified") is True for node in campus_places)
verified_edge_count = sum(edge.get("verified") is True for edge in campus_data.get("edges", []))

st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("🔐 Login"):
        st.switch_page("pages/1_Login.py")

with col2:
    if st.button("📝 Register"):
        st.switch_page("pages/2_Register.py")

st.divider()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Campus places", len(campus_places))
c2.metric("Departments", department_count)
c3.metric("Verified building pins", verified_pin_count)
c4.metric("Verified pedestrian links", verified_edge_count)

st.success("CampusAI Database Connected")
