import os
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PATIENT_CSV = os.path.join(DATA_DIR, "patients_sample_50.csv")
DOCTOR_XLSX = os.path.join(DATA_DIR, "doctor_schedules_sample.xlsx")
BOOKINGS_XLSX = os.path.join(DATA_DIR, "bookings.xlsx")

def load_patients(path: str = PATIENT_CSV):
    """Load patient CSV"""
    return pd.read_csv(path)

def load_doctors_and_availability(path: str = DOCTOR_XLSX):
    """Load doctors and availability from Excel"""
    xls = pd.ExcelFile(path, engine='openpyxl')
    doctors = pd.read_excel(xls, "doctors")
    availability = pd.read_excel(xls, "availability")
    holidays = pd.read_excel(xls, "holidays")
    availability["booked"] = availability["booked"].astype(int)
    return doctors, availability, holidays

def search_patient(patients_df: pd.DataFrame, name: str, dob: str):
    """Lookup patient by name + DOB"""
    name = name.strip().lower()
    parts = name.split()
    matches = patients_df[
        (patients_df["dob"].astype(str) == dob) &
        (
            patients_df["first_name"].str.lower().isin(parts) |
            patients_df["last_name"].str.lower().isin(parts) |
            (patients_df["first_name"].str.lower() + " " + patients_df["last_name"].str.lower() == name)
        )
    ]
    if len(matches) == 0:
        return None
    else:
        return matches.iloc[0].to_dict()

def get_available_slots(availability_df, doctor_id, date_str):
    """Return available slots for a doctor on a given date"""
    day_slots = availability_df[
        (availability_df["doctor_id"] == doctor_id) &
        (availability_df["date"] == date_str) &
        (availability_df["booked"] == 0)
    ].copy().sort_values(["slot_start"])
    return day_slots[["slot_start","slot_end","location"]].to_dict(orient="records")
