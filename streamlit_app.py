import os
import streamlit as st
from datetime import datetime
from langchain.llms import HuggingFaceHub
from appointment_core import load_patients, load_doctors_and_availability, search_patient, get_available_slots

st.set_page_config(page_title="Clinic Scheduling LangChain", layout="wide")
st.title("🗓️ Medical Appointment Scheduling Prototype")

# --- LangChain LLM Setup (Free) ---
llm = HuggingFaceHub(repo_id="google/flan-t5-small", model_kwargs={"temperature":0})

def llm_lookup_patient(name: str, dob: str):
    patients = load_patients()
    match = search_patient(patients, name, dob)
    if match:
        return (
            f"Found patient: {match['first_name']} {match['last_name']} (ID: {match['patient_id']})\n"
            f"Email: {match['email']}, Phone: {match['phone']}, City: {match['city']}\n"
            f"Preferred Doctor: {match['preferred_doctor_name']} at {match['preferred_location']}\n"
            f"Insurance: {match['insurance_carrier']}, Member ID: {match['insurance_member_id']}"
        )
    else:
        return f"No patient found. Create new patient: {name}"

def llm_list_doctor_slots(doctor_name: str, date_str: str):
    doctors, availability, _ = load_doctors_and_availability()
    doc = doctors[doctors["doctor_name"] == doctor_name].iloc[0]
    slots = get_available_slots(availability, doc["doctor_id"], date_str)
    return slots

# --- Streamlit UI ---
st.subheader("1) Patient Lookup")
name = st.text_input("Patient Name")
dob = st.date_input("Date of Birth")
if st.button("Lookup Patient"):
    st.text(llm_lookup_patient(name, dob.isoformat()))

st.subheader("2) Doctor Availability")
doctors_df, _, _ = load_doctors_and_availability()
doctor_name = st.selectbox("Select Doctor", doctors_df["doctor_name"].unique())
date_choice = st.date_input("Appointment Date", datetime.today())
if st.button("Show Slots"):
    slots = llm_list_doctor_slots(doctor_name, date_choice.isoformat())
    st.write(slots)
