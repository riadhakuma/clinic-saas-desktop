# 🏥 Clinic SaaS Desktop App & WhatsApp Manager (v2.0)

A high-performance, offline-first Windows Desktop SaaS Application designed for medical clinics in Algeria and worldwide. Built with **FastAPI**, **SQLite**, **PyWebView**, and **Vanilla Glassmorphic CSS/JS**.

---

## 🌟 Key Features

### 1. 🏥 Vue Réception (Clinic Receptionist)
- **Appointment Scheduling**: Manage daily appointment slots, doctor assignments, and live status badges (`Confirmé`, `En attente`, `Terminé`, `Annulé`).
- **Patient Directory & Digital Medical Cards**: Photo avatar uploader, blood type badges (`AB+`, `O+`, etc.), patient serial numbers (`PAT-2026-0001`), and print views.
- **WhatsApp Automated Link Builder**: Instant French & Arabic dynamic WhatsApp notification links (`wa.me/213...`) using customizable clinic templates.
- **CSV Data Exporter**: Export appointment datasets directly to CSV.

### 2. 👨‍⚕️ Espace Médecin (Doctor Portal)
- **PIN-Based Authentication**: Receptionist generates secure access PINs for each doctor (e.g. `DOC-6284`).
- **Personal Agenda**: Filtered view showing only the appointments assigned to the logged-in doctor.
- **Ordonnances & Medical History**: Doctors can write medical diagnoses and prescriptions directly onto patient charts, with full historical records.

### 3. 🛡️ HWID Anti-Piracy & Licensing Engine
- **Hardware-Locked Activation**: Key activation binds to the host PC's unique Windows Hardware ID (`MachineGuid` + PowerShell CIM).
- **Auto-Branding**: Entering a clinic-bound key automatically customizes the software title, headers, and WhatsApp templates for that clinic.
- **Master Admin Control Panel**: Vendor master key unlocks a hidden management panel to block/unblock compromised machines.

### 4. ⏱️ 30-Minute Free Demo Trial System
- Generate preview trial keys: `python generate_license.py --current --trial`.
- Live header countdown badge (`⏱️ Essai: 29m 45s`).
- Auto-locks the software after 30 minutes, prompting prospects to purchase a full key.

---

## 🚀 How to Build Standalone `.EXE`

To compile the entire application into a single executable (`dist/ClinicManager.exe`):

```bash
python build_exe.py
```

No Python or dependencies are required on the client's PC!

---

## 🔑 License Generator CLI (For Vendor)

```bash
# Generate 30-Minute Trial Demo Key for prospect
python generate_license.py --hwid <HWID> --trial

# Generate Full Premium Key for a clinic
python generate_license.py --hwid <HWID> --clinic "Clinique El Rahma"

# Generate Master Admin Key
python generate_license.py --current --admin
```
