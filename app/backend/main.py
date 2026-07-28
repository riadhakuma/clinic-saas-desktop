import os
import sys
import csv
import io
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.backend.database import get_db_connection, init_db
from app.backend.models import (
    DoctorCreate, DoctorLogin, PatientCreate, PatientPhotoUpdate,
    AppointmentCreate, AppointmentStatusUpdate, SettingUpdate, LicenseActivate,
    MedicalRecordCreate
)
from app.backend.whatsapp import generate_whatsapp_link, clean_algerian_phone
from app.backend.license import get_machine_hwid, parse_and_verify_key

app = FastAPI(title="Clinic SaaS Platform", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

# --- LICENSE & TRIAL ENDPOINTS ---
@app.get("/api/license/status")
def get_license_status():
    conn = get_db_connection()
    hwid = get_machine_hwid()
    
    key_row = conn.execute("SELECT value FROM settings WHERE key = 'license_key'").fetchone()
    clinic_row = conn.execute("SELECT value FROM settings WHERE key = 'clinic_name'").fetchone()
    block_row = conn.execute("SELECT value FROM settings WHERE key = 'is_blocked'").fetchone()
    trial_start_row = conn.execute("SELECT value FROM settings WHERE key = 'trial_activated_at'").fetchone()

    saved_key = key_row['value'] if key_row else ""
    clinic_name = clinic_row['value'] if clinic_row else ""
    is_blocked = (block_row['value'] == '1') if block_row else False
    trial_start_iso = trial_start_row['value'] if trial_start_row else ""

    conn.close()

    if is_blocked:
        return {
            "hwid": hwid,
            "is_activated": False,
            "is_blocked": True,
            "message": "Cette machine a été bloquée par le vendeur master admin.",
            "remaining_seconds": 0
        }

    if not saved_key:
        return {
            "hwid": hwid,
            "is_activated": False,
            "is_blocked": False,
            "clinic_name": clinic_name,
            "tier": "NONE",
            "is_admin": False,
            "remaining_seconds": 0
        }

    verification = parse_and_verify_key(hwid, saved_key, db_clinic_name=clinic_name, trial_start_iso=trial_start_iso)

    return {
        "hwid": hwid,
        "is_activated": verification["is_valid"],
        "is_blocked": False,
        "clinic_name": verification.get("clinic_name", clinic_name),
        "tier": verification.get("tier", "STANDARD"),
        "is_admin": verification.get("is_admin", False),
        "is_trial": verification.get("is_trial", False),
        "remaining_seconds": verification.get("remaining_seconds"),
        "reason": verification.get("reason", ""),
        "license_key": saved_key
    }

@app.post("/api/license/activate")
def activate_license(payload: LicenseActivate):
    conn = get_db_connection()
    hwid = get_machine_hwid()
    
    clinic_row = conn.execute("SELECT value FROM settings WHERE key = 'clinic_name'").fetchone()
    current_clinic = clinic_row['value'] if clinic_row else ""

    verification = parse_and_verify_key(hwid, payload.license_key, db_clinic_name=current_clinic, input_clinic_name=payload.clinic_name)

    if not verification["is_valid"]:
        conn.close()
        raise HTTPException(status_code=400, detail=verification.get("reason", "Clé de licence invalide"))

    new_clinic_name = verification["clinic_name"]

    conn.execute("UPDATE settings SET value = ? WHERE key = 'license_key'", (payload.license_key,))
    conn.execute("UPDATE settings SET value = ? WHERE key = 'clinic_name'", (new_clinic_name,))
    
    if verification.get("is_trial"):
        now_iso = datetime.now().isoformat()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('trial_activated_at', ?)", (now_iso,))

    conn.commit()
    conn.close()

    return {
        "message": "Licence activée avec succès !",
        "tier": verification["tier"],
        "clinic_name": new_clinic_name,
        "is_admin": verification.get("is_admin", False),
        "is_trial": verification.get("is_trial", False),
        "remaining_seconds": verification.get("remaining_seconds")
    }

# --- DOCTOR AUTHENTICATION & PORTAL ENDPOINTS ---
@app.post("/api/auth/doctor-login")
def doctor_login(payload: DoctorLogin):
    conn = get_db_connection()
    doc = conn.execute("SELECT * FROM doctors WHERE access_pin = ?", (payload.access_pin.strip(),)).fetchone()
    conn.close()
    
    if not doc:
        raise HTTPException(status_code=401, detail="Code PIN Médecin incorrect")
    
    return {
        "id": doc["id"],
        "name": doc["name"],
        "specialty": doc["specialty"],
        "phone": doc["phone"],
        "access_pin": doc["access_pin"]
    }

@app.get("/api/doctor/{doctor_id}/agenda")
def get_doctor_agenda(doctor_id: int):
    conn = get_db_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    
    appointments = conn.execute('''
        SELECT a.id, a.appointment_date, a.time_slot, a.status, a.notes,
               p.id as patient_id, p.full_name as patient_name, p.phone as patient_phone,
               p.gender, p.blood_type, p.photo_data
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = ? AND a.appointment_date >= ?
        ORDER BY a.appointment_date ASC, a.time_slot ASC
    ''', (doctor_id, today)).fetchall()
    
    conn.close()
    return [dict(app) for app in appointments]

@app.get("/api/doctor/{doctor_id}/notifications")
def get_doctor_notifications(doctor_id: int):
    conn = get_db_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    
    count = conn.execute('''
        SELECT COUNT(*) as count FROM appointments
        WHERE doctor_id = ? AND appointment_date = ? AND status = 'En attente'
    ''', (doctor_id, today)).fetchone()['count']
    
    conn.close()
    return {"count": count, "message": f"Vous avez {count} rendez-vous en attente aujourd'hui."}

# --- MEDICAL RECORDS & PRESCRIPTIONS ENDPOINTS ---
@app.post("/api/medical-records")
def create_medical_record(payload: MedicalRecordCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO medical_records (patient_id, doctor_id, diagnosis, prescription)
        VALUES (?, ?, ?, ?)
    ''', (payload.patient_id, payload.doctor_id, payload.diagnosis, payload.prescription))
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": record_id, "message": "Ordonnance et dossier médical enregistrés avec succès."}

@app.get("/api/medical-records/patient/{patient_id}")
def get_patient_medical_records(patient_id: int):
    conn = get_db_connection()
    records = conn.execute('''
        SELECT r.id, r.diagnosis, r.prescription, r.created_at,
               d.name as doctor_name, d.specialty as doctor_specialty
        FROM medical_records r
        JOIN doctors d ON r.doctor_id = d.id
        WHERE r.patient_id = ?
        ORDER BY r.created_at DESC
    ''', (patient_id,)).fetchall()
    
    conn.close()
    return [dict(r) for r in records]

# --- DASHBOARD & GENERAL ENDPOINTS ---
@app.get("/api/dashboard")
def get_dashboard_stats():
    conn = get_db_connection()
    today = datetime.now().strftime("%Y-%m-%d")

    total_patients = conn.execute("SELECT COUNT(*) as count FROM patients").fetchone()['count']
    total_doctors = conn.execute("SELECT COUNT(*) as count FROM doctors").fetchone()['count']
    today_appointments = conn.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ?", (today,)).fetchone()['count']
    pending_appointments = conn.execute("SELECT COUNT(*) as count FROM appointments WHERE status = 'En attente'").fetchone()['count']

    appointments = conn.execute('''
        SELECT a.id, a.appointment_date, a.time_slot, a.status, a.notes, a.whatsapp_sent,
               p.full_name as patient_name, p.phone as patient_phone, p.blood_type,
               d.name as doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.appointment_date DESC, a.time_slot ASC
        LIMIT 20
    ''').fetchall()

    conn.close()
    return {
        "stats": {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "today_appointments": today_appointments,
            "pending_appointments": pending_appointments
        },
        "recent_appointments": [dict(app) for app in appointments]
    }

# --- DOCTORS ENDPOINTS ---
@app.get("/api/doctors")
def get_doctors():
    conn = get_db_connection()
    doctors = conn.execute("SELECT * FROM doctors ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(doc) for doc in doctors]

@app.post("/api/doctors")
def create_doctor(doc: DoctorCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    pin = doc.access_pin or f"DOC-{datetime.now().microsecond % 9000 + 1000}"
    
    cursor.execute(
        "INSERT INTO doctors (name, specialty, phone, access_pin) VALUES (?, ?, ?, ?)",
        (doc.name, doc.specialty, doc.phone, pin)
    )
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": doc_id, "access_pin": pin, "message": "Médecin ajouté avec succès"}

# --- PATIENTS & MEDICAL CARDS ENDPOINTS ---
@app.get("/api/patients")
def get_patients():
    conn = get_db_connection()
    patients = conn.execute("SELECT * FROM patients ORDER BY full_name ASC").fetchall()
    conn.close()
    return [dict(p) for p in patients]

@app.post("/api/patients")
def create_patient(p: PatientCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (full_name, phone, gender, blood_type, photo_data, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (p.full_name, p.phone, p.gender, p.blood_type, p.photo_data, p.notes)
    )
    patient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": patient_id, "message": "Patient ajouté avec succès"}

@app.post("/api/patients/{patient_id}/photo")
def upload_patient_photo(patient_id: int, payload: PatientPhotoUpdate):
    conn = get_db_connection()
    conn.execute("UPDATE patients SET photo_data = ? WHERE id = ?", (payload.photo_data, patient_id))
    conn.commit()
    conn.close()
    return {"message": "Photo de la carte médicale mise à jour"}

@app.get("/api/patients/{patient_id}")
def get_patient_detail(patient_id: int):
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    return dict(patient)

# --- APPOINTMENTS ENDPOINTS ---
@app.post("/api/appointments")
def create_appointment(app_data: AppointmentCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, notes) VALUES (?, ?, ?, ?, ?)",
        (app_data.patient_id, app_data.doctor_id, app_data.appointment_date, app_data.time_slot, app_data.notes)
    )
    app_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": app_id, "message": "Rendez-vous créé avec succès"}

@app.put("/api/appointments/{app_id}/status")
def update_appointment_status(app_id: int, payload: AppointmentStatusUpdate):
    conn = get_db_connection()
    conn.execute("UPDATE appointments SET status = ? WHERE id = ?", (payload.status, app_id))
    conn.commit()
    conn.close()
    return {"message": "Statut mis à jour"}

# --- WHATSAPP LINK GENERATOR ---
@app.get("/api/whatsapp/link/{app_id}")
def get_whatsapp_link(app_id: int, lang: str = "fr"):
    conn = get_db_connection()
    
    app_row = conn.execute('''
        SELECT a.id, a.appointment_date, a.time_slot,
               p.full_name as patient_name, p.phone as patient_phone,
               d.name as doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.id = ?
    ''', (app_id,)).fetchone()

    if not app_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")

    clinic_name_row = conn.execute("SELECT value FROM settings WHERE key = 'clinic_name'").fetchone()
    clinic_name = clinic_name_row['value'] if clinic_name_row else "Clinique Médicale"

    template_key = 'msg_template_ar' if lang == 'ar' else 'msg_template_fr'
    template_row = conn.execute("SELECT value FROM settings WHERE key = ?", (template_key,)).fetchone()
    template = template_row['value'] if template_row else ""

    conn.execute("UPDATE appointments SET whatsapp_sent = 1 WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()

    result = generate_whatsapp_link(
        phone=app_row['patient_phone'],
        patient_name=app_row['patient_name'],
        doctor_name=app_row['doctor_name'],
        date_str=app_row['appointment_date'],
        time_str=app_row['time_slot'],
        clinic_name=clinic_name,
        custom_template=template
    )

    return result

# --- CSV DATA EXPORT ENDPOINT ---
@app.get("/api/export/csv")
def export_csv():
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.id, p.full_name as patient, p.phone, d.name as doctor,
               a.appointment_date, a.time_slot, a.status, a.notes
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.appointment_date DESC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Patient", "Téléphone", "Médecin", "Date", "Heure", "Statut", "Notes"])
    
    for row in appointments:
        writer.writerow([row["id"], row["patient"], row["phone"], row["doctor"], row["appointment_date"], row["time_slot"], row["status"], row["notes"]])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=rendez_vous_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# --- VENDOR ADMIN CONTROL ENDPOINTS ---
@app.post("/api/admin/block")
def toggle_block_machine(block: bool = True):
    conn = get_db_connection()
    conn.execute("UPDATE settings SET value = ? WHERE key = 'is_blocked'", ('1' if block else '0',))
    conn.commit()
    conn.close()
    return {"message": "Statut de blocage mis à jour"}

# --- SETTINGS ENDPOINTS ---
@app.get("/api/settings")
def get_settings():
    conn = get_db_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

@app.post("/api/settings")
def update_settings(s: SettingUpdate):
    conn = get_db_connection()
    conn.execute("UPDATE settings SET value = ? WHERE key = 'clinic_name'", (s.clinic_name,))
    conn.execute("UPDATE settings SET value = ? WHERE key = 'clinic_phone'", (s.clinic_phone,))
    conn.execute("UPDATE settings SET value = ? WHERE key = 'msg_template_fr'", (s.msg_template_fr,))
    conn.execute("UPDATE settings SET value = ? WHERE key = 'msg_template_ar'", (s.msg_template_ar,))
    conn.commit()
    conn.close()
    return {"message": "Paramètres enregistrés avec succès"}

# Static Files serving for Web UI
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
