import os
import streamlit as st
from datetime import datetime
from langchain.llms import HuggingFaceHub
from appointment_core import (
    load_patients, load_doctors_and_availability, search_patient,
    get_available_slots, book_appointment, send_message,
    get_template_path, export_admin_report
)

st.set_page_config(page_title="Clinic Scheduling MVP", layout="wide")
st.title("🗓️ Medical Appointment Scheduling MVP")

# LLM Setup
llm = HuggingFaceHub(repo_id="google/flan-t5-small", model_kwargs={"temperature":0})

# --- Admin Section ---
with st.sidebar:
    st.header("Admin")
    if st.button("Export Admin Report"):
        path = export_admin_report()
        st.success(f"Admin report generated: {os.path.basename(path)}")
        with open(path, "rb") as f:
            st.download_button("Download Admin Report", f, file_name=os.path.basename(path))

# --- 1) Patient Lookup ---
st.subheader("1) Patient Lookup")
name = st.text_input("Patient Name")
dob = st.date_input("Date of Birth")
if st.button("Lookup Patient"):
    patients = load_patients()
    match = search_patient(patients, name, dob.isoformat())
    if match:
        st.success(f"Found patient: {match['first_name']} {match['last_name']} (ID: {match['patient_id']})")
        st.session_state["patient"] = match
    else:
        st.info("New patient detected.")
        st.session_state["patient"] = {"name": name, "dob": dob.isoformat(), "patient_id":"NEW",
                                       "first_name": name.split()[0], "last_name":" ".join(name.split()[1:])}

# --- 2) Doctor Availability & Booking ---
if "patient" in st.session_state:
    st.subheader("2) Doctor Availability")
    doctors, availability, _ = load_doctors_and_availability()
    doctor_name = st.selectbox("Select Doctor", doctors["doctor_name"].unique())
    date_choice = st.date_input("Appointment Date", datetime.today())
    
    if st.button("Show Available Slots"):
        doc = doctors[doctors["doctor_name"] == doctor_name].iloc[0]
        slots = get_available_slots(availability, doc["doctor_id"], date_choice.isoformat())
        if not slots:
            st.warning("No slots available.")
        else:
            slot_labels = [f"{s['slot_start']}-{s['slot_end']} @ {s['location']}" for s in slots]
            pick = st.selectbox("Select Slot", slot_labels)
            pick_idx = slot_labels.index(pick)
            chosen = slots[pick_idx]

            if st.button("Book Appointment"):
                booking_id = book_appointment(st.session_state["patient"], doc, date_choice.isoformat(), chosen["slot_start"], chosen["slot_end"])
                st.success(f"Appointment booked! ID: {booking_id}")

                # Send simulated reminder
                send_message("EMAIL", st.session_state["patient"].get("email","unknown@example.com"), "Appointment Confirmed",
                             f"Your appointment is confirmed on {date_choice} at {chosen['slot_start']} with {doc['doctor_name']}.", booking_id)
                st.info("Reminder logged in communications_log.csv")

                # Download Forms
                intake = get_template_path("intake_form_template.html")
                consent = get_template_path("consent_form_template.html")
                with open(intake,"rb") as f1, open(consent,"rb") as f2:
                    st.download_button("Download Intake Form", f1, file_name="intake_form.html")
                    st.download_button("Download Consent Form", f2, file_name="consent_form.html")
