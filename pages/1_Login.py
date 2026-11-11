import streamlit as st
import sqlite3
from utils.auth import hash_password, is_password_hash, verify_password

st.title("🔐 Login")

email=st.text_input("Email")

password=st.text_input("Password",type="password")

if st.button("Login"):

    conn=sqlite3.connect("database/campus.db")

    cur=conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=?", (email.strip(),))

    user=cur.fetchone()

    if user and verify_password(user[3], password):

        if not is_password_hash(user[3]):
            cur.execute(
                "UPDATE users SET password=? WHERE id=?",
                (hash_password(password), user[0]),
            )
            conn.commit()

        conn.close()

        st.session_state["user"]=user[1]

        st.session_state["role"]=user[4]

        st.success("Login Successful")

        st.switch_page("pages/3_Dashboard.py")

    else:

        conn.close()

        st.error("Invalid Email or Password")
