import pandas as pd
from datetime import datetime, timedelta

# Load patients
def load_patients(path="patients_sample.csv"):
    return pd.read_csv(path)

# Load doctors and availability
def load_doctor_schedule(path="doctor_schedules_sample.xlsx"):
    return pd.read_excel(path)

# Get available slots for a doctor on a specific date
def get_available_slots(doctor_schedule, doctor_name, date):
    doc = doctor_schedule[doctor_schedule['Doctor'] == doctor_name]
    if doc.empty:
        return []
    slots = doc[doc['Date'] == pd.to_datetime(date)]['Slots'].values
    return slots[0] if len(slots) > 0 else []

# Book an appointment
def book_appointment(patient_name, doctor_name, date, slot_start, slot_end, doctor_schedule):
    df = doctor_schedule.copy()
    idx = df[(df['Doctor'] == doctor_name) & (df['Date'] == pd.to_datetime(date))].index
    if len(idx) == 0:
        return False, "Doctor not available on this date"
    idx = idx[0]
    slots = df.at[idx, 'Slots']
    if slot_start not in slots:
        return False, "Slot not available"
    slots.remove(slot_start)
    df.at[idx, 'Slots'] = slots
    df.to_excel("doctor_schedules_sample.xlsx", index=False)
    return True, f"Appointment booked for {patient_name} with {doctor_name} at {slot_start}"
