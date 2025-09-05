import streamlit as st
import pandas as pd
from appointment_core import load_patients, load_doctor_schedule, get_available_slots, book_appointment
from langchain.llms import HuggingFaceHub

st.set_page_config(page_title="Appointment AI Agent", layout="wide")
st.title("Appointment Scheduling AI Agent")

# -----------------------------
# Load HuggingFace LLM
# -----------------------------
hf_token = st.secrets["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"]

llm = HuggingFaceHub(
    repo_id="google/flan-t5-small",
    huggingfacehub_api_token=hf_token,
    model_kwargs={"temperature": 0.0, "max_new_tokens": 100}
)

# -----------------------------
# Load data
# -----------------------------
patients_df = load_patients()
doctor_schedule = load_doctor_schedule()

# -----------------------------
# Appointment booking UI
# -----------------------------
st.subheader("Book Appointment")

patient_name = st.selectbox("Select Patient", patients_df['Name'].tolist())
doctor_name = st.selectbox("Select Doctor", doctor_schedule['Doctor'].unique())
date = st.date_input("Select Date")

available_slots = get_available_slots(doctor_schedule, doctor_name, date)
slot = st.selectbox("Select Slot", available_slots)

if st.button("Book Appointment"):
    if not slot:
        st.warning("No slots available.")
    else:
        success, msg = book_appointment(patient_name, doctor_name, date, slot, slot, doctor_schedule)
        if success:
            st.success(msg)
        else:
            st.error(msg)

# -----------------------------
# Ask AI Agent
# -----------------------------
st.subheader("Ask AI Agent about appointments")

user_input = st.text_area("Enter your query for the AI Agent:")

if st.button("Generate AI Response"):
    if not user_input.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Generating response..."):
            response = llm(user_input)
        st.markdown("**AI Response:**")
        st.write(response)
