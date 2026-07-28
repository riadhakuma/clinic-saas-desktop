# 📘 Guide d'Architecture Full-Stack : Python, JS, PWA & Capacitor Native iOS

Ce guide vous explique pas à pas comment fonctionne l'architecture de votre application SaaS, la différence entre une **PWA** et **Capacitor iOS**, et comment transformer votre interface web en application native iPhone & iPad.

---

## 🏗️ 1. L'Architecture Full-Stack Expliquée Simplement

Votre application repose sur **deux piliers principaux** :

```
┌───────────────────────────┐      Requêtes REST JSON     ┌───────────────────────────┐
│   📱 Client (iPad / PC)   │ <-------------------------> │    ⚙️ Backend Python      │
│  HTML5 + CSS3 + JS Vanilla│                             │     FastAPI + SQLite      │
└───────────────────────────┘                             └───────────────────────────┘
```

1. **Le Backend Python (FastAPI + SQLite)** :
   - Fichiers : `app/backend/main.py`, `database.py`, `license.py`.
   - **Rôle** : C'est le "cerveau". Il gère la base de données (`clinic_data.db`), vérifie la clé de licence HMAC-SHA256, filtre l'agenda du médecin, et enregistre les ordonnances.
2. **Le Frontend Web (HTML / CSS / JavaScript)** :
   - Fichiers : `app/static/index.html`, `style.css`, `app.js`.
   - **Rôle** : C'est le "visuel". Il affiche les boutons, la bascule de thème sombre/clair, les fenêtres modales, et fait des requêtes `fetch('/api/...')` vers le serveur.

---

## 🌐 2. PWA (Progressive Web App) vs Capacitor iOS

| Critère | 🌐 PWA (Web App Progressive) | 📱 Capacitor Native iOS |
| :--- | :--- | :--- |
| **Principe** | Site web optimisé avec `manifest.json` | Wrapper natif Swift/WKWebView |
| **Installation** | Bouton Safari *"Sur l'écran d'accueil"* | Fichier `.ipa` via Xcode / TestFlight / App Store |
| **Frais Apple** | **0 $ / an** | 99 $ / an (si publication App Store) |
| **Mises à jour** | Instantanées dès le rafraîchissement | Compilation Xcode requise |
| **Accès Caméra / GPS** | Oui (via API Web Standard Safari) | Oui (via Plugins Natifs iOS Swift) |

---

## ⚡ 3. Comment Fonctionne Capacitor iOS (Méthode B) ?

**Capacitor** (développé par l'équipe Ionic) prend vos fichiers web (`HTML`, `CSS`, `JS`) et les encapsule dans un conteneur natif iOS (`WKWebView` en Swift).

```
   [ Vos Fichiers Web ]            [ Bridge Capacitor ]           [ Système iOS Natif ]
┌─────────────────────────┐     ┌───────────────────────┐     ┌───────────────────────┐
│  index.html / app.js    │ --> │  npx cap sync         │ --> │  App iOS (.xcodeproj) │
│  Interface Glassmorphic │     │  Bridge JS <-> Swift  │     │  Swift / iPad / iPhone│
└─────────────────────────┘     └───────────────────────┘     └───────────────────────┘
```

---

## 📲 4. Guide Pratique : Compiler & Tester sur iPad / iPhone

### Étape 1 : Synchroniser les Fichiers Web
Le dossier web de l'application est configuré sur `app/static` dans `capacitor.config.json`.
```bash
npx cap sync
```

### Étape 2 : Ajouter la Plateforme iOS (Génère le projet Xcode)
```bash
npx cap add ios
```

### Étape 3 : Ouvrir dans Xcode & Tester sur iPad / iPhone
```bash
npx cap open ios
```
* **Sur Mac** : Xcode s'ouvre automatiquement. Vous choisissez votre iPad/iPhone connecté en USB (ou le simulateur iPad Pro) et vous cliquez sur **Run (▶)** !
* **Sans Mac (via Cloud / GitHub Actions)** : On peut configurer un workflow GitHub Actions qui compile automatiquement le fichier `.ipa` téléchargeable sur votre iPad via le site **Diawi** ou **TestFlight** !
