# 🍏 Guide de Compilation & Installation iOS SANS Mac

Ce guide vous explique comment compiler votre application iOS natif (`.ipa`) gratuitement dans le Cloud grâce à **GitHub Actions**, et comment l'installer directement sur votre iPad ou iPhone depuis votre PC Windows.

---

## ⚡ Étape 1 : Activer la Compilation Cloud Gratuite (GitHub Actions)

Un fichier de workflow automatisé a été configuré dans votre projet :
📄 `[build-ios.yml](file:///C:/Users/attac/.gemini/antigravity/scratch/clinic_whatsapp_desktop/.github/workflows/build-ios.yml)`

1. Créez un dépôt sur **GitHub.com** (Privé ou Public).
2. Connectez votre projet local et poussez le code :
   ```bash
   git remote add origin https://github.com/VOTRE_PSEUDO/clinic-saas.git
   git branch -M main
   git push -u origin main
   ```
3. Sur votre dépôt GitHub, allez dans l'onglet **Actions**.
4. Vous verrez le job **"📱 Build iOS App (Without Mac)"** démarrer automatiquement ! Un Mac virtuel dans le Cloud va compiler l'application en 2 minutes.
5. Une fois terminé, téléchargez l'artefact **`CliniqueSaaS-iOS-Unsigned`** (qui contient le fichier `.ipa`).

---

## 📲 Étape 2 : Installer le fichier `.ipa` sur iPad / iPhone depuis Windows

Il existe **3 solutions ultra simples** sans Mac :

### 🎯 Option A : Sideloadly (Recommandé sur PC Windows)
1. Téléchargez gratuitement **Sideloadly** sur votre PC Windows ([sideloadly.io](https://sideloadly.io)).
2. Branchez votre iPad / iPhone à votre PC Windows avec un câble USB.
3. Glissez-déposez le fichier `CliniqueSaaS-iOS.ipa` dans Sideloadly.
4. Entrez votre identifiant Apple ID gratuit (permet à Apple d'autoriser l'application sur votre iPad).
5. Cliquez sur **Start** -> L'application s'installe directement sur l'écran d'accueil de votre iPad !

---

### 🌐 Option B : Diawi.com (Installation sans câble USB)
1. Rendez-vous sur le site gratuit [Diawi.com](https://www.diawi.com).
2. Glissez votre fichier `CliniqueSaaS-iOS.ipa`.
3. Diawi vous génère un **QR Code** et un lien court.
4. Scannez le QR Code avec l'appareil photo de votre iPad -> Cliquez sur **Installer** !

---

### 🖥️ Option C : Appetize.io (Simulateur iPad dans votre Navigateur PC)
Si vous n'avez pas votre iPad sous la main et voulez tester immédiatement l'application iOS dans un navigateur web PC :
1. Allez sur [Appetize.io](https://appetize.io).
2. Transférez le fichier `.ipa`.
3. Un iPad virtuel apparaît sur votre écran de PC Windows pour tester l'application en direct !
