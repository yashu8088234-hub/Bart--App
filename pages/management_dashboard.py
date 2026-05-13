import streamlit as st
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="mydatabase",
        user="postgres",
        password="",   # usually empty on Mac local setup
        port=5432
    )

    st.success("✅ Connected to PostgreSQL!")

except Exception as e:
    st.error(e)
