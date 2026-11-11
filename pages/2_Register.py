import streamlit as st # type: ignore
import sqlite3
from utils.auth import hash_password

st.title("📝 Student Registration")

name=st.text_input("Name")
email=st.text_input("Email")
password=st.text_input("Password",type="password")

role=st.selectbox(
"Role",
["Student","Faculty"]
)

if st.button("Register"):

    if not name.strip() or not email.strip() or not password:
        st.error("Enter your name, email, and password to register.")
        st.stop()

    conn=sqlite3.connect("database/campus.db")

    cur=conn.cursor()

    try:

        cur.execute("""

        INSERT INTO users(name,email,password,role)

        VALUES(?,?,?,?)

        """,(name.strip(),email.strip(),hash_password(password),role))

        conn.commit()

        st.success("Registration Successful")

    except sqlite3.IntegrityError:

        st.error("Email already exists")

    conn.close()
