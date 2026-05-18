# 🎯 Self-Trust Score - Task Manager

Το **Self-Trust Score** είναι μια επαγγελματική εφαρμογή διαχείρισης εργασιών (Task Manager) που επικεντρώνεται στη συνέπεια. Υπολογίζει ένα σκορ εμπιστοσύνης με βάση την ολοκλήρωση των εργασιών σας, λειτουργώντας ως "κινητήρας συνέπειας" για τις υποσχέσεις προς τον εαυτό σας.

## 🚀 Χαρακτηριστικά
- **Σύστημα Σκορ Εμπιστοσύνης**: Δυναμικός υπολογισμός βάσει ολοκλήρωσης και δυσκολίας.
- **Πολυγλωσσικό UI (i18n)**: Υποστήριξη για 7 γλώσσες (Ελληνικά, English, Español, Français, Deutsch, Italiano, Português).
- **Modern UI/UX**: Καθαρός σχεδιασμός, σκοτεινή λειτουργία (Dark Mode) και ομαλά animations.
- **Advanced Analytics**: Διαγράμματα πίτας (Chart.js) για οπτικοποίηση της προόδου.
- **PWA Support**: Πλήρως εγκαταστάσιμη εφαρμογή (Installable App) για Android/iOS/Desktop.
- **Toast Notifications**: Άμεση ενημέρωση για κάθε ενέργεια.

---

## 🛠️ Τρόπος Λειτουργίας (Local)

### 1. Προετοιμασία
Βεβαιωθείτε ότι έχετε εγκαταστήσει την Python 3.12+.

### 2. Εγκατάσταση Εξαρτήσεων
```bash
pip install -r requirements.txt
```

### 3. Εκτέλεση της Εφαρμογής
Η εφαρμογή λειτουργεί πλέον ως ενιαίο FastAPI app που σερβίρει και το frontend:
```bash
uvicorn backend.main:app --reload
```
Ανοίξτε το `http://localhost:8000` στον browser σας.

---

## 🌐 Deployment (Ανάπτυξη)

### Επιλογή Α: Render (Προτεινόμενο)
1. Συνδέστε το GitHub repository σας στο **Render**.
2. Το Render θα αναγνωρίσει το `render.yaml` (Blueprint).
3. **Σημαντικό**: Βεβαιωθείτε ότι η μεταβλητή `DATABASE_URL` στο Render Dashboard είναι σωστή (πρέπει να ξεκινά με `postgres://` ή `postgresql://`).

---

## 📂 Δομή Project
- `backend/`: API (FastAPI), Database (SQLAlchemy), Auth (JWT).
- `frontend/`: Pure JS/CSS/HTML UI (Single Page Application).
- `config/`: Ρυθμίσεις και Environment Variables.
- `frontend/static/`: Εικονίδια και Branding assets.

---

## 🛡️ Ασφάλεια
- Κρυπτογράφηση κωδικών με **bcrypt**.
- Αυθεντικοποίηση με **JWT tokens** (αποθηκευμένα στο localStorage).
- Πλήρης υποστήριξη HTTPS.
