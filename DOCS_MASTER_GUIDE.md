# 🏥 Clinic SaaS Desktop & Licensing Master Guide

> [!NOTE] 
> **Project Directory**: `C:\Users\attac\.gemini\antigravity\scratch\clinic_whatsapp_desktop`  
> **Target Executable**: `dist/ClinicManager.exe`

---

## 🔑 Active License Keys (`HWID: 76E2-5FA5-55E0-4445`)

| Key Type | Clinic / Role | License Key | Description |
| :--- | :--- | :--- | :--- |
| 🛡️ **Master Admin** | Vendor Master | `ADMIN-ADM-76E2-5DCEA-1DF6D` | Unlocks Vendor Admin Tab & machine blocking controls. |
| ⏱️ **30-Min Demo** | Prospect Trial | `DEMO-TRL-76E2-EFBF8-01439` | 30-Minute trial timer; auto-locks on expiration. |
| 💎 **Premium** | Clinique Kamel | `KAMXX-PRM-76E2-316C1-DAC0A` | Full permanent license auto-branded to *Clinique Kamel*. |

> [!TIP]
> **Client HWID `EFB4-C6C1-7DAC-EDEC` Keys**:
> - **Demo Key**: `DEMO-TRL-EFB4-A0D9F-C5948`
> - **Full Key (El Rahma)**: `RAHMA-PRM-EFB4-64F7F-C41BC`

---

## 💻 Key Generator CLI Commands

Run these inside `C:\Users\attac\.gemini\antigravity\scratch\clinic_whatsapp_desktop`:

```bash
# 1. Generate 30-Minute Free Demo Trial Key
python generate_license.py --hwid <CLIENT_HWID> --trial

# 2. Generate Full Premium Key bound to Clinic Name
python generate_license.py --hwid <CLIENT_HWID> --clinic "Clinique Name"

# 3. Generate Master Admin Key for local machine
python generate_license.py --current --admin
```

---

## 📦 Build & Recompile Command

```bash
python build_exe.py
```
> Outputs single standalone `.exe` at `dist/ClinicManager.exe` (zero client Python dependencies required).

---

## 🚀 3-Step Client Selling Workflow

1. **Send `.exe`**: Send `ClinicManager.exe` to client (Google Drive / USB).
2. **Get HWID**: Client opens app -> copies HWID code from lock screen -> sends to you with payment.
3. **Send Key**: Run `generate_license.py` -> send generated key to client.
