import sqlite3
import os
import random
from datetime import datetime, timedelta
from app.backend.paths import get_db_path

def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Doctors table with access_pin
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            phone TEXT NOT NULL,
            access_pin TEXT UNIQUE
        )
    ''')

    # Patients table with photo_data and blood_type
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            gender TEXT DEFAULT 'M',
            blood_type TEXT DEFAULT 'O+',
            photo_data TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date DATE NOT NULL,
            time_slot TIME NOT NULL,
            status TEXT DEFAULT 'En attente',
            notes TEXT,
            whatsapp_sent BOOLEAN DEFAULT 0,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
        )
    ''')

    # Medical Records & Prescriptions table (NEW)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            diagnosis TEXT NOT NULL,
            prescription TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
        )
    ''')

    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Default settings
    default_settings = [
        ('clinic_name', 'Clinique (Licence Non Activée)'),
        ('clinic_phone', '0550000000'),
        ('language', 'fr'),
        ('msg_template_fr', 'Bonjour {patient}, nous vous rappelons votre rendez-vous avec le Dr. {doctor} le {date} à {time} à la {clinic}. Merci de confirmer votre présence.'),
        ('msg_template_ar', 'مرحباً {patient}، نذكركم بموعدكم مع الدكتور {doctor} يوم {date} على الساعة {time} في {clinic}. يرجى تأكيد حضوركم.'),
        ('license_key', ''),
        ('trial_activated_at', ''),
        ('is_blocked', '0')
    ]


    for key, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

    # Migration for missing columns
    cursor.execute("PRAGMA table_info(doctors)")
    doc_cols = [row[1] for row in cursor.fetchall()]
    if "access_pin" not in doc_cols:
        cursor.execute("ALTER TABLE doctors ADD COLUMN access_pin TEXT")

    cursor.execute("PRAGMA table_info(patients)")
    pat_cols = [row[1] for row in cursor.fetchall()]
    if "photo_data" not in pat_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN photo_data TEXT")
    if "blood_type" not in pat_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN blood_type TEXT DEFAULT 'O+'")

    # Seed initial Doctors & PINs if empty
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    if cursor.fetchone()['count'] == 0:
        cursor.execute("INSERT INTO doctors (name, specialty, phone, access_pin) VALUES (?, ?, ?, ?)", 
                       ("Dr. Karim Amrani", "Médecine Générale", "0550112233", "DOC-1001"))
        cursor.execute("INSERT INTO doctors (name, specialty, phone, access_pin) VALUES (?, ?, ?, ?)", 
                       ("Dr. Sarah Benali", "Dentiste", "0661998877", "DOC-1002"))
        
        cursor.execute("INSERT INTO patients (full_name, phone, gender, blood_type, notes) VALUES (?, ?, ?, ?, ?)", 
                       ("Yassine Zerrouki", "0555123456", "M", "O+", "Allergie Pénicilline"))
        cursor.execute("INSERT INTO patients (full_name, phone, gender, blood_type, notes) VALUES (?, ?, ?, ?, ?)", 
                       ("Amina Khelifi", "0770987654", "F", "A+", "Consultation de suivi"))
        cursor.execute("INSERT INTO patients (full_name, phone, gender, blood_type, notes) VALUES (?, ?, ?, ?, ?)", 
                       ("Omar Bouzid", "0662334455", "M", "B+", "Contrôle dentaire"))

        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, status, notes) VALUES (1, 1, ?, '09:30', 'Confirmé', 'Visite routine')", (today,))
        cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, status, notes) VALUES (2, 2, ?, '11:00', 'En attente', 'Détartrage')", (today,))
        cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, status, notes) VALUES (3, 1, ?, '14:00', 'En attente', 'Contrôle tension')", (tomorrow,))

        # Seed initial medical record
        cursor.execute("INSERT INTO medical_records (patient_id, doctor_id, diagnosis, prescription) VALUES (?, ?, ?, ?)",
                       (1, 1, "Hypertension artérielle légère", "1. Amaryl 2mg - 1 cp/jour pendant 30 jours\n2. Paracétamol 1g si douleur"))

    # Ensure all doctors have a PIN assigned
    cursor.execute("SELECT id, name FROM doctors WHERE access_pin IS NULL OR access_pin = ''")
    unassigned = cursor.fetchall()
    for doc in unassigned:
        new_pin = f"DOC-{random.randint(1000, 9999)}"
        cursor.execute("UPDATE doctors SET access_pin = ? WHERE id = ?", (new_pin, doc['id']))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print(f"Database initialized cleanly at: {get_db_path()}")
