import urllib.parse

def clean_algerian_phone(phone: str) -> str:
    """Formats Algerian phone numbers into international format (213xxxxxxxx)."""
    cleaned = ''.join(filter(str.isdigit, str(phone)))
    if cleaned.startswith("0"):
        cleaned = "213" + cleaned[1:]
    elif cleaned.startswith("213"):
        pass
    else:
        cleaned = "213" + cleaned
    return cleaned

def build_whatsapp_url(phone: str, message: str) -> str:
    """Generates direct wa.me link with pre-filled encoded text."""
    formatted_phone = clean_algerian_phone(phone)
    encoded_text = urllib.parse.quote(message)
    return f"https://wa.me/{formatted_phone}?text={encoded_text}"

def generate_appointment_message(
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    time_slot: str,
    clinic_name: str,
    template: str
) -> str:
    """Formats custom template message with appointment data."""
    message = template.replace("{patient}", patient_name)\
                      .replace("{doctor}", doctor_name)\
                      .replace("{date}", appointment_date)\
                      .replace("{time}", time_slot)\
                      .replace("{clinic}", clinic_name)
    return message

def generate_whatsapp_link(
    phone: str,
    patient_name: str,
    doctor_name: str,
    date_str: str,
    time_str: str,
    clinic_name: str,
    custom_template: str
) -> dict:
    """Generates formatted message & direct wa.me URL."""
    msg = generate_appointment_message(
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_date=date_str,
        time_slot=time_str,
        clinic_name=clinic_name,
        template=custom_template
    )
    url = build_whatsapp_url(phone, msg)
    return {"message": msg, "whatsapp_url": url}
