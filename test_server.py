import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.backend.main import app
from app.backend.database import init_db
from app.backend.license import get_machine_hwid, generate_license_key

client = TestClient(app)

def run_tests():
    init_db()
    print("--- Testing Cryptographic Clinic Payload & Master Admin Key ---")

    
    hwid = get_machine_hwid()
    print(f" [+] Machine HWID: {hwid}")

    # 1. Generate key bound to "Clinique El Rahma"
    key_rahma = generate_license_key(hwid, clinic_name="Clinique El Rahma", tier="Premium")
    print(f" [+] Generated Key for El Rahma: {key_rahma}")

    # Activate El Rahma Key
    res_act = client.post("/api/license/activate", json={"license_key": key_rahma, "clinic_name": "Clinique El Rahma"})
    assert res_act.status_code == 200
    act_data = res_act.json()
    assert act_data['clinic_name'] == "Clinique El Rahma"

    print(f" [+] Activated El Rahma Key -> Auto-updated Clinic Name to: '{act_data['clinic_name']}'")

    # Verify status reflects El Rahma
    res_status = client.get("/api/license/status")
    assert res_status.json()['clinic_name'] == "Clinique El Rahma"
    assert res_status.json()['tier'] == "PREMIUM"
    print(" [+] Status Check OK: Tier PREMIUM, Clinic 'Clinique El Rahma'")

    # 2. Master Admin Key
    admin_key = generate_license_key(hwid, clinic_name="", is_admin=True)
    print(f" [+] Generated Master Admin Key: {admin_key}")
    
    res_admin = client.post("/api/license/activate", json={"license_key": admin_key})
    assert res_admin.status_code == 200
    assert res_admin.json()['is_admin'] == True
    print(" [+] Master Admin Mode Activated OK!")

    print("\nALL CLINIC-BOUND & ADMIN KEY TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
