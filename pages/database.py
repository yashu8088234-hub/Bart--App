import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

@st.cache_resource
def init_firestore():

    cred = credentials.Certificate(st.secrets["FIREBASE_KEY"])

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    return firestore.client()

db = init_firestore()
