from pydantic import BaseModel
from typing import Optional

class DoctorCreate(BaseModel):
    name: str
    specialty: str
    phone: str
    access_pin: Optional[str] = None

class DoctorLogin(BaseModel):
    access_pin: str

class PatientCreate(BaseModel):
    full_name: str
    phone: str
    gender: Optional[str] = "M"
    blood_type: Optional[str] = "O+"
    photo_data: Optional[str] = None
    notes: Optional[str] = ""

class PatientPhotoUpdate(BaseModel):
    photo_data: str

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: str
    time_slot: str
    notes: Optional[str] = ""

class AppointmentStatusUpdate(BaseModel):
    status: str

class SettingUpdate(BaseModel):
    clinic_name: str
    clinic_phone: str
    msg_template_fr: str
    msg_template_ar: str

class LicenseActivate(BaseModel):
    license_key: str
    clinic_name: Optional[str] = None

class MedicalRecordCreate(BaseModel):
    patient_id: int
    doctor_id: int
    diagnosis: str
    prescription: str
