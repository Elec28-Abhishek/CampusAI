import streamlit as st

from data.campus import load_campus_data


st.set_page_config(page_title="VSSUT Campus Data", layout="wide")
st.title("📊 VSSUT Campus Data Status")
st.caption("Veer Surendra Sai University of Technology · Burla, Sambalpur, Odisha")

campus = load_campus_data()
locations = [
    node for node in campus["nodes"]
    if node["id"] != "vssut-campus" and node["category"] != "Road junction"
]
departments = sum(node["category"] == "Department" for node in locations)
verified_pins = sum(node.get("coordinates_verified") is True for node in locations)
verified_edges = sum(edge.get("verified") is True for edge in campus.get("edges", []))
sample_edges = sum(edge.get("verified") is not True for edge in campus.get("edges", []))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Listed campus places", len(locations))
col2.metric("Departments", departments)
col3.metric("Verified building pins", verified_pins)
col4.metric("Verified road connections", verified_edges)

if sample_edges:
    st.warning(f"The campus graph includes {sample_edges} sample connections. Their distances are illustrative and must not be treated as confirmed walking routes.")
else:
    st.success("All stored graph connections are marked verified by a campus administrator.")

unlocated = [node["name"] for node in locations if node.get("latitude") is None or node.get("longitude") is None]
if unlocated:
    st.info(f"{len(unlocated)} campus places still need verified coordinates.")
    st.write(", ".join(unlocated))
else:
    st.success("All listed campus places have coordinates.")
