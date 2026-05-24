import streamlit as st
import joblib
import pandas as pd
import requests
import os

st.set_page_config(page_title="Assurance", layout="wide")

@st.cache_resource
def load_model():
    try:
        path = os.path.join(os.path.dirname(__file__), "model.pkl")
        return joblib.load(path), True
    except:
        return None, False

model_rf, model_charge = load_model()

coords = {
    "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73),
    "Bizerte": (37.27, 9.87), "Beja": (36.72, 9.18),
    "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97),
    "Gabes": (33.88, 10.09)
}
