import os
import uuid
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PATIENT_CSV = os.path.join(DATA_DIR, "patients_sample_50.csv")
DOCTOR_XLSX = os.path.join(DATA_DIR, "doctor_schedules_sample.xlsx")
BOOKINGS_XLSX = os.path.join(DATA_DIR, "bookings.xlsx")
COMM_LOG_CSV = os.path.join(DATA_DIR, "communications_log.csv")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Load patients
def load_patients(path: str = PATIENT_CSV):
    return pd.read_csv(path)

# Load doctors and availability
def load_doctors_and_availability(path: str = DOCTOR_XLSX):
    xls = pd.ExcelFile(path, engine='openpyxl')
    doctors = pd.read_excel(xls, "doctors")
    availability = pd.read_excel(xls, "availability")
    holidays = pd.read_excel(xls, "holidays")
    availability["booked"] = availability["booked"].astype(int)
    return doctors, availability, holidays

# Search patient
def search_patient(patients_df: pd.DataFrame, name: str, dob: str):
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

# Get available slots
def get_available_slots(availability_df, doctor_id, date_str):
    day_slots = availability_df[
        (availability_df["doctor_id"] == doctor_id) &
        (availability_df["date"] == date_str) &
        (availability_df["booked"] == 0)
    ].copy().sort_values(["slot_start"])
    return day_slots[["slot_start","slot_end","location"]].to_dict(orient="records")

# Book appointment
def book_appointment(patient: dict, doctor_row: dict, date_str: str, slot_start: str, slot_end: str):
    doctors, availability, holidays = load_doctors_and_availability()
    # Mark slot booked
    idx = availability.index[
        (availability["doctor_id"] == doctor_row["doctor_id"]) &
        (availability["date"] == date_str) &
        (availability["slot_start"] == slot_start) &
        (availability["slot_end"] == slot_end) &
        (availability["booked"] == 0)
    ]
    if len(idx) == 0:
        raise ValueError("Slot no longer available.")
    availability.loc[idx, "booked"] = 1
    # Save availability back
    with pd.ExcelWriter(DOCTOR_XLSX, engine="openpyxl") as writer:
        doctors.to_excel(writer, sheet_name="doctors", index=False)
        availability.to_excel(writer, sheet_name="availability", index=False)
        holidays.to_excel(writer, sheet_name="holidays", index=False)
    # Append booking
    booking_id = str(uuid.uuid4())[:8]
    book_row = pd.DataFrame([{
        "booking_id": booking_id,
        "patient_id": patient.get("patient_id","NEW"),
        "patient_name": f"{patient.get('first_name','')} {patient.get('last_name','')}".strip(),
        "doctor_id": doctor_row["doctor_id"],
        "doctor_name": doctor_row["doctor_name"],
        "date": date_str,
        "slot_start": slot_start,
        "slot_end": slot_end,
        "location": doctor_row["location"],
        "status": "CONFIRMED",
        "created_at": datetime.now().isoformat(timespec="seconds")
    }])
    if os.path.exists(BOOKINGS_XLSX):
        existing = pd.read_excel(BOOKINGS_XLSX, sheet_name="bookings")
        all_rows = pd.concat([existing, book_row], ignore_index=True)
        with pd.ExcelWriter(BOOKINGS_XLSX, engine="openpyxl") as writer:
            all_rows.to_excel(writer, sheet_name="bookings", index=False)
    else:
        with pd.ExcelWriter(BOOKINGS_XLSX, engine="openpyxl") as writer:
            book_row.to_excel(writer, sheet_name="bookings", index=False)
    return booking_id

# Send message (simulated)
def send_message(channel: str, to: str, subject: str, message: str, booking_id: str=None):
    row = pd.DataFrame([{
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "channel": channel,
        "to": to,
        "subject": subject,
        "message": message,
        "booking_id": booking_id or ""
    }])
    if os.path.exists(COMM_LOG_CSV):
        existing = pd.read_csv(COMM_LOG_CSV)
        all_rows = pd.concat([existing, row], ignore_index=True)
        all_rows.to_csv(COMM_LOG_CSV, index=False)
    else:
        row.to_csv(COMM_LOG_CSV, index=False)

# Template path
def get_template_path(name: str):
    path = os.path.join(TEMPLATE_DIR, name)
    if os.path.exists(path):
        return path
    raise FileNotFoundError(f"Template not found: {name}")

# Admin report export
def export_admin_report():
    """Export patients, doctors, availability, bookings, and communications to Excel."""
    report_path = os.path.join(os.path.dirname(__file__), f"admin_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    
    doctors, availability, holidays = load_doctors_and_availability()
    patients = load_patients()
    bookings = pd.read_excel(BOOKINGS_XLSX, sheet_name="bookings") if os.path.exists(BOOKINGS_XLSX) else pd.DataFrame()
    communications = pd.read_csv(COMM_LOG_CSV) if os.path.exists(COMM_LOG_CSV) else pd.DataFrame()
    
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        patients.to_excel(writer, sheet_name="patients", index=False)
        doctors.to_excel(writer, sheet_name="doctors", index=False)
        availability.to_excel(writer, sheet_name="availability", index=False)
        holidays.to_excel(writer, sheet_name="holidays", index=False)
        bookings.to_excel(writer, sheet_name="bookings", index=False)
        communications.to_excel(writer, sheet_name="communications", index=False)
    
    return report_path
