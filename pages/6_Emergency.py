import streamlit as st

st.title("🚨 Emergency Contacts")

st.table({
    "Department":[
        "Security",
        "Medical",
        "Fire",
        "Administration"
    ],
    "Phone":[
        "9437000001",
        "9437000002",
        "101",
        "0663-2430211"
    ]
})
