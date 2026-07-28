// Clinic SaaS Dynamic Frontend Engine
const API_BASE = "/api";
let currentCardPatientId = null;
let currentPrescriptionPatientId = null;
let trialTimerInterval = null;
let activeDoctor = null;

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    checkLicense();
    loadDashboard();
    loadDoctors();
    loadPatients();
    loadSettings();
    restoreDoctorSession();
});

// --- THEME SWITCHER ENGINE ---
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const btn = document.getElementById('themeToggleBtn');
    if (btn) {
        if (theme === 'light') {
            btn.innerHTML = `<i class="fa-solid fa-moon"></i> Mode Sombre`;
        } else {
            btn.innerHTML = `<i class="fa-solid fa-sun"></i> Mode Clair`;
        }
    }
}

// --- LICENSE & 30-MIN TRIAL COUNTDOWN ---
async function checkLicense() {
    try {
        const res = await fetch(`${API_BASE}/license/status`);
        const data = await res.json();

        const displayHwid = document.getElementById("displayHwid");
        if (displayHwid) displayHwid.innerText = data.hwid || "XXXX-XXXX-XXXX-XXXX";

        const badge = document.getElementById("licenseTierBadge");
        const adminTab = document.getElementById("adminNavTab");
        const trialBadge = document.getElementById("trialCountdownBadge");
        const sidebarTitle = document.getElementById("sidebarClinicName");

        if (adminTab) {
            adminTab.style.display = data.is_admin ? "flex" : "none";
        }

        if (data.is_trial && data.remaining_seconds !== null) {
            startTrialCountdown(data.remaining_seconds);
        } else if (trialBadge) {
            trialBadge.style.display = "none";
        }

        if (!data.is_activated) {
            document.getElementById("activationOverlay").style.display = "flex";
            if (badge) badge.innerText = "TIER: NON ACTIVÉ";
            if (sidebarTitle) sidebarTitle.innerText = "Clinique (Non Activée)";

            if (data.reason) {
                const errDiv = document.getElementById("activationError");
                if (errDiv) {
                    errDiv.innerText = data.reason;
                    errDiv.style.display = "block";
                }
            }
        } else {
            document.getElementById("activationOverlay").style.display = "none";
            if (badge) badge.innerText = `TIER: ${data.tier || 'ACTIVÉ'}`;
            if (data.clinic_name && sidebarTitle) {
                sidebarTitle.innerText = data.clinic_name;
            }
        }
    } catch (e) {
        console.error("Erreur de vérification de licence", e);
    }
}


function startTrialCountdown(seconds) {
    const badge = document.getElementById("trialCountdownBadge");
    if (!badge) return;
    badge.style.display = "inline-block";

    if (trialTimerInterval) clearInterval(trialTimerInterval);

    let remaining = seconds;
    const updateDisplay = () => {
        if (remaining <= 0) {
            badge.innerText = "⏱️ Essai expiré";
            clearInterval(trialTimerInterval);
            checkLicense();
            return;
        }
        const mins = Math.floor(remaining / 60);
        const secs = remaining % 60;
        badge.innerText = `⏱️ Essai: ${mins}m ${secs < 10 ? '0' : ''}${secs}s`;
        remaining--;
    };

    updateDisplay();
    trialTimerInterval = setInterval(updateDisplay, 1000);
}

function copyHwid() {
    const hwidText = document.getElementById("displayHwid").innerText;
    navigator.clipboard.writeText(hwidText).then(() => {
        alert("ID Matériel copié ! Envoyez ce code à votre vendeur.");
    });
}

async function submitActivation(e) {
    e.preventDefault();
    const key = document.getElementById("activationKeyInput").value.trim();
    const errDiv = document.getElementById("activationError");
    errDiv.style.display = "none";

    try {
        const res = await fetch(`${API_BASE}/license/activate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ license_key: key })
        });
        const data = await res.json();
        if (!res.ok) {
            errDiv.innerText = data.detail || "Clé invalide";
            errDiv.style.display = "block";
        } else {
            alert(data.message);
            checkLicense();
            loadSettings();
        }
    } catch (err) {
        errDiv.innerText = "Erreur de connexion serveur";
        errDiv.style.display = "block";
    }
}

// --- DOCTOR AUTHENTICATION & PORTAL ---
function restoreDoctorSession() {
    const saved = localStorage.getItem("doctorSession");
    if (saved) {
        try {
            activeDoctor = JSON.parse(saved);
            showDoctorDashboard();
        } catch (e) {
            localStorage.removeItem("doctorSession");
        }
    }
}

async function loginDoctor() {
    const pin = document.getElementById("doctorPinInput").value.trim();
    if (!pin) {
        alert("Veuillez saisir un code PIN");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/doctor-login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ access_pin: pin })
        });

        const data = await res.json();
        if (!res.ok) {
            alert(data.detail || "Code PIN invalide");
            return;
        }

        activeDoctor = data;
        localStorage.setItem("doctorSession", JSON.stringify(data));
        showDoctorDashboard();
    } catch (e) {
        alert("Erreur de connexion au serveur");
    }
}

function showDoctorDashboard() {
    document.getElementById("doctorLoginBox").style.display = "none";
    document.getElementById("doctorDashboardBox").style.display = "block";
    document.getElementById("activeDoctorName").innerText = activeDoctor.name;
    document.getElementById("activeDoctorSpecialty").innerText = activeDoctor.specialty;
    loadDoctorAgenda();
}

function logoutDoctor() {
    activeDoctor = null;
    localStorage.removeItem("doctorSession");
    document.getElementById("doctorLoginBox").style.display = "block";
    document.getElementById("doctorDashboardBox").style.display = "none";
}

async function loadDoctorAgenda() {
    if (!activeDoctor) return;

    try {
        const [agendaRes, notifRes] = await Promise.all([
            fetch(`${API_BASE}/doctor/${activeDoctor.id}/agenda`),
            fetch(`${API_BASE}/doctor/${activeDoctor.id}/notifications`)
        ]);

        const agenda = await agendaRes.json();
        const notif = await notifRes.json();

        const notifBadge = document.getElementById("doctorNotificationBadge");
        if (notifBadge) {
            notifBadge.innerText = `🔔 ${notif.count} En attente`;
        }

        const tbody = document.getElementById("tableDoctorAgenda");
        tbody.innerHTML = "";

        if (agenda.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">Aucun rendez-vous planifié aujourd'hui.</td></tr>`;
            return;
        }

        agenda.forEach(app => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${app.time_slot}</strong><br><small style="color:var(--text-secondary);">${app.appointment_date}</small></td>
                <td><strong>${app.patient_name}</strong><br><small style="color:var(--text-secondary);">${app.patient_phone}</small></td>
                <td><span class="badge badge-cancelled">${app.blood_type || 'O+'}</span></td>
                <td><span class="badge badge-confirmed">${app.status}</span></td>
                <td>
                    <button class="btn btn-primary" onclick="openPrescriptionModal(${app.patient_id}, '${app.patient_name}')" style="padding: 6px 12px; font-size: 0.8rem;">
                        <i class="fa-solid fa-file-signature"></i> Ordonnance & Dossier
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Erreur de chargement de l'agenda médecin", e);
    }
}

// --- MEDICAL RECORDS & PRESCRIPTIONS ---
async function openPrescriptionModal(patientId, patientName) {
    currentPrescriptionPatientId = patientId;
    document.getElementById("prescPatientHeader").innerText = `Patient: ${patientName}`;
    document.getElementById("prescDiagnosis").value = "";
    document.getElementById("prescText").value = "";

    openModal("modalPrescription");
    loadPatientPrescriptionHistory(patientId);
}

async function loadPatientPrescriptionHistory(patientId) {
    const listDiv = document.getElementById("prescHistoryList");
    listDiv.innerHTML = "<p style='color: var(--text-secondary); font-size: 0.85rem;'>Chargement...</p>";

    try {
        const res = await fetch(`${API_BASE}/medical-records/patient/${patientId}`);
        const records = await res.json();

        listDiv.innerHTML = "";
        if (records.length === 0) {
            listDiv.innerHTML = "<p style='color: var(--text-secondary); font-size: 0.85rem;'>Aucun antécédent d'ordonnance trouvé.</p>";
            return;
        }

        records.forEach(r => {
            const card = document.createElement("div");
            card.style.cssText = "background: var(--input-bg); padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid var(--accent-indigo);";
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 4px;">
                    <span>${r.doctor_name} (${r.doctor_specialty})</span>
                    <span>${r.created_at}</span>
                </div>
                <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 4px; color: var(--accent-cyan);">${r.diagnosis}</div>
                <div style="white-space: pre-wrap; font-size: 0.85rem;">${r.prescription}</div>
            `;
            listDiv.appendChild(card);
        });
    } catch (e) {
        listDiv.innerHTML = "<p style='color: var(--accent-rose); font-size: 0.85rem;'>Erreur de chargement de l'historique</p>";
    }
}

async function saveMedicalRecord(e) {
    e.preventDefault();
    if (!currentPrescriptionPatientId || !activeDoctor) {
        alert("Veuillez vous connecter en tant que médecin.");
        return;
    }

    const diagnosis = document.getElementById("prescDiagnosis").value;
    const prescription = document.getElementById("prescText").value;

    try {
        const res = await fetch(`${API_BASE}/medical-records`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                patient_id: currentPrescriptionPatientId,
                doctor_id: activeDoctor.id,
                diagnosis: diagnosis,
                prescription: prescription
            })
        });

        const data = await res.json();
        if (res.ok) {
            alert("Ordonnance et dossier enregistrés avec succès !");
            closeModal("modalPrescription");
            loadDoctorAgenda();
        } else {
            alert(data.detail || "Erreur d'enregistrement");
        }
    } catch (err) {
        alert("Erreur de sauvegarde de l'ordonnance");
    }
}

// --- DASHBOARD DATA LOADING ---
async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/dashboard`);
        const data = await res.json();

        document.getElementById("statPatients").innerText = data.stats.total_patients;
        document.getElementById("statTodayApp").innerText = data.stats.today_appointments;
        document.getElementById("statPendingApp").innerText = data.stats.pending_appointments;
        document.getElementById("statDoctors").innerText = data.stats.total_doctors;

        const tbody = document.getElementById("tableRecentAppointments");
        tbody.innerHTML = "";

        data.recent_appointments.forEach(app => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${app.patient_name}</strong><br><small style="color:var(--text-secondary);">${app.patient_phone}</small></td>
                <td>${app.doctor_name}</td>
                <td>${app.appointment_date} à ${app.time_slot}</td>
                <td><span class="badge ${getStatusBadgeClass(app.status)}">${app.status}</span></td>
                <td>
                    <button class="btn btn-whatsapp" onclick="sendWhatsApp(${app.id}, 'fr')"><i class="fa-brands fa-whatsapp"></i> FR</button>
                    <button class="btn btn-whatsapp" onclick="sendWhatsApp(${app.id}, 'ar')"><i class="fa-brands fa-whatsapp"></i> AR</button>
                </td>
                <td>
                    <select onchange="updateStatus(${app.id}, this.value)" class="form-control" style="padding: 4px; font-size: 0.8rem; width: auto;">
                        <option value="En attente" ${app.status === 'En attente' ? 'selected' : ''}>En attente</option>
                        <option value="Confirmé" ${app.status === 'Confirmé' ? 'selected' : ''}>Confirmé</option>
                        <option value="Terminé" ${app.status === 'Terminé' ? 'selected' : ''}>Terminé</option>
                        <option value="Annulé" ${app.status === 'Annulé' ? 'selected' : ''}>Annulé</option>
                    </select>
                </td>
            `;
            tbody.appendChild(tr);
        });

        loadAllAppointments();
    } catch (e) {
        console.error("Erreur tableau de bord", e);
    }
}

async function loadAllAppointments() {
    try {
        const res = await fetch(`${API_BASE}/dashboard`);
        const data = await res.json();
        const tbody = document.getElementById("tableAllAppointments");
        tbody.innerHTML = "";

        data.recent_appointments.forEach(app => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>#${app.id}</td>
                <td><strong>${app.patient_name}</strong></td>
                <td>${app.doctor_name}</td>
                <td>${app.appointment_date}</td>
                <td>${app.time_slot}</td>
                <td><span class="badge ${getStatusBadgeClass(app.status)}">${app.status}</span></td>
                <td>
                    <button class="btn btn-whatsapp" onclick="sendWhatsApp(${app.id}, 'fr')"><i class="fa-brands fa-whatsapp"></i> FR</button>
                    <button class="btn btn-whatsapp" onclick="sendWhatsApp(${app.id}, 'ar')"><i class="fa-brands fa-whatsapp"></i> AR</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {}
}

// --- DOCTORS DIRECTORY & PIN GENERATOR ---
async function loadDoctors() {
    try {
        const res = await fetch(`${API_BASE}/doctors`);
        const doctors = await res.json();

        const docSelect = document.getElementById("appDoctorSelect");
        if (docSelect) {
            docSelect.innerHTML = '<option value="">-- Sélectionner un médecin --</option>';
            doctors.forEach(d => {
                docSelect.innerHTML += `<option value="${d.id}">${d.name} (${d.specialty})</option>`;
            });
        }

        const tbody = document.getElementById("tableDoctors");
        if (tbody) {
            tbody.innerHTML = "";
            doctors.forEach(d => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>#${d.id}</td>
                    <td><strong>${d.name}</strong></td>
                    <td>${d.specialty}</td>
                    <td>${d.phone}</td>
                    <td><code style="background: var(--input-bg); padding: 4px 8px; border-radius: 4px; color: var(--accent-cyan); font-weight: 700;">${d.access_pin || 'Non défini'}</code></td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error("Erreur de chargement médecins", e);
    }
}

async function saveDoctor(e) {
    e.preventDefault();
    const name = document.getElementById("docName").value;
    const specialty = document.getElementById("docSpecialty").value;
    const phone = document.getElementById("docPhone").value;
    const access_pin = document.getElementById("docPin").value;

    try {
        const res = await fetch(`${API_BASE}/doctors`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, specialty, phone, access_pin })
        });
        const data = await res.json();
        alert(`Médecin créé ! Code PIN d'accès : ${data.access_pin}`);
        closeModal("modalDoctor");
        loadDoctors();
        loadDashboard();
    } catch (err) {
        alert("Erreur lors de l'ajout du médecin");
    }
}

// --- PATIENTS & MEDICAL CARDS ---
async function loadPatients() {
    try {
        const res = await fetch(`${API_BASE}/patients`);
        const patients = await res.json();

        const patSelect = document.getElementById("appPatientSelect");
        if (patSelect) {
            patSelect.innerHTML = '<option value="">-- Sélectionner un patient --</option>';
            patients.forEach(p => {
                patSelect.innerHTML += `<option value="${p.id}">${p.full_name} (${p.phone})</option>`;
            });
        }

        const tbody = document.getElementById("tablePatients");
        if (tbody) {
            tbody.innerHTML = "";
            patients.forEach(p => {
                const cardId = `PAT-2026-${String(p.id).padStart(4, '0')}`;
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong style="color: var(--accent-cyan);">${cardId}</strong></td>
                    <td><strong>${p.full_name}</strong></td>
                    <td>${p.phone}</td>
                    <td>${p.gender === 'F' ? 'Femme' : 'Homme'}</td>
                    <td><span class="badge badge-cancelled">${p.blood_type || 'O+'}</span></td>
                    <td>
                        <button class="btn btn-secondary" onclick="viewMedicalCard(${p.id})">
                            <i class="fa-solid fa-address-card"></i> Voir Carte
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {}
}

async function savePatient(e) {
    e.preventDefault();
    const full_name = document.getElementById("patName").value;
    const phone = document.getElementById("patPhone").value;
    const gender = document.getElementById("patGender").value;
    const blood_type = document.getElementById("patBlood").value;
    const notes = document.getElementById("patNotes").value;

    try {
        const res = await fetch(`${API_BASE}/patients`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ full_name, phone, gender, blood_type, notes })
        });
        if (res.ok) {
            alert("Patient créé avec succès !");
            closeModal("modalPatient");
            loadPatients();
            loadDashboard();
        }
    } catch (err) {
        alert("Erreur lors de l'ajout du patient");
    }
}

async function viewMedicalCard(patientId) {
    currentCardPatientId = patientId;
    try {
        const res = await fetch(`${API_BASE}/patients/${patientId}`);
        const p = await res.json();

        document.getElementById("cardPatientId").innerText = `PAT-2026-${String(p.id).padStart(4, '0')}`;
        document.getElementById("cardPatientName").innerText = p.full_name;
        document.getElementById("cardPatientPhone").innerText = p.phone;
        document.getElementById("cardPatientBlood").innerText = p.blood_type || "O+";

        const avatarBox = document.getElementById("cardAvatarBox");
        if (p.photo_data) {
            avatarBox.innerHTML = `<img src="${p.photo_data}" alt="Avatar">`;
        } else {
            avatarBox.innerHTML = `<i class="fa-solid fa-user avatar-placeholder"></i>`;
        }

        openModal("modalMedicalCard");
    } catch (e) {
        alert("Impossible d'afficher la carte médicale");
    }
}

function handlePhotoUpload(e) {
    const file = e.target.files[0];
    if (!file || !currentCardPatientId) return;

    const reader = new FileReader();
    reader.onload = async function(evt) {
        const base64Data = evt.target.result;
        try {
            const res = await fetch(`${API_BASE}/patients/${currentCardPatientId}/photo`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ photo_data: base64Data })
            });

            if (res.ok) {
                document.getElementById("cardAvatarBox").innerHTML = `<img src="${base64Data}" alt="Avatar">`;
                alert("Photo enregistrée sur la carte médicale !");
            }
        } catch (err) {
            alert("Échec du téléchargement de la photo");
        }
    };
    reader.readAsDataURL(file);
}

// --- APPOINTMENT ACTIONS & WHATSAPP ---
async function saveAppointment(e) {
    e.preventDefault();
    const patient_id = document.getElementById("appPatientSelect").value;
    const doctor_id = document.getElementById("appDoctorSelect").value;
    const appointment_date = document.getElementById("appDate").value;
    const time_slot = document.getElementById("appTime").value;
    const notes = document.getElementById("appNotes").value;

    try {
        const res = await fetch(`${API_BASE}/appointments`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ patient_id, doctor_id, appointment_date, time_slot, notes })
        });
        if (res.ok) {
            alert("Rendez-vous programmé avec succès !");
            closeModal("modalAppointment");
            loadDashboard();
        }
    } catch (err) {
        alert("Erreur de réservation");
    }
}

async function sendWhatsApp(appId, lang) {
    try {
        const res = await fetch(`${API_BASE}/whatsapp/link/${appId}?lang=${lang}`);
        const data = await res.json();
        if (data.whatsapp_url) {
            window.open(data.whatsapp_url, "_blank");
        }
    } catch (e) {
        alert("Impossible de générer le lien WhatsApp");
    }
}

async function updateStatus(appId, newStatus) {
    try {
        await fetch(`${API_BASE}/appointments/${appId}/status`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });
        loadDashboard();
    } catch (e) {}
}

function exportCSV() {
    window.location.href = `${API_BASE}/export/csv`;
}

async function toggleAdminBlock(blockState) {
    try {
        const res = await fetch(`${API_BASE}/admin/block?block=${blockState}`, { method: "POST" });
        const data = await res.json();
        alert(data.message);
        checkLicense();
    } catch (e) {
        alert("Erreur admin");
    }
}

// --- SETTINGS MANAGEMENT ---
async function loadSettings() {
    try {
        const res = await fetch(`${API_BASE}/settings`);
        const s = await res.json();

        if (s.clinic_name) {
            document.getElementById("settingClinicName").value = s.clinic_name;
            const sidebarTitle = document.getElementById("sidebarClinicName");
            if (sidebarTitle) sidebarTitle.innerText = s.clinic_name;
            const cardTitle = document.getElementById("cardClinicName");
            if (cardTitle) cardTitle.innerText = s.clinic_name;
        }
        if (s.clinic_phone) document.getElementById("settingClinicPhone").value = s.clinic_phone;
        if (s.msg_template_fr) document.getElementById("settingMsgFr").value = s.msg_template_fr;
        if (s.msg_template_ar) document.getElementById("settingMsgAr").value = s.msg_template_ar;
    } catch (e) {}
}

async function saveSettings(e) {
    e.preventDefault();
    const clinic_name = document.getElementById("settingClinicName").value;
    const clinic_phone = document.getElementById("settingClinicPhone").value;
    const msg_template_fr = document.getElementById("settingMsgFr").value;
    const msg_template_ar = document.getElementById("settingMsgAr").value;

    try {
        const res = await fetch(`${API_BASE}/settings`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ clinic_name, clinic_phone, msg_template_fr, msg_template_ar })
        });
        if (res.ok) {
            alert("Paramètres sauvegardés avec succès !");
            loadSettings();
        }
    } catch (err) {
        alert("Erreur de sauvegarde");
    }
}

// --- UI NAVIGATION & MODALS ---
function switchTab(tabName, clickedItem) {
    document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
    if (clickedItem) clickedItem.classList.add("active");

    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    
    const targetMap = {
        'dashboard': { id: 'tabDashboard', title: 'Tableau de Bord Réception', sub: 'Aperçu global, agendages et rappels WhatsApp du jour' },
        'appointments': { id: 'tabAppointments', title: 'Gestion des Rendez-vous', sub: 'Planning des consultations et états des rappels' },
        'patients': { id: 'tabPatients', title: 'Répertoire Patients & Cartes Santé', sub: 'Dossiers des patients, cartes de santé et photos' },
        'doctorPortal': { id: 'tabDoctorPortal', title: 'Espace & Agenda Médecin', sub: 'Consultations personnelles, prescriptions et ordonnances' },
        'doctors': { id: 'tabDoctors', title: 'Gestion des Médecins', sub: 'Équipe médicale et codes PIN d\'accès' },
        'settings': { id: 'tabSettings', title: 'Paramètres Général', sub: 'Modèles de messages WhatsApp et informations clinique' },
        'admin': { id: 'tabAdmin', title: 'Panneau Vendor Master Admin', sub: 'Contrôle maître de sécurité et blocage des machines' }
    };

    const target = targetMap[tabName];
    if (target) {
        document.getElementById(target.id).classList.add("active");
        document.getElementById("pageTitle").innerText = target.title;
        document.getElementById("pageSubtitle").innerText = target.sub;
        if (tabName === 'doctorPortal' && activeDoctor) {
            loadDoctorAgenda();
        }
    }
}

function openModal(id) {
    document.getElementById(id).classList.add("open");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("open");
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'Confirmé': return 'badge-confirmed';
        case 'En attente': return 'badge-pending';
        case 'Annulé': return 'badge-cancelled';
        case 'Terminé': return 'badge-completed';
        default: return 'badge-pending';
    }
}
