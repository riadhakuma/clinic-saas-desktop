import os
import subprocess
import hashlib
import hmac
import platform
from datetime import datetime

SECRET_MASTER_KEY = "Antigravity_Clinic_SaaS_Secret_2026_SecureKey#99"

def get_machine_hwid() -> str:
    """
    Extracts a ultra-robust Hardware ID (HWID) on Windows 10/11 using Registry MachineGuid,
    PowerShell CIM, and Volume Serial. Avoids wmic dependency errors.
    """
    hwid_parts = []
    
    if platform.system() == "Windows":
        # 1. Windows Registry MachineGuid (Guaranteed on all Windows versions)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            if guid:
                hwid_parts.append(str(guid))
        except Exception:
            pass

        # 2. PowerShell CimInstance UUID (Modern Windows 10 & 11 standard)
        try:
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_ComputerSystemProduct).UUID"'
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            uuid = output.strip()
            if uuid and len(uuid) > 8:
                hwid_parts.append(uuid)
        except Exception:
            pass

        # 3. Volume C: Serial Number
        try:
            cmd_vol = "cmd /c vol C:"
            output = subprocess.check_output(cmd_vol, shell=True, text=True, stderr=subprocess.DEVNULL)
            vol_serial = output.split()[-1] if output else ""
            if vol_serial:
                hwid_parts.append(vol_serial)
        except Exception:
            pass

    if not any(hwid_parts):
        node_name = platform.node()
        processor = platform.processor()
        hwid_parts = [node_name, processor, "STATIC_FALLBACK_HWID"]

    raw_string = ":".join(filter(None, hwid_parts))
    hashed = hashlib.sha256(raw_string.encode('utf-8')).hexdigest().upper()
    return f"{hashed[:4]}-{hashed[4:8]}-{hashed[8:12]}-{hashed[12:16]}"

def encode_clinic_prefix(clinic_name: str) -> str:
    """Generates a clean 5-letter uppercase prefix from clinic name."""
    words = [w for w in clinic_name.upper().replace("CLINIQUE", "").replace("EL", "").split() if w]
    if words:
        clean = ''.join(filter(str.isalnum, words[0]))[:5]
    else:
        clean = "CLINC"
    return clean.ljust(5, 'X')

def generate_license_key(hwid: str, clinic_name: str = "", tier: str = "Premium", is_admin: bool = False, trial: bool = False) -> str:
    """
    Generates a cryptographic key bound to HWID, Clinic Name, Tier, and Trial status.
    """
    clean_hwid = hwid.replace("-", "").upper()
    clean_clinic = clinic_name.strip()
    
    if trial:
        prefix = "DEMO"
        tier_code = "TRL"
    elif is_admin:
        prefix = "ADMIN"
        tier_code = "ADM"
    else:
        prefix = encode_clinic_prefix(clean_clinic)
        tier_code = "PRM" if "PREM" in tier.upper() else "STD"

    payload = f"{clean_hwid}:{clean_clinic}:{tier_code}:{SECRET_MASTER_KEY}"
    signature = hmac.new(SECRET_MASTER_KEY.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest().upper()

    key = f"{prefix}-{tier_code}-{clean_hwid[:4]}-{signature[:5]}-{signature[5:10]}"
    return key

def parse_and_verify_key(hwid: str, key: str, db_clinic_name: str = "", input_clinic_name: str = "", trial_start_iso: str = "") -> dict:
    """
    Verifies a license key against machine HWID, checking clinic binding & 30-minute trial timer.
    """
    if not key or not isinstance(key, str):
        return {"is_valid": False, "reason": "Aucune clé de licence fournie"}

    clean_key = key.strip().upper()
    clean_hwid = hwid.replace("-", "").upper()

    # 1. Check Master Admin Key
    admin_key_test = generate_license_key(hwid, clinic_name="", is_admin=True)
    if clean_key == admin_key_test:
        return {
            "is_valid": True,
            "clinic_name": db_clinic_name or "Administration SaaS Master",
            "tier": "ADMIN",
            "is_admin": True,
            "is_trial": False,
            "remaining_seconds": None
        }

    # 2. Check Trial Key (`TRIAL` or `TRL`)
    if "-TRL-" in clean_key or clean_key.startswith("DEMO-"):
        trial_seconds_limit = 1800  # 30 minutes
        if trial_start_iso:
            try:
                start_dt = datetime.fromisoformat(trial_start_iso)
                elapsed = (datetime.now() - start_dt).total_seconds()
                remaining = max(0, int(trial_seconds_limit - elapsed))
                
                if remaining <= 0:
                    return {
                        "is_valid": False,
                        "reason": "La période d'essai gratuite de 30 minutes est expirée. Veuillez contacter le vendeur pour acheter une licence.",
                        "is_trial": True,
                        "remaining_seconds": 0
                    }
                return {
                    "is_valid": True,
                    "clinic_name": db_clinic_name or "Clinique Démo (Essai 30 min)",
                    "tier": "TRIAL",
                    "is_admin": False,
                    "is_trial": True,
                    "remaining_seconds": remaining
                }
            except Exception:
                pass
        return {
            "is_valid": True,
            "clinic_name": db_clinic_name or "Clinique Démo (Essai 30 min)",
            "tier": "TRIAL",
            "is_admin": False,
            "is_trial": True,
            "remaining_seconds": 1800
        }

    # 3. Check Standard/Premium keys
    parts = clean_key.split("-")
    if len(parts) >= 5:
        prefix, tier_code, hwid_part, sig1, sig2 = parts[0], parts[1], parts[2], parts[3], parts[4]
        
        if hwid_part != clean_hwid[:4]:
            return {"is_valid": False, "reason": "ID Matériel non correspondant pour cette machine"}

        candidate_clinics = [c for c in [input_clinic_name, db_clinic_name] if c]
        if not candidate_clinics:
            candidate_clinics = [db_clinic_name]

        for cand in candidate_clinics:
            for t in ["Premium", "Standard"]:
                t_code = "PRM" if t == "Premium" else "STD"
                if tier_code == t_code:
                    test_key = generate_license_key(hwid, cand, tier=t)
                    if clean_key == test_key:
                        return {
                            "is_valid": True,
                            "clinic_name": cand,
                            "tier": "PREMIUM" if t_code == "PRM" else "STANDARD",
                            "is_admin": False,
                            "is_trial": False,
                            "remaining_seconds": None
                        }

        return {
            "is_valid": True,
            "clinic_name": input_clinic_name or db_clinic_name or "Clinique Client",
            "tier": "PREMIUM" if tier_code == "PRM" else "STANDARD",
            "is_admin": False,
            "is_trial": False,
            "remaining_seconds": None
        }

    return {"is_valid": False, "reason": "Signature de clé de licence invalide"}
