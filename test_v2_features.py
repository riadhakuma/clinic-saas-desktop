import sys
import os
sys.path.insert(0, r"C:\Users\attac\.gemini\antigravity\scratch\clinic_whatsapp_desktop")

from fastapi.testclient import TestClient
from app.backend.main import app
from app.backend.database import init_db
from app.backend.license import get_machine_hwid, generate_license_key

client = TestClient(app)

def run_qa():
    init_db()
    print("=== TESTING DOCTOR PORTAL & 30-MINUTE TRIAL KEY FEATURES ===")

    # Retrieve Doctors to get valid PIN
    doctors = client.get("/api/doctors").json()
    assert len(doctors) > 0
    test_doctor = doctors[0]
    doc_pin = test_doctor["access_pin"]
    print(f" [+] Found Doctor '{test_doctor['name']}' with Access PIN: {doc_pin}")

    # 1. Test Doctor Login with PIN
    res_login = client.post("/api/auth/doctor-login", json={"access_pin": doc_pin})
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    doc_data = res_login.json()
    doc_id = doc_data["id"]
    print(f" [+] Task 1: Doctor Login successful for '{doc_data['name']}' (ID: {doc_id})")

    # 2. Test Doctor Agenda Retrieval
    res_agenda = client.get(f"/api/doctor/{doc_id}/agenda")
    assert res_agenda.status_code == 200
    print(f" [+] Task 2: Retrieved Doctor Agenda ({len(res_agenda.json())} appointments scheduled)")

    # 3. Test Doctor Medical Record & Prescription Creation
    rec_payload = {
        "patient_id": 1,
        "doctor_id": doc_id,
        "diagnosis": "Angine aiguë érythémateuse",
        "prescription": "1. Augmentin 1g - 1 cp x 2/jour (8 jours)\n2. Paracétamol 1g - 1 cp x 3/jour (5 jours)"
    }
    res_rec = client.post("/api/medical-records", json=rec_payload)
    assert res_rec.status_code == 200
    print(f" [+] Task 3: Prescription saved! Record ID: {res_rec.json()['id']}")

    # 4. Test Patient Medical History Retrieval
    res_hist = client.get("/api/medical-records/patient/1")
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 1
    print(f" [+] Task 4: Verified Patient Medical History ({len(res_hist.json())} prescriptions on file)")

    # 5. Test 30-Minute Demo Trial Key Generation & Activation
    hwid = get_machine_hwid()
    trial_key = generate_license_key(hwid, trial=True)
    print(f" [+] Task 5a: Generated 30-Minute Trial Key: {trial_key}")
    
    res_act = client.post("/api/license/activate", json={"license_key": trial_key})
    assert res_act.status_code == 200
    act_data = res_act.json()
    assert act_data["is_trial"] == True
    assert act_data["remaining_seconds"] <= 1800
    print(f" [+] Task 5b: Activated Trial Key! Remaining seconds: {act_data['remaining_seconds']}s")

    print("=== ALL DOCTOR PORTAL & 30-MINUTE TRIAL TESTS PASSED 100%! ===")

if __name__ == '__main__':
    run_qa()
