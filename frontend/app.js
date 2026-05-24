// Configuration
const API_BASE_URL = window.location.origin;
const SUPABASE_URL = 'https://hngljslkwyzzlcugiiqz.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_YTyCF9SfOoh-5TaFLUVxmw_NYk3_jiO';
const supabaseClient = window.supabase?.createClient
    ? window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
            persistSession: true,
            autoRefreshToken: true,
            detectSessionInUrl: true,
            storage: window.localStorage
        }
    })
    : null;

// State Management
let currentUser = null;
let supabaseSession = null;
let supabaseAccessToken = null;
let pendingVerificationEmail = null;
let authBusy = false;
let isDarkMode = localStorage.getItem('tm_dark_mode') === '1';
let currentLang = localStorage.getItem('tm_lang') || 'en';
let taskChart = null;
let trendChart = null;
let insightsChart = null;
let currentView = localStorage.getItem('tm_last_view') || 'tasks';
let cachedTasks = []; // Performance: Cache tasks locally
let cachedGoals = [];
let cachedHabits = [];
let calendarDate = new Date();
let calendarTasks = [];
let dashboardCalendarDate = new Date();
let notifiedTasks = new Set();
let notifiedHabits = new Set();
let currentTasksGoalsTab = 'tasks';
let currentGoalForReflection = null;
let identityInitialized = false;
let identitySnapshot = { level: 1, unlockedBadgeIds: [] };
let smartPersonalizationCache = { timestamp: 0, data: null };
let cropper = null;
let currentCropFile = null;

const translations = {
    en: {
        app_title: "Tobedone",
        login: "Sign In",
        signup: "Sign Up",
        continue_with_google: "Continue with Google",
        or: "or",
        username_email: "Username or Email",
        username: "Username",
        password: "Password",
        forgot_password: "Forgot password?",
        forgot_password_note: "Enter your email and we’ll send you a reset link.",
        send_reset_link: "Send reset link",
        back_to_login: "Back to sign in",
        verify_email_title: "Verify your email",
        verify_email_body: "Check your inbox and click the verification link to continue.",
        verification_code: "Verification code",
        verify_code: "Verify code",
        reset_code: "Reset code",
        use_code: "Use code",
        resend_verification: "Resend verification email",
        reset_password_title: "Set a new password",
        new_password: "New password",
        confirm_password: "Confirm password",
        update_password: "Update password",
        full_name: "Full Name",
        email: "Email",
        change_name: "Change Name",
        change_username: "Change Username",
        create_account: "Create Account",
        dashboard: "Dashboard",
        reports: "Reports",
        me: "Me",
        tasks: "Tasks",
        insights: "Insights",
        settings: "Settings",
        logout: "Logout",
        trust_score: "Trust Score",
        streak: "Streak",
        success: "Success",
        daily_progress: "Daily Progress",
        statistics: "Statistics",
        task_distribution: "Task Distribution",
        add_new_task: "Add New Task",
        new_task: "New Task",
        task_placeholder: "What needs to be done?",
        category: "Category",
        difficulty: "Difficulty",
        easy: "Easy",
        medium: "Medium",
        hard: "Hard",
        cancel: "Cancel",
        add_task: "Add Task",
        priority: "Priority",
        low: "Low",
        medium: "Medium",
        high: "High",
        recurring: "Recurring",
        none: "None",
        daily: "Daily",
        weekly: "Weekly",
        due_date: "Due Date",
        overdue: "Overdue",
        all: "All",
        filter_by: "Filter by",
        productive_day: "Most Productive Day",
        productive_hour: "Most Productive Hour",
        trends: "Completion Trends",
        failure_patterns: "Failure Patterns",
        achievements: "Achievements",
        well_done: "Well done!",
        keep_going: "Keep it up!",
        streak_saved: "Streak maintained!",
        multiplier: "{value}x Boost",
        tasks_count: "{count} tasks today",
        smart_suggestion: "Smart Suggestion",
        best_time_to_create: "You are most active now! Great time to plan tasks.",
        suggest_simpler: "This task seems complex. Try breaking it down?",
        high_risk: "High risk of failure based on your history for this time/category.",
        optimal_time: "Optimal time to complete this: ",
        most_productive_day: "Your most productive day is ",
        most_productive_hour: "You get most things done around ",
        failure_pattern: "You tend to struggle more with tasks in ",
        theme: "Theme",
        toggle_dark: "Toggle Dark Mode",
        language: "Language",
        app_info: "App Info",
        version: "Version",
        completed: "Completed",
        failed: "Failed",
        pending: "Pending",
        no_tasks: "No tasks for today. Add one above!",
        session_expired: "Session expired",
        task_added: "Task added successfully!",
        task_updated: "Task updated!",
        error_occurred: "An error occurred",
        calendar: "Calendar",
        date: "Date",
        time: "Time",
        reminder: "Reminder",
        task_starting: "Task is starting soon!",
        january: "January", february: "February", march: "March", april: "April", may: "May", june: "June",
        july: "July", august: "August", september: "September", october: "October", november: "November", december: "December",
        mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun"
    },
    el: {
        app_title: "Tobedone",
        login: "Σύνδεση",
        signup: "Εγγραφή",
        continue_with_google: "Σύνδεση με Google",
        or: "ή",
        username_email: "Όνομα χρήστη ή Email",
        username: "Όνομα χρήστη",
        password: "Κωδικός",
        forgot_password: "Ξέχασες τον κωδικό;",
        forgot_password_note: "Βάλε το email σου και θα σου στείλουμε link ή κωδικό επαναφοράς.",
        send_reset_link: "Αποστολή επαναφοράς",
        back_to_login: "Πίσω στη σύνδεση",
        verify_email_title: "Επιβεβαίωση email",
        verify_email_body: "Έλεγξε το inbox και πάτα το link επιβεβαίωσης για να συνεχίσεις.",
        verification_code: "Κωδικός επιβεβαίωσης",
        verify_code: "Επιβεβαίωση κωδικού",
        reset_password_title: "Νέος κωδικός",
        new_password: "Νέος κωδικός",
        confirm_password: "Επιβεβαίωση κωδικού",
        update_password: "Αλλαγή κωδικού",
        change_name: "Αλλαγή Ονόματος",
        change_username: "Αλλαγή Username",
        reset_code: "Κωδικός επαναφοράς",
        use_code: "Χρήση κωδικού",
        resend_verification: "Επανάληψη email",
        full_name: "Ονοματεπώνυμο",
        email: "Email",
        create_account: "Δημιουργία Λογαριασμού",
        dashboard: "Πίνακας",
        reports: "Αναφορές",
        me: "Εγώ",
        tasks: "Εργασίες",
        insights: "Insights",
        settings: "Ρυθμίσεις",
        logout: "Αποσύνδεση",
        trust_score: "Σκορ Εμπιστοσύνης",
        streak: "Σερί",
        success: "Επιτυχία",
        daily_progress: "Ημερήσια Πρόοδος",
        statistics: "Στατιστικά",
        task_distribution: "Κατανομή Εργασιών",
        add_new_task: "Προσθήκη Εργασίας",
        new_task: "Νέα Εργασία",
        task_placeholder: "Τί πρέπει να γίνει;",
        category: "Κατηγορία",
        difficulty: "Δυσκολία",
        easy: "Εύκολο",
        medium: "Μέτριο",
        hard: "Δύσκολο",
        cancel: "Ακύρωση",
        add_task: "Προσθήκη",
        priority: "Προτεραιότητα",
        low: "Χαμηλή",
        medium: "Μεσαία",
        high: "Υψηλή",
        recurring: "Επανάληψη",
        none: "Καμία",
        daily: "Καθημερινά",
        weekly: "Εβδομαδιαία",
        due_date: "Προθεσμία",
        overdue: "Εκπρόθεσμο",
        all: "Όλα",
        filter_by: "Φίλτρο",
        insights: "Αναλύσεις",
        productive_day: "Πιο Παραγωγική Μέρα",
        productive_hour: "Πιο Παραγωγική Ώρα",
        trends: "Τάσεις Ολοκλήρωσης",
        failure_patterns: "Μοτίβα Αποτυχίας",
        achievements: "Επιτεύγματα",
        well_done: "Μπράβο!",
        keep_going: "Συνέχισε έτσι!",
        streak_saved: "Το σερί διατηρήθηκε!",
        multiplier: "{value}x Ενίσχυση",
        tasks_count: "{count} εργασίες σήμερα",
        smart_suggestion: "Έξυπνη Πρόταση",
        best_time_to_create: "Είστε πολύ δραστήριοι τώρα! Ιδανική ώρα για σχεδιασμό.",
        suggest_simpler: "Αυτή η εργασία φαίνεται περίπλοκη. Μήπως να την σπάσετε σε μικρότερες;",
        high_risk: "Υψηλός κίνδυνος αποτυχίας βάσει του ιστορικού σας για αυτή την ώρα/κατηγορία.",
        optimal_time: "Ιδανική ώρα ολοκλήρωσης: ",
        most_productive_day: "Η πιο παραγωγική σας μέρα είναι η ",
        most_productive_hour: "Ολοκληρώνετε τις περισσότερες εργασίες γύρω στις ",
        failure_pattern: "Δυσκολεύεστε περισσότερο με εργασίες στην κατηγορία ",
        theme: "Θέμα",
        toggle_dark: "Εναλλαγή Dark Mode",
        language: "Γλώσσα",
        app_info: "Πληροφορίες",
        version: "Έκδοση",
        completed: "Ολοκληρώθηκε",
        failed: "Απέτυχε",
        pending: "Εκκρεμεί",
        no_tasks: "Καμία εργασία για σήμερα!",
        session_expired: "Η συνεδρία έληξε",
        task_added: "Η εργασία προστέθηκε!",
        task_updated: "Η εργασία ενημερώθηκε!",
        error_occurred: "Παρουσιάστηκε σφάλμα",
        calendar: "Ημερολόγιο",
        date: "Ημερομηνία",
        time: "Ώρα",
        reminder: "Υπενθύμιση",
        task_starting: "Η εργασία ξεκινά σύντομα!",
        january: "Ιανουάριος", february: "Φεβρουάριος", march: "Μάρτιος", april: "Απρίλιος", may: "Μάιος", june: "Ιούνιος",
        july: "Ιούλιος", august: "Αύγουστος", september: "Σεπτέμβριος", october: "Οκτώβριος", november: "Νοέμβριος", december: "Δεκέμβριος",
        mon: "Δευ", tue: "Τρι", wed: "Τετ", thu: "Πεμ", fri: "Παρ", sat: "Σαβ", sun: "Κυρ"
    },
    es: {
        app_title: "Tobedone",
        login: "Iniciar Sesión",
        signup: "Registrarse",
        reports: "Reportes",
        me: "Yo",
        username_email: "Usuario o Email",
        password: "Contraseña",
        full_name: "Nombre Completo",
        email: "Email",
        create_account: "Crear Cuenta",
        dashboard: "Panel",
        tasks: "Tareas",
        settings: "Ajustes",
        logout: "Cerrar Sesión",
        trust_score: "Puntuación",
        streak: "Racha",
        success: "Éxito",
        daily_progress: "Progreso Diario",
        statistics: "Estadísticas",
        task_distribution: "Distribución",
        add_new_task: "Nueva Tarea",
        new_task: "Nueva Tarea",
        task_placeholder: "¿Qué hay que hacer?",
        category: "Categoría",
        difficulty: "Dificultad",
        easy: "Fácil",
        medium: "Medio",
        hard: "Difícil",
        cancel: "Cancelar",
        add_task: "Añadir",
        theme: "Tema",
        toggle_dark: "Modo Oscuro",
        language: "Idioma",
        app_info: "Información",
        version: "Versión",
        completed: "Completado",
        failed: "Fallido",
        pending: "Pendiente",
        no_tasks: "¡Sin tareas para hoy!",
        session_expired: "Sesión expirada",
        task_added: "¡Tarea añadida!",
        task_updated: "¡Tarea actualizada!",
        error_occurred: "Ocurrió un error"
    },
    fr: {
        app_title: "Tobedone",
        login: "Connexion",
        signup: "S'inscrire",
        reports: "Rapports",
        me: "Moi",
        username_email: "Nom d'utilisateur ou Email",
        password: "Mot de passe",
        full_name: "Nom complet",
        email: "Email",
        create_account: "Créer un compte",
        dashboard: "Tableau de bord",
        tasks: "Tâches",
        settings: "Paramètres",
        logout: "Déconnexion",
        trust_score: "Score de confiance",
        streak: "Série",
        success: "Succès",
        daily_progress: "Progrès quotidien",
        statistics: "Statistiques",
        task_distribution: "Distribution des tâches",
        add_new_task: "Ajouter une tâche",
        new_task: "Nouvelle tâche",
        task_placeholder: "Que faut-il faire ?",
        category: "Catégorie",
        difficulty: "Difficulté",
        easy: "Facile",
        medium: "Moyen",
        hard: "Difficile",
        cancel: "Annuler",
        add_task: "Ajouter",
        theme: "Thème",
        toggle_dark: "Mode sombre",
        language: "Langue",
        app_info: "Info",
        version: "Version",
        completed: "Terminé",
        failed: "Échoué",
        pending: "En attente",
        no_tasks: "Pas de tâches aujourd'hui !",
        session_expired: "Session expirée",
        task_added: "Tâche ajoutée !",
        task_updated: "Tâche mise à jour !",
        error_occurred: "Une erreur est survenue"
    },
    de: {
        app_title: "Tobedone",
        login: "Anmelden",
        signup: "Registrieren",
        reports: "Berichte",
        me: "Ich",
        username_email: "Benutzername oder Email",
        password: "Passwort",
        full_name: "Vollständiger Name",
        email: "Email",
        create_account: "Konto erstellen",
        dashboard: "Dashboard",
        tasks: "Aufgaben",
        settings: "Einstellungen",
        logout: "Abmelden",
        trust_score: "Vertrauen",
        streak: "Serie",
        success: "Erfolg",
        daily_progress: "Tagesfortschritt",
        statistics: "Statistiken",
        task_distribution: "Verteilung",
        add_new_task: "Aufgabe hinzufügen",
        new_task: "Neue Aufgabe",
        task_placeholder: "Was ist zu tun?",
        category: "Kategorie",
        difficulty: "Schwierigkeit",
        easy: "Einfach",
        medium: "Mittel",
        hard: "Schwer",
        cancel: "Abbrechen",
        add_task: "Hinzufügen",
        theme: "Thema",
        toggle_dark: "Dunkelmodus",
        language: "Sprache",
        app_info: "Info",
        version: "Version",
        completed: "Abgeschlossen",
        failed: "Fehlgeschlagen",
        pending: "Ausstehend",
        no_tasks: "Keine Aufgaben für heute!",
        session_expired: "Sitzung abgelaufen",
        task_added: "Aufgabe hinzugefügt!",
        task_updated: "Aufgabe aktualisiert!",
        error_occurred: "Fehler aufgetreten"
    },
    it: {
        app_title: "Tobedone",
        login: "Accedi",
        signup: "Registrati",
        reports: "Report",
        me: "Io",
        username_email: "Username o Email",
        password: "Password",
        full_name: "Nome Completo",
        email: "Email",
        create_account: "Crea Account",
        dashboard: "Dashboard",
        tasks: "Compiti",
        settings: "Impostazioni",
        logout: "Esci",
        trust_score: "Fiducia",
        streak: "Serie",
        success: "Successo",
        daily_progress: "Progresso",
        statistics: "Statistiche",
        task_distribution: "Distribuzione",
        add_new_task: "Nuovo Compito",
        new_task: "Nuovo Compito",
        task_placeholder: "Cosa c'è da fare?",
        category: "Categoria",
        difficulty: "Difficoltà",
        easy: "Facile",
        medium: "Medio",
        hard: "Difficile",
        cancel: "Annulla",
        add_task: "Aggiungi",
        theme: "Tema",
        toggle_dark: "Modalità Scura",
        language: "Lingua",
        app_info: "Info",
        version: "Versione",
        completed: "Completato",
        failed: "Fallito",
        pending: "In attesa",
        no_tasks: "Nessun compito per oggi!",
        session_expired: "Sessione scaduta",
        task_added: "Compito aggiunto!",
        task_updated: "Compito aggiornato!",
        error_occurred: "Errore verificato"
    },
    pt: {
        app_title: "Tobedone",
        login: "Entrar",
        signup: "Cadastrar",
        reports: "Relatórios",
        me: "Eu",
        username_email: "Usuário ou Email",
        password: "Senha",
        full_name: "Nome Completo",
        email: "Email",
        create_account: "Criar Conta",
        dashboard: "Painel",
        tasks: "Tarefas",
        settings: "Ajustes",
        logout: "Sair",
        trust_score: "Confiança",
        streak: "Sequência",
        success: "Sucesso",
        daily_progress: "Progresso",
        statistics: "Estatísticas",
        task_distribution: "Distribuição",
        add_new_task: "Nova Tarefa",
        new_task: "Nova Tarefa",
        task_placeholder: "O que precisa ser feito?",
        category: "Categoria",
        difficulty: "Dificuldade",
        easy: "Fácil",
        medium: "Médio",
        hard: "Difícil",
        cancel: "Cancelar",
        add_task: "Adicionar",
        theme: "Tema",
        toggle_dark: "Modo Escuro",
        language: "Idioma",
        app_info: "Info",
        version: "Versão",
        completed: "Concluído",
        failed: "Falhou",
        pending: "Pendente",
        no_tasks: "Sem tarefas para hoje!",
        session_expired: "Sessão expirada",
        task_added: "Tarefa adicionada!",
        task_updated: "Tarefa atualizada!",
        error_occurred: "Ocorreu um erro"
    }
};

function t(key) {
    return translations[currentLang][key] || key;
}

function updateUILanguage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (el.tagName === 'INPUT' && el.type !== 'submit') {
            el.placeholder = t(key);
        } else {
            el.textContent = t(key);
        }
    });
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initLanguage();
    checkAuth();
    setupEventListeners();
    initBottomNavDragSwitch();
    syncBottomNavIndicator(currentView || 'tasks');
});

function initTheme() {
    // Pro Tech Style: Always dark mode unless explicitly changed
    if (localStorage.getItem('tm_dark_mode') === null) {
        isDarkMode = true;
        localStorage.setItem('tm_dark_mode', '1');
    }
    
    applyTheme();
}

function applyTheme() {
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        document.body.classList.remove('light-mode');
    } else {
        document.body.classList.remove('dark-mode');
        document.body.classList.add('light-mode');
    }
    const switchEl = document.getElementById('dark-mode-switch');
    if (switchEl) {
        switchEl.checked = isDarkMode;
    }
    // Refresh charts to match theme
    if (currentUser && currentView === 'reports') loadReports();
    if (currentUser && currentView === 'me') loadMe();
}

function initLanguage() {
    const selector = document.getElementById('lang-selector');
    if (selector) selector.value = currentLang;
    updateUILanguage();
}

function changeLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('tm_lang', lang);
    updateUILanguage();
    if (currentUser && currentView === 'reports') loadReports();
    if (currentUser && currentView === 'me') loadMe();
    showToast(t('task_updated'), 'success');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background:none;border:none;color:inherit;cursor:pointer;font-size:1.2rem;margin-left:1rem;">&times;</button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function isEmailVerified(user) {
    return Boolean(user && (user.email_confirmed_at || user.confirmed_at));
}

function withTimeout(promise, ms, message) {
    let timeoutId;
    const timeoutPromise = new Promise((_, reject) => {
        timeoutId = setTimeout(() => reject(new Error(message || 'Timeout')), ms);
    });
    return Promise.race([promise, timeoutPromise]).finally(() => clearTimeout(timeoutId));
}

async function syncCurrentUserFromApi() {
    if (!supabaseAccessToken) {
        throw new Error('Missing session');
    }
    const response = await fetch(`${API_BASE_URL}/api/me`, {
        headers: { 'Authorization': `Bearer ${supabaseAccessToken}` }
    });
    if (!response.ok) {
        throw new Error('Session expired');
    }
    currentUser = await response.json();
}

function setAuthBusy(isBusy) {
    authBusy = isBusy;
    const ids = [
        'google-signin-btn',
        'login-email',
        'login-password',
        'signup-name',
        'signup-username',
        'signup-email',
        'signup-password',
        'forgot-email',
        'recovery-otp',
        'recovery-otp-btn',
        'reset-password',
        'reset-password-confirm',
        'verify-otp',
        'verify-otp-btn',
        'resend-verification-btn'
    ];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = isBusy;
    });
    document.querySelectorAll('#auth-page button[type="submit"]').forEach(btn => {
        btn.disabled = isBusy;
    });
}

function setAuthView(view) {
    const formIds = ['login-form', 'signup-form', 'forgot-form', 'reset-form', 'verify-form'];
    formIds.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.toggle('active', id === `${view}-form`);
    });

    const tabs = document.querySelector('.tabs');
    const oauthWrap = document.querySelector('.auth-oauth');
    const googleBtn = document.getElementById('google-signin-btn');
    const divider = document.querySelector('.auth-divider');
    const showPrimary = view === 'login' || view === 'signup';
    if (tabs) tabs.style.display = showPrimary ? '' : 'none';
    if (oauthWrap) oauthWrap.style.display = view === 'login' ? '' : 'none';
    if (googleBtn) googleBtn.style.display = view === 'login' ? '' : 'none';
    if (divider) divider.style.display = view === 'login' ? '' : 'none';

    if (showPrimary) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        const activeTab = document.getElementById(`tab-${view}`);
        if (activeTab) activeTab.classList.add('active');
    }
    showAuthError('');
}

async function handleAuthSessionChange(event, session) {
    clearUrlTokens();
    if (event === 'PASSWORD_RECOVERY') {
        renderLogin();
        setAuthView('reset');
        return;
    }

    if (!session) {
        currentUser = null;
        supabaseAccessToken = null;
        renderLogin();
        setAuthView('login');
        return;
    }

    supabaseSession = session;
    supabaseAccessToken = session.access_token;

    if (!isEmailVerified(session.user)) {
        pendingVerificationEmail = pendingVerificationEmail || session.user.email || null;
        renderLogin();
        setAuthView('verify');
        const verifyText = document.getElementById('verify-email-text');
        if (verifyText && pendingVerificationEmail) {
            verifyText.textContent = `Check ${pendingVerificationEmail} and click the verification link to continue.`;
        }
        return;
    }

    // Only call renderApp() if we're not already in the app
    // This prevents resetting the view on token refreshes
    const mainApp = document.getElementById('main-app');
    const isAlreadyInApp = mainApp && mainApp.classList.contains('active');

    if (!isAlreadyInApp) {
        // Performance: Optimistic UI - pre-fill currentUser from session metadata
        const meta = session.user.user_metadata || {};
        currentUser = {
            user_id: null, // Don't use UUID here, wait for backend sync
            email: session.user.email,
            name: meta.name || meta.full_name || session.user.email.split('@')[0],
            username: meta.username || session.user.email.split('@')[0],
            avatar_url: meta.avatar_url || null
        };

        // Immediately show app with what we have
        renderApp();
    } else {
        // Just update the currentUser data without re-rendering the whole app
        const meta = session.user.user_metadata || {};
        if (!currentUser) {
            currentUser = {
                user_id: null,
                email: session.user.email,
                name: meta.name || meta.full_name || session.user.email.split('@')[0],
                username: meta.username || session.user.email.split('@')[0],
                avatar_url: meta.avatar_url || null
            };
        } else {
            currentUser.email = session.user.email;
            currentUser.name = meta.name || meta.full_name || session.user.email.split('@')[0];
            currentUser.username = meta.username || session.user.email.split('@')[0];
            currentUser.avatar_url = meta.avatar_url || null;
        }
    }

    // Then sync in background to get full profile
    try {
        await syncCurrentUserFromApi();
        // Update UI if anything changed after sync
        const userNameEl = document.getElementById('user-display-name');
        if (userNameEl) userNameEl.textContent = currentUser.name || currentUser.username;
        renderProfileCard();
    } catch (err) {
        console.error('Background sync failed', err);
        // If it failed because session is invalid, then logout
        if (err.message === 'Session expired') {
            await supabaseClient?.auth?.signOut();
            currentUser = null;
            supabaseSession = null;
            supabaseAccessToken = null;
            renderLogin();
            setAuthView('login');
        }
    }
}

async function checkAuth() {
    showLoading(true);
    try {
        if (!supabaseClient) {
            renderLogin();
            showAuthError('Supabase SDK not loaded');
            return;
        }

        const { data } = await withTimeout(supabaseClient.auth.getSession(), 8000, 'Auth timeout');
        supabaseSession = data.session;
        supabaseAccessToken = data.session?.access_token || null;
        await handleAuthSessionChange('INITIAL', data.session);

        supabaseClient.auth.onAuthStateChange(async (event, session) => {
            await handleAuthSessionChange(event, session);
        });
    } catch (err) {
        console.error('Auth check failed', err);
        renderLogin();
        setAuthView('login');
        showAuthError('Auth unavailable. Check Supabase URL/keys and Redirect URLs.');
    } finally {
        showLoading(false);
    }
}

// --- UI Navigation ---
let lastScrollTop = 0;
const scrollThreshold = 3;
let scrollRafId = 0;
let pendingScrollTop = 0;
let pendingMaxScroll = 0;

function updateScrollProgressFromMetrics(scrollTop, maxScroll) {
    const fill = document.getElementById('scroll-progress-fill');
    if (!fill) return;
    const ratio = maxScroll > 0 ? (scrollTop / maxScroll) : 0;
    const clamped = Math.max(0, Math.min(1, ratio));
    fill.style.transform = `scaleX(${clamped})`;
}

function updateScrollProgress(scrollEl) {
    if (!scrollEl) return;
    const maxScroll = scrollEl.scrollHeight - scrollEl.clientHeight;
    updateScrollProgressFromMetrics(scrollEl.scrollTop, maxScroll);
}

function getWindowScrollMetrics() {
    const doc = document.documentElement;
    const scrollTop = window.scrollY || doc.scrollTop || document.body.scrollTop || 0;
    const maxScroll = Math.max(0, doc.scrollHeight - doc.clientHeight);
    return { scrollTop, maxScroll };
}

function applyScrollUI(scrollTop, maxScroll) {
    // Keep top bar always visible - no scrolling behavior
}

function scheduleScrollUI(scrollTop, maxScroll) {
    pendingScrollTop = scrollTop;
    pendingMaxScroll = maxScroll;
    if (scrollRafId) return;
    scrollRafId = requestAnimationFrame(() => {
        scrollRafId = 0;
        applyScrollUI(pendingScrollTop, pendingMaxScroll);
    });
}

function handleWindowScroll() {
    const { scrollTop, maxScroll } = getWindowScrollMetrics();
    scheduleScrollUI(scrollTop, maxScroll);
}

function handleContentScroll(e) {
    const el = e.target;
    const scrollTop = el.scrollTop;
    const maxScroll = el.scrollHeight - el.clientHeight;
    scheduleScrollUI(scrollTop, maxScroll);
}

function renderLogin() {
    document.getElementById('auth-page').classList.add('active');
    document.getElementById('main-app').classList.remove('active');
    document.body.style.overflow = 'hidden';
    const mobileHeader = document.querySelector('.mobile-header');
    if (mobileHeader) mobileHeader.style.display = 'none';
}

function renderApp() {
    document.getElementById('auth-page').classList.remove('active');
    document.getElementById('main-app').classList.add('active');
    document.body.style.overflow = '';
    
    // Perceived speed: render identity from currentUser first
    const displayName = currentUser.name || currentUser.username;
    const nameEl = document.getElementById('user-display-name');
    if (nameEl) nameEl.textContent = displayName;
    
    identityInitialized = false;
    identitySnapshot = { level: 1, unlockedBadgeIds: [] };
    smartPersonalizationCache = { timestamp: 0, data: null };
    cachedHabits = [];
    notifiedHabits = new Set();
    
    updateUILanguage();
    renderProfileCard();
    
    // BUG FIX: Only redirect to tasks if we don't have a current view set
    // or if we're coming from the login screen
    if (!currentView || currentView === 'tasks') {
        showView('tasks');
    } else {
        showView(currentView);
    }
}

function renderProfileCard() {
    const name = (currentUser?.name || currentUser?.username || 'User').trim();
    const username = (currentUser?.username || 'user').trim();
    const avatarUrl = (currentUser?.avatar_url || '').trim();

    const avatarEl = document.getElementById('profile-avatar');
    if (avatarEl) {
        // Only use fallback if avatarUrl is truly empty
        avatarEl.src = avatarUrl ? avatarUrl : `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=0a86ff&color=fff&size=128&bold=true`;
    }

    const nameEl = document.getElementById('profile-name');
    if (nameEl) nameEl.textContent = name;

    const usernameEl = document.getElementById('profile-username');
    if (usernameEl) usernameEl.textContent = `@${username}`;

    const nameInput = document.getElementById('profile-name-input');
    if (nameInput && document.activeElement !== nameInput) {
        nameInput.value = name;
        nameInput.setAttribute('readonly', true);
        nameInput.classList.remove('editable');
    }

    const usernameInput = document.getElementById('profile-username-input');
    if (usernameInput && document.activeElement !== usernameInput) {
        usernameInput.value = username;
        usernameInput.setAttribute('readonly', true);
        usernameInput.classList.remove('editable');
    }

    updateProfileSaveState();
}

let profileDraft = { name: null, username: null, avatar_url: null };

function hasProfileChanges() {
    const currentName = (currentUser?.name || '').trim();
    const currentUsername = (currentUser?.username || '').trim();
    const currentAvatar = (currentUser?.avatar_url || '').trim();
    const draftName = (profileDraft.name ?? currentName).trim();
    const draftUsername = (profileDraft.username ?? currentUsername).trim();
    const draftAvatar = (profileDraft.avatar_url ?? currentAvatar).trim();
    return draftName !== currentName || draftUsername !== currentUsername || draftAvatar !== currentAvatar;
}

function updateProfileSaveState() {
    const btn = document.getElementById('profile-save-btn');
    const cancelBtn = document.getElementById('profile-cancel-btn');
    if (!btn || !cancelBtn) return;
    const changed = hasProfileChanges();
    btn.style.display = 'block'; // Always show
    btn.disabled = !changed;
    cancelBtn.style.display = 'block'; // Always show
    cancelBtn.disabled = !changed;
}

async function compressImageToDataUrl(file, size = 256, quality = 0.85) {
    const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('Failed to read image'));
        reader.readAsDataURL(file);
    });

    const img = await new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error('Invalid image'));
        image.src = dataUrl;
    });

    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#0a86ff';
    ctx.fillRect(0, 0, size, size);

    const minSide = Math.min(img.width, img.height);
    const sx = Math.floor((img.width - minSide) / 2);
    const sy = Math.floor((img.height - minSide) / 2);
    ctx.drawImage(img, sx, sy, minSide, minSide, 0, 0, size, size);

    return canvas.toDataURL('image/jpeg', quality);
}

function cancelProfileChanges() {
    profileDraft = { name: null, username: null, avatar_url: null };
    renderProfileCard();
    const fileInput = document.getElementById('profile-avatar-input');
    if (fileInput) fileInput.value = '';
    updateProfileSaveState();
}

async function updateProfile(name, username) {
    const payload = {};
    const newName = (name || '').trim();
    const newUsername = (username || '').trim();
    const newAvatar = (profileDraft.avatar_url || '').trim();

    if (!newName || !newUsername) {
        throw new Error('Name and username cannot be empty');
    }

    // Always include values in payload if they are changed or if we want to force update
    if (newName !== (currentUser?.name || '').trim()) payload.name = newName;
    if (newUsername !== (currentUser?.username || '').trim()) payload.username = newUsername;
    
    // CRITICAL: Handle avatar_url specifically
    if (profileDraft.avatar_url !== null) {
        payload.avatar_url = newAvatar; // This is the Base64 from the cropper
    }

    if (Object.keys(payload).length === 0) {
        return { name: currentUser?.name, username: currentUser?.username, avatar_url: currentUser?.avatar_url };
    }

    const result = await apiFetch('/identity/profile', {
        method: 'PATCH',
        body: JSON.stringify(payload)
    });

    // Update LOCAL state immediately
    currentUser.name = result.name;
    currentUser.username = result.username;
    currentUser.avatar_url = result.avatar_url || null;

    // Force update UI elements
    const headerName = document.getElementById('user-display-name');
    if (headerName) headerName.textContent = currentUser.name || currentUser.username;

    // Reset draft and re-render
    profileDraft = { name: null, username: null, avatar_url: null };
    renderProfileCard();
    updateProfileSaveState();
    
    // Update Supabase metadata as well so it persists across sessions
    if (supabaseClient) {
        await supabaseClient.auth.updateUser({
            data: { 
                name: currentUser.name,
                username: currentUser.username,
                avatar_url: currentUser.avatar_url 
            }
        });
    }

    return result;
}

function showView(viewId) {
    currentView = viewId;
    localStorage.setItem('tm_last_view', viewId);
    
    // UI Update
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const target = document.getElementById(`view-${viewId}`);
    if (target) target.classList.add('active');
    
    document.querySelectorAll('.nav-item').forEach(item => {
        const onClickAttr = item.getAttribute('onclick');
        if (onClickAttr && onClickAttr.includes(viewId)) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    syncBottomNavIndicator(viewId);

    // Scroll content to top
    const content = document.getElementById('content');
    if (content) {
        content.scrollTop = 0;
        window.scrollTo(0, 0);
        lastScrollTop = 0;
        const topBar = document.querySelector('.top-bar');
        if (topBar) topBar.classList.remove('hidden');
        updateScrollProgress(content);
        // Attach scroll listener once
        if (!content.dataset.scrollBound) {
            content.addEventListener('scroll', handleContentScroll);
            content.dataset.scrollBound = "true";
        }
    }

    if (!document.body.dataset.windowScrollBound) {
        window.addEventListener('scroll', handleWindowScroll, { passive: true });
        document.body.dataset.windowScrollBound = "true";
    }

    // Load Data
    if (viewId === 'reports') loadReports();
    if (viewId === 'me') loadMe();
    if (viewId === 'tasks') {
        if (currentTasksGoalsTab === 'habits') loadHabits();
        else if (currentTasksGoalsTab === 'goals') loadGoals();
        else loadTasks();
    }
    if (viewId === 'goals') loadGoals();
    if (viewId === 'insights') loadInsights();
    if (viewId === 'settings') applyTheme(); // Sync theme switch state
}

function getBottomNavViewOrder() {
    const nav = document.querySelector('.bottom-nav');
    if (!nav) return [];
    const items = Array.from(nav.querySelectorAll('.nav-item'));
    const order = [];
    for (const item of items) {
        const handler = item.getAttribute('onclick') || '';
        const match = handler.match(/showView\('([^']+)'\)/);
        if (match && match[1]) order.push(match[1]);
    }
    return order;
}

function ensureBottomNavIndicator() {
    const nav = document.querySelector('.bottom-nav');
    if (!nav) return null;
    let indicator = nav.querySelector('.nav-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'nav-indicator';
        indicator.setAttribute('aria-hidden', 'true');
        const glow = nav.querySelector('.bottom-nav-glow');
        if (glow && glow.nextSibling) {
            nav.insertBefore(indicator, glow.nextSibling);
        } else {
            nav.insertBefore(indicator, nav.firstChild);
        }
    }
    nav.classList.add('has-indicator');
    return indicator;
}

function setBottomNavIndicatorOffset(nav, indicator, offsetPx) {
    indicator.style.transform = `translate(-50%, -50%) translateX(${offsetPx}px)`;
    nav.classList.add('has-indicator');
}

function syncBottomNavIndicator(viewId) {
    const nav = document.querySelector('.bottom-nav');
    if (!nav) return;
    const indicator = ensureBottomNavIndicator();
    if (!indicator) return;
    const items = Array.from(nav.querySelectorAll('.nav-item'));
    const targetItem = items.find(item => (item.getAttribute('onclick') || '').includes(`'${viewId}'`));
    if (!targetItem) return;
    const navRect = nav.getBoundingClientRect();
    const itemRect = targetItem.getBoundingClientRect();
    const centerX = (itemRect.left + itemRect.right) / 2;
    const offset = centerX - (navRect.left + navRect.width / 2);
    setBottomNavIndicatorOffset(nav, indicator, offset);
}

function initBottomNavDragSwitch() {
    const nav = document.querySelector('.bottom-nav');
    if (!nav) return;
    if (nav.dataset.dragSwitchInit === 'true') return;
    nav.dataset.dragSwitchInit = 'true';

    const indicator = ensureBottomNavIndicator();
    let viewOrder = getBottomNavViewOrder();

    let startX = 0;
    let startY = 0;
    let pointerId = null;
    let dragging = false;
    let blockClickUntil = 0;
    let rafId = 0;
    let pendingX = 0;
    let pendingY = 0;

    function isMobile() {
        return window.innerWidth <= 768;
    }

    function computeNearestIndex(clientX) {
        const items = Array.from(nav.querySelectorAll('.nav-item'));
        const centers = items.map(item => {
            const r = item.getBoundingClientRect();
            return (r.left + r.right) / 2;
        });
        let bestIdx = 0;
        let bestDist = Infinity;
        for (let i = 0; i < centers.length; i++) {
            const d = Math.abs(centers[i] - clientX);
            if (d < bestDist) {
                bestDist = d;
                bestIdx = i;
            }
        }
        return bestIdx;
    }

    function updateIndicatorFromClientX(clientX) {
        if (!indicator) return;
        const navRect = nav.getBoundingClientRect();
        const clampedX = Math.max(navRect.left, Math.min(navRect.right, clientX));
        const offset = clampedX - (navRect.left + navRect.width / 2);
        setBottomNavIndicatorOffset(nav, indicator, offset);
    }

    function scheduleMove(clientX, clientY) {
        pendingX = clientX;
        pendingY = clientY;
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            rafId = 0;
            handleMoveFrame(pendingX, pendingY);
        });
    }

    function handleMoveFrame(clientX, clientY) {
        const dx = clientX - startX;
        const dy = clientY - startY;

        if (!dragging) {
            if (Math.abs(dx) > 5 && Math.abs(dx) > Math.abs(dy) * 0.8) { // Lower threshold for faster drag
                dragging = true;
                nav.classList.add('is-dragging');
            } else {
                return;
            }
        }

        updateIndicatorFromClientX(clientX);

        const idx = computeNearestIndex(clientX);
        const nextView = viewOrder[idx];
        if (nextView && nextView !== currentView) {
            showView(nextView);
        }
    }

    nav.addEventListener('pointerdown', (e) => {
        if (!isMobile()) return;
        if (e.pointerType !== 'touch') return;
        pointerId = e.pointerId;
        startX = e.clientX;
        startY = e.clientY;
        dragging = false;
        try { nav.setPointerCapture(pointerId); } catch (_) {}
    }, { passive: true });

    nav.addEventListener('pointermove', (e) => {
        if (!isMobile()) return;
        if (pointerId === null || e.pointerId !== pointerId) return;
        scheduleMove(e.clientX, e.clientY);
        if (dragging) e.preventDefault();
    }, { passive: false });

    function endPointer(e) {
        if (pointerId === null || e.pointerId !== pointerId) return;
        pointerId = null;
        if (dragging) {
            blockClickUntil = Date.now() + 350;
            nav.classList.remove('is-dragging');
            syncBottomNavIndicator(currentView);
        }
        dragging = false;
    }

    nav.addEventListener('pointerup', endPointer, { passive: true });
    nav.addEventListener('pointercancel', endPointer, { passive: true });

    nav.addEventListener('click', (e) => {
        if (!isMobile()) return;
        if (Date.now() < blockClickUntil) {
            e.preventDefault();
            e.stopPropagation();
        }
    }, true);

    window.addEventListener('resize', () => {
        viewOrder = getBottomNavViewOrder();
        syncBottomNavIndicator(currentView);
    });
}

function focusInput(id) {
    const el = document.getElementById(id);
    if (el) {
        el.focus();
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function enableEdit(id) {
    const el = document.getElementById(id);
    if (el) {
        el.removeAttribute('readonly');
        el.focus();
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Optional: add a class to show it's editable
        el.classList.add('editable');
    }
}


async function loadInsights() {
    try {
        let url = `/score/history?days=30`;
        if (currentUser.user_id && Number.isInteger(currentUser.user_id)) {
            url += `&user_id=${currentUser.user_id}`;
        }
        const history = await apiFetch(url);
        renderInsights(history);
    } catch (err) {
        console.error('Insights load failed', err);
    }
}

function renderInsights(history) {
    // 1. Pattern Detection Logic
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayStats = dayNames.map(name => ({ name, count: 0, completed: 0 }));
    const categoryStats = {};

    history.forEach(entry => {
        const date = new Date(entry.date);
        const dayIdx = date.getDay();
        dayStats[dayIdx].count++;
        if (entry.success_rate > 0.5) dayStats[dayIdx].completed++;
        
        // We'd need task-level history for better hour/category insights
        // For now, let's use the provided daily history entry
    });

    const bestDayIdx = dayStats.reduce((best, curr, idx) => curr.completed > dayStats[best].completed ? idx : best, 0);
    
    document.getElementById('insight-best-day').textContent = dayNames[bestDayIdx];
    document.getElementById('insight-best-hour').textContent = '09:00 - 11:00'; // Intelligent placeholder
    document.getElementById('insight-failure-pattern').textContent = t('failure_pattern') + ' "Health"'; // Example

    // 2. Achievements
    const streak = parseInt(document.getElementById('streak-value').textContent) || 0;
    const achievements = [
        { id: 'early_bird', name: 'Early Bird', icon: '🌅', unlocked: true },
        { id: 'streak_3', name: '3 Day Streak', icon: '🔥', unlocked: streak >= 3 },
        { id: 'master', name: 'Task Master', icon: '🏆', unlocked: streak >= 7 }
    ];
    
    const list = document.getElementById('achievements-list');
    list.innerHTML = achievements.map(a => `
        <div class="achievement-badge ${a.unlocked ? 'unlocked' : ''}">
            <span class="icon">${a.icon}</span>
            <span class="name">${a.name}</span>
        </div>
    `).join('');
}

// --- Calendar Logic ---
async function renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    const title = document.getElementById('calendar-month-year');
    if (!grid || !title) return;

    grid.innerHTML = '';
    const month = calendarDate.getMonth();
    const year = calendarDate.getFullYear();

    const monthNames = [t('january'), t('february'), t('march'), t('april'), t('may'), t('june'), t('july'), t('august'), t('september'), t('october'), t('november'), t('december')];
    title.textContent = `${monthNames[month]} ${year}`;

    // Days Labels
    const days = [t('mon'), t('tue'), t('wed'), t('thu'), t('fri'), t('sat'), t('sun')];
    days.forEach(d => grid.innerHTML += `<div class="calendar-day-label">${d}</div>`);

    // Get tasks for the month
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    // ISO format for API
    const startStr = firstDay.toISOString().split('T')[0];
    const endStr = lastDay.toISOString().split('T')[0];
    
    try {
        calendarTasks = await apiFetch(`/tasks/range?start_date=${startStr}&end_date=${endStr}`);
    } catch (err) {
        console.error('Failed to load calendar tasks', err);
    }

    const firstDayIdx = (firstDay.getDay() + 6) % 7; // Monday start
    const daysInMonth = lastDay.getDate();
    const todayStr = new Date().toISOString().split('T')[0];

    // Padding for previous month
    for (let i = 0; i < firstDayIdx; i++) {
        grid.innerHTML += `<div class="calendar-day other-month"></div>`;
    }

    // Days in current month
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const hasTasks = calendarTasks.some(t => t.date === dateStr);
        const isToday = dateStr === todayStr;
        
        const dayEl = document.createElement('div');
        dayEl.className = `calendar-day ${isToday ? 'today' : ''} ${hasTasks ? 'has-tasks' : ''}`;
        dayEl.textContent = d;
        dayEl.onclick = () => renderDayTasks(dateStr);
        grid.appendChild(dayEl);
    }
}

function changeMonth(delta) {
    calendarDate.setMonth(calendarDate.getMonth() + delta);
    renderCalendar();
}

function renderDayTasks(dateStr) {
    const container = document.getElementById('day-tasks-container');
    if (!container) return;

    // Highlight active day
    document.querySelectorAll('.calendar-day').forEach(el => {
        if (el.textContent == parseInt(dateStr.split('-')[2])) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    const tasks = calendarTasks.filter(t => t.date === dateStr);
    
    if (tasks.length === 0) {
        container.innerHTML = `<div class="card"><p style="text-align:center;">${t('no_tasks')}</p></div>`;
        return;
    }

    container.innerHTML = `<h3>Tasks for ${dateStr}</h3>`;
    tasks.forEach(task => {
        const card = document.createElement('div');
        card.className = `task-card ${task.status}`;
        card.innerHTML = `
            <div class="task-info">
                <h3>${task.title}</h3>
                <p>${task.time || ''} | ${task.category}</p>
            </div>
            <div class="status-badge ${task.status}">${t(task.status)}</div>
        `;
        container.appendChild(card);
    });
}

// --- Notification Logic ---
function checkReminders() {
    const hasTasks = cachedTasks && cachedTasks.length > 0;
    const hasHabits = cachedHabits && cachedHabits.length > 0;
    if (!hasTasks && !hasHabits) return;
    
    const now = new Date();
    
    if (hasTasks) {
        cachedTasks.forEach(task => {
            if (task.status !== 'pending' || !task.time) return;
            const [h, m] = task.time.split(':').map(Number);
            const taskTime = new Date();
            taskTime.setHours(h, m, 0, 0);
            const diffMinutes = (taskTime - now) / 60000;
            if (diffMinutes >= 0 && diffMinutes <= 5 && !notifiedTasks.has(task.id)) {
                showNotification(task);
                notifiedTasks.add(task.id);
            }
        });
    }

    if (hasHabits) {
        cachedHabits.forEach(habit => {
            if (!habit.is_due_today || habit.today_status === 'completed' || !habit.preferred_time) return;
            const [h, m] = habit.preferred_time.split(':').map(Number);
            const habitTime = new Date();
            habitTime.setHours(h, m, 0, 0);
            const diffMinutes = (habitTime - now) / 60000;
            if (diffMinutes >= 0 && diffMinutes <= 10 && !notifiedHabits.has(habit.id)) {
                showToast(`Habit reminder: ${habit.title}`, 'info');
                notifiedHabits.add(habit.id);
            } else if (diffMinutes < -90 && !notifiedHabits.has(`nudge-${habit.id}`)) {
                showToast(`Gentle nudge: keep "${habit.title}" on track today`, 'info');
                notifiedHabits.add(`nudge-${habit.id}`);
            }
        });
    }
}

function showNotification(task) {
    showToast(`${t('reminder')}: ${task.title} @ ${task.time}`, 'info');
    // Sound could be added here
}

// --- Real Insights Upgrade ---
async function loadInsights() {
    showLoading(true);
    try {
        // Fetch all user tasks for comprehensive insights
        const tasks = await apiFetch(`/tasks/range?start_date=2000-01-01&end_date=2100-12-31`);
        renderRealInsights(tasks);
    } catch (err) {
        console.error('Insights load failed', err);
    } finally {
        showLoading(false);
    }
}

function renderRealInsights(tasks) {
    if (!tasks || tasks.length === 0) return;

    const completed = tasks.filter(t => t.status === 'completed');
    const failed = tasks.filter(t => t.status === 'failed');
    const rate = tasks.length > 0 ? (completed.length / (completed.length + failed.length || 1)) * 100 : 0;

    // Most productive day
    const dayCounts = {};
    completed.forEach(t => {
        const d = new Date(t.date).getDay();
        dayCounts[d] = (dayCounts[d] || 0) + 1;
    });
    const dayNames = [t('sun'), t('mon'), t('tue'), t('wed'), t('thu'), t('fri'), t('sat')];
    let bestDayIdx = 0;
    for (let d in dayCounts) if (dayCounts[d] > (dayCounts[bestDayIdx] || 0)) bestDayIdx = d;

    // Most active hours
    const hourCounts = {};
    tasks.forEach(t => {
        if (t.time) {
            const h = t.time.split(':')[0];
            hourCounts[h] = (hourCounts[h] || 0) + 1;
        }
    });
    let bestHour = '00';
    for (let h in hourCounts) if (hourCounts[h] > (hourCounts[bestHour] || 0)) bestHour = h;

    // Update UI
    document.getElementById('insight-best-day').textContent = dayNames[bestDayIdx];
    document.getElementById('insight-best-hour').textContent = `${bestHour}:00`;
    
    // Update stats grid (if exists)
    const successVal = document.getElementById('success-value');
    if (successVal) successVal.textContent = `${rate.toFixed(0)}%`;

    // Failure patterns
    const failCategories = {};
    failed.forEach(t => failCategories[t.category] = (failCategories[t.category] || 0) + 1);
    let worstCat = 'None';
    for (let c in failCategories) if (failCategories[c] > (failCategories[worstCat] || 0)) worstCat = c;
    document.getElementById('insight-failure-pattern').textContent = worstCat;
}

// Override showView to handle Calendar load
const originalShowView = showView;
showView = function(viewId) {
    originalShowView(viewId);
    if (viewId === 'calendar') renderCalendar();
};

// --- API Calls ---
async function apiFetch(endpoint, options = {}) {
    // Ensure endpoint starts with /api/ if it doesn't already
    const apiEndpoint = endpoint.startsWith('/api') ? endpoint : `/api${endpoint}`;
    
    options.headers = {
        ...options.headers,
        'Content-Type': 'application/json'
    };
    
    if (supabaseAccessToken) {
        options.headers['Authorization'] = `Bearer ${supabaseAccessToken}`;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${apiEndpoint}`, options);
        if (response.status === 401) {
            logout();
            showToast(t('session_expired'), 'error');
            throw new Error('Session expired');
        }
        if (!response.ok) {
            const error = await response.json();
            // Handle Pydantic validation errors
            let message = t('error_occurred');
            if (typeof error.detail === 'string') {
                message = error.detail;
            } else if (Array.isArray(error.detail)) {
                message = error.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join('\n');
            }
            throw new Error(message);
        }
        return response.json();
    } catch (err) {
        if (err.message !== 'Session expired') {
            showToast(err.message, 'error');
        }
        throw err;
    }
}

// --- Auth Actions ---
function normalizeSupabaseError(err) {
    if (!err) return t('error_occurred');
    if (typeof err === 'string') return err;
    return err.message || err.error_description || err.description || t('error_occurred');
}

async function login(email, password) {
    if (!supabaseClient) return;
    setAuthBusy(true);
    showAuthError('');
    try {
        const { data, error } = await supabaseClient.auth.signInWithPassword({
            email: (email || '').trim(),
            password: password || ''
        });
        if (error) throw error;
        await handleAuthSessionChange('SIGNED_IN', data.session);
    } catch (err) {
        showAuthError(normalizeSupabaseError(err));
    } finally {
        setAuthBusy(false);
    }
}

async function signup(name, username, email, password) {
    if (!supabaseClient) return;
    setAuthBusy(true);
    showAuthError('');
    try {
        const { data, error } = await supabaseClient.auth.signUp({
            email: (email || '').trim(),
            password: password || '',
            options: {
                data: {
                    name: (name || '').trim(),
                    username: (username || '').trim()
                },
                emailRedirectTo: window.location.origin
            }
        });
        if (error) throw error;

        pendingVerificationEmail = (email || '').trim();
        if (data.session) {
            await handleAuthSessionChange('SIGNED_IN', data.session);
            return;
        }

        renderLogin();
        setAuthView('verify');
        showToast(t('verify_email_title'), 'success');
    } catch (err) {
        showAuthError(normalizeSupabaseError(err));
    } finally {
        setAuthBusy(false);
    }
}

async function signInWithGoogle() {
    if (!supabaseClient) return;
    setAuthBusy(true);
    showAuthError('');
    try {
        const { error } = await supabaseClient.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: window.location.origin,
                queryParams: { prompt: 'select_account' }
            }
        });
        if (error) throw error;
    } catch (err) {
        setAuthBusy(false);
        showAuthError(normalizeSupabaseError(err));
    }
}

async function sendPasswordReset(email) {
    if (!supabaseClient) return;
    setAuthBusy(true);
    showAuthError('');
    try {
        const { error } = await supabaseClient.auth.resetPasswordForEmail((email || '').trim(), {
            redirectTo: window.location.origin
        });
        if (error) throw error;
        showToast(t('send_reset_link'), 'success');
        setAuthView('forgot');
    } catch (err) {
        showAuthError(normalizeSupabaseError(err));
    } finally {
        setAuthBusy(false);
    }
}

async function resendVerificationEmail() {
    if (!supabaseClient) return;
    const email = pendingVerificationEmail || document.getElementById('signup-email')?.value?.trim() || '';
    if (!email) return;
    setAuthBusy(true);
    showAuthError('');
    try {
        const { error } = await supabaseClient.auth.resend({ type: 'signup', email });
        if (error) throw error;
        showToast(t('resend_verification'), 'success');
    } catch (err) {
        showAuthError(normalizeSupabaseError(err));
    } finally {
        setAuthBusy(false);
    }
}

async function verifyEmailCode() {
    if (!supabaseClient) return;
    const email =
        pendingVerificationEmail ||
        document.getElementById('signup-email')?.value?.trim() ||
        document.getElementById('login-email')?.value?.trim() ||
        '';
    const code = document.getElementById('verify-otp')?.value?.trim() || '';
    if (!email || !code) return;
    setAuthBusy(true);
    showAuthError('');
    try {
        const { data, error } = await supabaseClient.auth.verifyOtp({
            email,
            token: code,
            type: 'email'
        });
        if (error) throw error;
        pendingVerificationEmail = null;
        await handleAuthSessionChange('VERIFY_OTP', data.session);
    } catch (err) {
        showAuthError(normalizeSupabaseError(err));
    } finally {
        setAuthBusy(false);
    }
}

async function verifyRecoveryCode() {
    if (!supabaseClient) return;
    const email = document.getElementById('forgot-email')?.value?.trim() || '';
    const code = document.getElementById('recovery-otp')?.value?.trim() || '';
    if (!email || !code) return;
    setAuthBusy(true);
    showAuthError('');
    try {
        const { data, error } = await supabaseClient.auth.verifyOtp({
            email,
            token: code,
            type: 'recovery'
        });
        if (error) throw error;
        await handleAuthSessionChange('PASSWORD_RECOVERY', data.session);
    } catch (err) {
        showAuthError(normalizeSupabaseError(err));
    } finally {
        setAuthBusy(false);
    }
}

async function updatePassword(newPassword, confirmPassword) {
    if (!supabaseClient) return;
    showAuthError('');
    if (!newPassword || newPassword.length < 8) {
        showAuthError('Password must be at least 8 characters');
        return;
    }
    if (newPassword !== confirmPassword) {
        showAuthError('Passwords do not match');
        return;
    }
    setAuthBusy(true);
    try {
        const { error } = await supabaseClient.auth.updateUser({ password: newPassword });
        if (error) throw error;
        const { data } = await supabaseClient.auth.getSession();
        await handleAuthSessionChange('USER_UPDATED', data.session);
        showToast(t('update_password'), 'success');
    } catch (err) {
        showAuthError(normalizeSupabaseError(err));
    } finally {
        setAuthBusy(false);
    }
}

function resetUiToDefaults() {
    currentView = 'tasks';
    currentTasksGoalsTab = 'tasks';
    calendarDate = new Date();
    dashboardCalendarDate = new Date();
    cachedTasks = [];
    cachedGoals = [];
    cachedHabits = [];
    calendarTasks = [];
    notifiedTasks = new Set();
    notifiedHabits = new Set();
    currentGoalForReflection = null;
    identityInitialized = false;
    identitySnapshot = { level: 1, unlockedBadgeIds: [] };
    smartPersonalizationCache = { timestamp: 0, data: null };

    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
    document.querySelectorAll('.hamburger').forEach(h => h.classList.remove('active'));
    document.body.classList.remove('sidebar-open');
}

function clearUrlTokens() {
    if (window.location.hash) {
        window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
    }
}

function logout() {
    (async () => {
        showLoading(true);
        try {
            await supabaseClient?.auth?.signOut();
        } finally {
            currentUser = null;
            supabaseSession = null;
            supabaseAccessToken = null;
            pendingVerificationEmail = null;
            resetUiToDefaults();
            clearUrlTokens();
            renderLogin();
            setAuthView('login');
            showLoading(false);
        }
    })();
}

function getScoreLabel(score) {
    if (score >= 100) return { text: 'Excellent', icon: '🏆', class: 'excellent' };
    if (score >= 60) return { text: 'Good', icon: '✨', class: 'good' };
    if (score >= 30) return { text: 'Average', icon: '⚡', class: 'average' };
    return { text: 'Low', icon: '⚠️', class: 'low' };
}

function getBadgeImageSrc(scoreClass) {
    const map = {
        excellent: 'badge_excellent.png',
        good: 'badge_good.png',
        average: 'badge_average.png',
        low: 'badge_low.png',
    };
    const name = map[scoreClass] || map.low;
    return `/static/${name}?v=7`;
}

// --- Reports & Me Logic ---
async function loadReports() {
    try {
        const today = new Date().toISOString().split('T')[0];

        const scorePromise = apiFetch('/score/daily', {
            method: 'POST',
            body: JSON.stringify({ user_id: currentUser.user_id, day: today })
        });

        const calendarPromise = renderDashboardCalendar();

        const score = await scorePromise;
        await calendarPromise;

        renderHeroMetrics(score);

        const progressFill = document.getElementById('daily-progress-fill');
        if (progressFill) progressFill.style.width = `${score.success_rate * 100}%`;

        const multBadge = document.getElementById('multiplier-badge');
        if (multBadge) {
            if (score.multiplier > 1.0) {
                multBadge.textContent = `${score.multiplier.toFixed(1)}x Boost${score.goal_bonus > 0 ? ` +${score.goal_bonus.toFixed(0)} Goal` : ''}`;
                multBadge.style.display = 'inline-block';
            } else {
                multBadge.style.display = 'none';
            }
        }

        await Promise.all([loadWeeklySummary(), loadTodayHabits()]);
    } catch (err) {
        console.error('Reports load failed', err);
    }
}

async function loadMe() {
    try {
        renderProfileCard();
        
        const today = new Date().toISOString().split('T')[0];
        
        // Parallelize everything
        const promises = [
            loadIdentityProfile(),
            loadDashboardPersonalization(),
            loadScoreComparison(),
            loadMissedTasks()
        ];

        const pieEl = document.getElementById('task-pie-chart');
        if (pieEl) {
            let tasksUrl = `/tasks?day=${today}`;
            if (currentUser.user_id && Number.isInteger(currentUser.user_id)) {
                tasksUrl += `&user_id=${currentUser.user_id}`;
            }
            promises.push(apiFetch(tasksUrl).then(tasks => updateTaskChart(tasks)));
        }

        const trendEl = document.getElementById('weekly-trend-chart');
        if (trendEl) {
            promises.push(loadWeeklyTrend());
        }

        await Promise.all(promises);
    } catch (err) {
        console.error('Me load failed', err);
    }
}

async function loadDashboard() {
    await Promise.all([loadReports(), loadMe()]);
}

function renderHeroMetrics(score) {
    const container = document.getElementById('dashboard-hero-metrics');
    if (!container) return;

    const label = getScoreLabel(score.score);
    const scoreVal = score.score.toFixed(1);
    const isLightMode = document.body.classList.contains('light-mode');
    
    // Use pre-loaded Base64 assets
    const img1 = ASSETS.img1;
    const img4 = ASSETS.img4;
    const img6 = ASSETS.img6;

    const trustBg = isLightMode
        ? 'linear-gradient(135deg, #bfdbfe 0%, #2563eb 30%, #1e293b 100%)'
        : 'radial-gradient(circle at bottom right, #005c99 0%, #004a7a 20%, #003761 40%, #002542 60%, #001221 80%, #000000 100%)';

    const streakBg = isLightMode
        ? 'linear-gradient(135deg, #fed7aa 0%, #ea580c 30%, #451a03 100%)'
        : 'radial-gradient(circle at bottom right, #993d00 0%, #7a3100 20%, #5c2700 40%, #3d1a00 60%, #1f0d00 80%, #000000 100%)';

    const successBg = isLightMode
        ? 'linear-gradient(135deg, #bbf7d0 0%, #16a34a 30%, #052e16 100%)'
        : 'radial-gradient(circle at bottom right, #009952 0%, #007a42 20%, #005c34 40%, #003d27 60%, #001f1a 80%, #000000 100%)';

    const progressTrackBg = isLightMode ? 'rgba(255,255,255,0.22)' : 'rgba(255,255,255,0.1)';
    const progressTrackBorder = isLightMode ? 'rgba(255,255,255,0.28)' : 'rgba(255,255,255,0.2)';

    container.innerHTML = `
        <!-- Card 1: Trust Score -->
        <div class="hero-metric hero-metric--trust" style="background: ${trustBg} !important; isolation: isolate !important;">
            <div class="hero-metric-content">
                <div class="hero-metric-icon">
                    <img src="${img1}">
                </div>
                <div class="hero-metric-label">Self Trust Score</div>
                <div class="hero-metric-value">${scoreVal}</div>
                <img class="trust-score-badge" src="${getBadgeImageSrc(label.class)}" alt="${label.text}">
            </div>
        </div>

        <!-- Card 2: Streak -->
        <div class="hero-metric" style="background: ${streakBg} !important; isolation: isolate !important;">
            <div class="hero-metric-content">
                <div class="hero-metric-icon">
                    <img src="${img4}">
                </div>
                <div class="hero-metric-label">Current Streak</div>
                <div class="hero-metric-value">${score.streak}</div>
            </div>
        </div>

        <!-- Card 3: Success -->
        <div class="hero-metric" style="background: ${successBg} !important; isolation: isolate !important;">
            <div class="hero-metric-content">
                <div class="hero-metric-icon">
                    <img src="${img6}">
                </div>
                <div class="hero-metric-label">Success Rate</div>
                <div class="hero-metric-value">${(score.success_rate * 100).toFixed(0)}%</div>
                <div style="margin-top: 40px; width: 100%; background: ${progressTrackBg}; height: 8px; border-radius: 10px; overflow: hidden; border: 1px solid ${progressTrackBorder};">
                    <div style="width: ${score.success_rate * 100}%; height: 100%; background: #4ade80; box-shadow: none; border-radius: 10px;"></div>
                </div>
            </div>
        </div>
    `;
}

async function getSmartPersonalization(forceRefresh = false) {
    const now = Date.now();
    if (!forceRefresh && smartPersonalizationCache.data && (now - smartPersonalizationCache.timestamp) < 60000) {
        return smartPersonalizationCache.data;
    }
    const data = await apiFetch('/insights/smart');
    smartPersonalizationCache = { timestamp: now, data };
    return data;
}

function renderDashboardPersonalization(smartData) {
    const listEl = document.getElementById('for-you-list');
    const pressureEl = document.getElementById('for-you-pressure');
    if (!listEl || !pressureEl) return;

    const messages = (smartData.for_you || []).slice(0, 4);
    listEl.innerHTML = messages.map(m => `<div class="for-you-item">${m}</div>`).join('');
    if (messages.length === 0) {
        listEl.innerHTML = `<div class="for-you-item">Keep completing tasks to unlock personalized guidance</div>`;
    }

    const pressure = smartData.pressure_level || 'normal';
    pressureEl.textContent = pressure === 'light' ? 'Low Pressure' : pressure === 'high' ? 'High Momentum' : 'Balanced';
    pressureEl.className = `priority-badge ${pressure === 'light' ? 'priority-low' : pressure === 'high' ? 'priority-high' : 'priority-medium'}`;
}

async function loadDashboardPersonalization() {
    try {
        const smartData = await getSmartPersonalization();
        renderDashboardPersonalization(smartData);
    } catch (err) {
        console.error('Dashboard personalization load failed', err);
    }
}

async function loadScoreComparison() {
    try {
        const history = await apiFetch('/score/history');
        const today = new Date().toISOString().split('T')[0];
        const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
        
        const todayScore = history.find(h => h.date === today);
        const yesterdayScore = history.find(h => h.date === yesterday);
        
        const comparisonEl = document.getElementById('score-comparison');
        const comparisonText = document.getElementById('score-comparison-text');
        
        if (todayScore && yesterdayScore) {
            const diff = todayScore.score - yesterdayScore.score;
            comparisonEl.style.display = 'block';
            
            if (diff > 0) {
                comparisonEl.className = 'card score-comparison improved';
                comparisonText.textContent = `You improved by ${diff.toFixed(1)} points compared to yesterday! 🎉`;
            } else if (diff < 0) {
                comparisonEl.className = 'card score-comparison dropped';
                comparisonText.textContent = `You dropped by ${Math.abs(diff).toFixed(1)} points compared to yesterday`;
            } else {
                comparisonEl.style.display = 'none';
            }
        } else {
            comparisonEl.style.display = 'none';
        }
    } catch (err) {
        console.error('Score comparison load failed', err);
        document.getElementById('score-comparison').style.display = 'none';
    }
}

async function loadMissedTasks() {
    try {
        const data = await apiFetch('/tasks/missed');
        const alertEl = document.getElementById('missed-tasks-alert');
        const textEl = document.getElementById('missed-tasks-text');
        
        if (data.count > 0) {
            alertEl.style.display = 'block';
            let message = `You missed ${data.count} task${data.count > 1 ? 's' : ''}`;
            
            const today = new Date().toISOString().split('T')[0];
            let url = `/tasks?day=${today}`;
            if (currentUser.user_id && Number.isInteger(currentUser.user_id)) {
                url += `&user_id=${currentUser.user_id}`;
            }
            const todayTasks = await apiFetch(url);
            const hasCompletedToday = todayTasks.some(t => t.status === 'completed');
            const streakValue = parseInt(document.getElementById('streak-value').textContent) || 0;
            
            if (streakValue > 0 && !hasCompletedToday) {
                message += ` — You are at risk of losing your streak! ⚠️`;
            }
            
            textEl.textContent = message;
        } else {
            alertEl.style.display = 'none';
        }
    } catch (err) {
        console.error('Missed tasks load failed', err);
        document.getElementById('missed-tasks-alert').style.display = 'none';
    }
}

async function loadWeeklySummary() {
    try {
        const data = await apiFetch('/score/weekly-summary');
        const container = document.getElementById('weekly-summary');
        const content = document.getElementById('weekly-summary-content');
        
        container.style.display = 'block';
        
        content.innerHTML = `
            <div class="weekly-summary-stats">
                <div class="weekly-summary-stat">
                    <span class="label">Total Tasks</span>
                    <span class="value">${data.current_week.total_tasks}</span>
                </div>
                <div class="weekly-summary-stat">
                    <span class="label">Completed</span>
                    <span class="value">${data.current_week.completed_tasks}</span>
                </div>
                <div class="weekly-summary-stat">
                    <span class="label">Success Rate</span>
                    <span class="value">${data.current_week.success_rate}%</span>
                </div>
                <div class="weekly-summary-stat">
                    <span class="label">Streak</span>
                    <span class="value">${data.current_week.streak}</span>
                </div>
            </div>
            <div class="weekly-summary-change ${data.success_change >= 0 ? 'positive' : 'negative'}">
                ${data.success_change >= 0 ? '↑' : '↓'} ${Math.abs(data.success_change)}% ${data.success_change >= 0 ? 'improvement' : 'drop'} from last week
            </div>
        `;
    } catch (err) {
        console.error('Weekly summary load failed', err);
    }
}

// --- Insights Logic ---
async function loadInsights() {
    try {
        const smartData = await getSmartPersonalization();
        const container = document.getElementById('smart-insights-container');
        
        const smartMessages = [
            ...(smartData.insights || []),
            ...(smartData.suggestions || []),
            ...(smartData.adaptive_feedback || []),
            ...(smartData.habit_insights || []),
        ].slice(0, 6);
        if (smartMessages.length > 0) {
            container.innerHTML = smartMessages.map(insight => `
                <div class="insight-card">
                    <span class="icon">✨</span>
                    <div class="insight-content">
                        <p style="font-weight: 600; color: var(--text-primary);">${insight}</p>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '';
        }

        const completionRate = document.getElementById('goal-completion-rate');
        const achievedFailed = document.getElementById('goal-achieved-failed');
        const averageTime = document.getElementById('goal-average-time');
        if (completionRate) completionRate.textContent = `${smartData.goal_completion_rate || 0}%`;
        if (achievedFailed) achievedFailed.textContent = `${smartData.goals_achieved || 0} / ${smartData.goals_failed || 0}`;
        if (averageTime) averageTime.textContent = `${smartData.average_completion_time || 0}d`;

        const end = new Date();
        const start = new Date(Date.now() - 120 * 86400000);
        const startStr = start.toISOString().split('T')[0];
        const endStr = end.toISOString().split('T')[0];
        renderRealInsights(await apiFetch(`/tasks/range?start_date=${startStr}&end_date=${endStr}`));
        loadIdentityProfile();
    } catch (err) {
        console.error('Insights load failed', err);
    }
}

async function loadWeeklyTrend() {
    try {
        let url = `/score/history?days=7`;
        if (currentUser.user_id && Number.isInteger(currentUser.user_id)) {
            url += `&user_id=${currentUser.user_id}`;
        }
        const scores = await apiFetch(url);
        updateTrendChart(scores);
    } catch (err) {
        console.error('Trend load failed', err);
    }
}

function updateTrendChart(history) {
    const ctx = document.getElementById('weekly-trend-chart').getContext('2d');
    if (trendChart) trendChart.destroy();

    const labels = history.map(s => s.date.split('-').slice(1).reverse().join('/'));
    const data = history.map(s => s.score);

    const rootStyles = getComputedStyle(document.documentElement);
    const primary = rootStyles.getPropertyValue('--primary').trim() || '#0066FF';
    const primary2 = rootStyles.getPropertyValue('--primary-2').trim() || primary;
    const primary3 = rootStyles.getPropertyValue('--primary-3').trim() || primary;

    const textColor = isDarkMode ? '#FFFFFF' : '#0F172A';
    const bgColor = isDarkMode ? '#111827' : '#FFFFFF';
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';
    const stroke = ctx.createLinearGradient(0, 0, 420, 0);
    stroke.addColorStop(0, primary2);
    stroke.addColorStop(0.5, primary);
    stroke.addColorStop(1, primary3);
    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, isDarkMode ? 'rgba(34, 211, 238, 0.22)' : 'rgba(34, 211, 238, 0.16)');
    gradient.addColorStop(0.45, isDarkMode ? 'rgba(10, 134, 255, 0.16)' : 'rgba(10, 134, 255, 0.12)');
    gradient.addColorStop(1, isDarkMode ? 'rgba(167, 139, 250, 0.05)' : 'rgba(167, 139, 250, 0.03)');
    const fillColor = gradient;

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: t('trust_score'),
                data: data,
                borderColor: stroke,
                backgroundColor: fillColor,
                fill: true,
                tension: 0.35,
                pointRadius: 5,
                pointBackgroundColor: primary2,
                pointBorderColor: bgColor,
                pointBorderWidth: 3,
                pointHoverBackgroundColor: primary3,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    padding: 12,
                    backgroundColor: bgColor,
                    titleColor: textColor,
                    bodyColor: textColor,
                    borderColor: gridColor,
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 150,
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 11, weight: '500' } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: textColor, font: { size: 11, weight: '500' } }
                }
            }
        }
    });
}

function updateTaskChart(tasks) {
    const counts = {
        completed: tasks.filter(t => t.status === 'completed').length,
        failed: tasks.filter(t => t.status === 'failed').length,
        pending: tasks.filter(t => t.status === 'pending').length
    };

    const ctx = document.getElementById('task-pie-chart').getContext('2d');
    
    if (taskChart) {
        taskChart.destroy();
    }

    const textColor = isDarkMode ? '#FFFFFF' : '#0F172A';
    const bgColor = isDarkMode ? '#111827' : '#FFFFFF';
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';
    const pendingColor = isDarkMode ? 'rgba(10, 134, 255, 0.14)' : 'rgba(10, 134, 255, 0.10)';

    taskChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [t('completed'), t('failed'), t('pending')],
            datasets: [{
                data: [counts.completed, counts.failed, counts.pending],
                backgroundColor: ['#22c55e', '#ef4444', pendingColor],
                borderWidth: 4,
                borderColor: bgColor,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: textColor,
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 12, weight: '600' }
                    }
                },
                tooltip: {
                    backgroundColor: bgColor,
                    titleColor: textColor,
                    bodyColor: textColor,
                    borderColor: gridColor,
                    borderWidth: 1,
                    padding: 12,
                    boxPadding: 6,
                    usePointStyle: true
                }
            },
            cutout: '65%'
        }
    });
}


// --- Tasks Logic ---
async function loadTasks() {
    const list = document.getElementById('task-list');
    
    // Performance: If we have cached tasks, show them first
    if (cachedTasks.length > 0) {
        renderTasks(cachedTasks);
    } else if (list.innerHTML === '' || list.querySelector('.empty-state')) {
        list.innerHTML = `
            <div class="task-card skeleton" style="height: 80px; opacity: 0.6;"></div>
            <div class="task-card skeleton" style="height: 80px; opacity: 0.4;"></div>
            <div class="task-card skeleton" style="height: 80px; opacity: 0.2;"></div>
        `;
    }

    try {
        const today = new Date().toISOString().split('T')[0];
        const priority = document.getElementById('filter-priority').value;
        const status = document.getElementById('filter-status').value;
        
        let url = `/tasks?day=${today}`;
        if (currentUser.user_id && Number.isInteger(currentUser.user_id)) {
            url += `&user_id=${currentUser.user_id}`;
        }
        if (priority) url += `&priority=${priority}`;
        if (status) url += `&status=${status}`;

        const tasks = await apiFetch(url);
        cachedTasks = tasks;
        renderTasks(tasks);
    } catch (err) {
        console.error('Tasks load failed', err);
        if (cachedTasks.length === 0) {
            list.innerHTML = `<div class="empty-state"><p class="error-msg">${t('error_occurred')}</p></div>`;
        }
    }
}

function formatHabitDays(habit) {
    if (habit.frequency_type === 'daily') return 'Daily';
    const names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return (habit.frequency_days || []).map(d => names[d] || '').filter(Boolean).join(', ');
}

function renderHabits(habits) {
    const list = document.getElementById('habits-list');
    if (!list) return;
    if (!habits || habits.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <span class="empty-state-icon">🧠</span>
                <h3 class="empty-state-title">No habits yet</h3>
                <p class="empty-state-text">Build consistency with your first recurring habit.</p>
                <button onclick="toggleHabitForm()" class="btn primary">Create Habit</button>
            </div>
        `;
        return;
    }
    list.innerHTML = habits.map(habit => `
        <div class="task-card habit-card">
            <div class="task-info">
                <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                    <h3>${habit.title}</h3>
                    <span class="priority-badge priority-medium">${habit.category}</span>
                    <span class="priority-badge priority-low">🔥 ${habit.streak}</span>
                    <span class="priority-badge priority-low">${habit.consistency_score.toFixed(0)}% consistency</span>
                </div>
                <div class="habit-meta">
                    <span>${formatHabitDays(habit)}</span>
                    ${habit.preferred_time ? `<span>⏰ ${habit.preferred_time}</span>` : ''}
                    <span>Best streak ${habit.best_streak}</span>
                </div>
            </div>
            <div class="task-actions">
                ${habit.today_status === 'completed' ? `
                    <div class="status-badge completed"><span>Completed ✔</span></div>
                ` : habit.today_status === 'skipped' ? `
                    <div class="status-badge failed"><span>Skipped</span></div>
                ` : habit.is_due_today ? `
                    <button class="btn task-btn completed" onclick="trackHabit(${habit.id}, 'completed')">Complete</button>
                    <button class="btn task-btn failed" onclick="trackHabit(${habit.id}, 'skipped')">Skip</button>
                ` : `
                    <div class="status-badge pending"><span>Not scheduled today</span></div>
                `}
            </div>
        </div>
    `).join('');
}

async function loadHabits() {
    try {
        const habits = await apiFetch('/habits');
        cachedHabits = habits;
        renderHabits(habits);
        if (currentView === 'reports') renderTodayHabits(habits);
    } catch (err) {
        const list = document.getElementById('habits-list');
        if (list) list.innerHTML = `<div class="empty-state"><p class="error-msg">${err.message}</p></div>`;
    }
}

function renderTodayHabits(habits) {
    const list = document.getElementById('today-habits-list');
    if (!list) return;
    const dueHabits = (habits || []).filter(h => h.is_due_today);
    if (dueHabits.length === 0) {
        list.innerHTML = `<div class="for-you-item">No habits scheduled for today.</div>`;
        return;
    }
    list.innerHTML = dueHabits.map(habit => `
        <div class="for-you-item">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
                <span>${habit.title} 🔥 ${habit.streak}</span>
                <span>${habit.consistency_score.toFixed(0)}%</span>
            </div>
            <div style="display:flex; gap:0.45rem; margin-top:0.45rem;">
                ${habit.today_status ? `<span class="priority-badge ${habit.today_status === 'completed' ? 'priority-low' : 'priority-high'}">${habit.today_status}</span>` : `
                    <button class="btn task-btn completed" onclick="trackHabit(${habit.id}, 'completed')">Complete</button>
                    <button class="btn task-btn failed" onclick="trackHabit(${habit.id}, 'skipped')">Skip</button>
                `}
            </div>
        </div>
    `).join('');
}

async function loadTodayHabits() {
    if (cachedHabits.length > 0) {
        renderTodayHabits(cachedHabits);
        return;
    }
    try {
        const habits = await apiFetch('/habits');
        cachedHabits = habits;
        renderTodayHabits(habits);
    } catch (err) {
        const list = document.getElementById('today-habits-list');
        if (list) list.innerHTML = `<div class="for-you-item">Unable to load habits now.</div>`;
    }
}

async function trackHabit(habitId, status) {
    const previous = [...cachedHabits];
    cachedHabits = cachedHabits.map(h => h.id === habitId ? { ...h, today_status: status } : h);
    renderHabits(cachedHabits);
    renderTodayHabits(cachedHabits);
    try {
        await apiFetch(`/habits/${habitId}/track`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
        smartPersonalizationCache = { timestamp: 0, data: null };
        await Promise.all([loadHabits(), loadReports()]);
    } catch (err) {
        cachedHabits = previous;
        renderHabits(cachedHabits);
        renderTodayHabits(cachedHabits);
    }
}

function toggleHabitDaysSelector(freq) {
    const group = document.getElementById('habit-days-group');
    if (!group) return;
    group.style.display = freq === 'weekly' ? 'block' : 'none';
}

function getSelectedHabitDays() {
    return Array.from(document.querySelectorAll('#habit-days-group input[type="checkbox"]:checked'))
        .map(el => Number(el.value))
        .filter(v => Number.isInteger(v));
}

function toggleHabitForm() {
    const container = document.getElementById('habit-form-container');
    container.classList.toggle('active');
    if (container.classList.contains('active')) {
        document.getElementById('habit-title').value = '';
        document.getElementById('habit-category').value = 'General';
        document.getElementById('habit-time').value = '';
        document.getElementById('habit-frequency').value = 'daily';
        document.querySelectorAll('#habit-days-group input[type="checkbox"]').forEach(el => { el.checked = false; });
        toggleHabitDaysSelector('daily');
    }
}

async function addHabit() {
    const title = document.getElementById('habit-title').value.trim();
    const category = document.getElementById('habit-category').value.trim() || 'general';
    const frequency = document.getElementById('habit-frequency').value;
    const preferredTime = document.getElementById('habit-time').value || null;
    const frequencyDays = frequency === 'weekly' ? getSelectedHabitDays() : null;
    if (frequency === 'weekly' && (!frequencyDays || frequencyDays.length === 0)) {
        showToast('Select at least one day for weekly habit', 'error');
        return;
    }
    await apiFetch('/habits', {
        method: 'POST',
        body: JSON.stringify({
            title,
            category,
            frequency_type: frequency,
            frequency_days: frequencyDays,
            preferred_time: preferredTime,
        }),
    });
    smartPersonalizationCache = { timestamp: 0, data: null };
    toggleHabitForm();
    await loadHabits();
    showToast('Habit created', 'success');
}

function showSmartSuggestion() {
    const container = document.getElementById('smart-suggestion-container');
    if (!container) return;

    const smart = smartPersonalizationCache.data;
    let suggestion = '';
    if (smart && smart.suggestions && smart.suggestions.length > 0) {
        suggestion = smart.suggestions[0];
    } else {
        const now = new Date();
        const hour = now.getHours();
        if (hour >= 8 && hour <= 10) suggestion = t('best_time_to_create');
        else if (hour >= 14 && hour <= 16) suggestion = t('optimal_time') + " 15:30";
    }

    if (suggestion) {
        container.innerHTML = `
            <div class="suggestion-box">
                <span class="icon">✨</span>
                <p>${suggestion}</p>
            </div>
        `;
    } else {
        container.innerHTML = '';
    }
}

function renderTasks(tasks) {
    const list = document.getElementById('task-list');
    showSmartSuggestion(); // Show suggestion based on time

    if (!tasks || tasks.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <span class="empty-state-icon">📝</span>
                <h3 class="empty-state-title">${t('no_tasks')}</h3>
                <p class="empty-state-text">Start by adding your first task for today.</p>
                <button onclick="toggleTaskForm()" class="btn primary">${t('add_new_task')}</button>
            </div>
        `;
        return;
    }
    
    list.innerHTML = '';
    const today = new Date();
    today.setHours(0,0,0,0);

    tasks.forEach(task => {
        const card = document.createElement('div');
        card.className = `task-card ${task.status}`;
        
        // Risk Detection (Mock logic based on behavior)
        let riskHtml = '';
        if (task.status === 'pending') {
            const isComplex = task.title.length > 40;
            const isHard = task.difficulty === 'hard';
            if (isComplex || isHard) {
                riskHtml = `<span class="task-risk-warning">⚠️ ${isComplex ? t('suggest_simpler') : t('high_risk')}</span>`;
            }
        }

        // Check overdue
        let overdueHtml = '';
        if (task.status === 'pending' && task.due_date) {
            const dueDate = new Date(task.due_date);
            if (dueDate < today) {
                overdueHtml = `<span class="overdue-badge">⚠️ ${t('overdue')}</span>`;
            }
        }

        const recurringIcon = task.recurring !== 'none' ? `<span class="recurring-icon" title="${t(task.recurring)}">🔄</span>` : '';

        card.innerHTML = `
            <div class="task-info">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <h3>${task.title}</h3>
                    <span class="priority-badge priority-${task.priority}">${t(task.priority)}</span>
                </div>
                <div class="task-meta">
                    <p>${task.category} | ${t(task.difficulty)}</p>
                    ${task.goal_id ? `<p>🎯 Linked Goal</p>` : ''}
                    ${recurringIcon}
                    ${task.due_date ? `<p>📅 ${task.due_date}</p>` : ''}
                    ${overdueHtml}
                </div>
                ${riskHtml}
            </div>
            <div class="task-actions">
                ${task.status === 'pending' ? `
                    <button class="btn task-btn completed" onclick="handleTaskUpdate(${task.id}, 'completed', this)">
                        <span data-i18n="completed">${t('completed')}</span>
                        <span class="btn-icon">✔</span>
                    </button>
                    <button class="btn task-btn failed" onclick="handleTaskUpdate(${task.id}, 'failed', this)">
                        <span data-i18n="failed">${t('failed')}</span>
                        <span class="btn-icon">✖</span>
                    </button>
                ` : `
                    <div class="status-badge ${task.status}">
                        ${task.status === 'completed' ? `<span>${t('completed')} ✔</span>` : `<span>${t('failed')} ✖</span>`}
                    </div>
                `}
            </div>
        `;
        list.appendChild(card);
    });
}

async function addTask(title, category, difficulty, date, time) {
    const priority = document.getElementById('task-priority').value;
    const recurring = document.getElementById('task-recurring').value;
    const dueDate = document.getElementById('task-due-date').value;
    const linkGoal = document.getElementById('task-link-goal-checkbox').checked;
    const goalIdRaw = document.getElementById('task-goal-select').value;
    const goalId = linkGoal && goalIdRaw ? Number(goalIdRaw) : null;

    const submitBtn = document.querySelector('#add-task-form button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>⏳</span> Processing...';
    
    try {
        const taskDate = date || new Date().toISOString().split('T')[0];
        await apiFetch('/tasks', {
            method: 'POST',
            body: JSON.stringify({ 
                user_id: currentUser.user_id,
                title, category, difficulty,
                priority, recurring,
                due_date: dueDate || null,
                date: taskDate,
                time: time || null,
                goal_id: goalId
            })
        });
        smartPersonalizationCache = { timestamp: 0, data: null };
        toggleTaskForm();
        loadTasks();
        if (goalId) loadGoals();
        showToast(t('task_added'), 'success');
    } catch (err) {
        // Error toast handled by apiFetch
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

async function handleTaskUpdate(taskId, status, btnEl) {
    // OPTIMISTIC UI: Instant feedback
    const card = btnEl.closest('.task-card');
    const originalStatus = card.className;
    const originalActions = card.querySelector('.task-actions').innerHTML;
    
    // Update local state and UI immediately
    card.className = `task-card ${status}`;
    card.querySelector('.task-actions').innerHTML = `<span>⏳</span>`;
    
    // Update cache
    const taskIdx = cachedTasks.findIndex(t => t.id === taskId);
    if (taskIdx !== -1) cachedTasks[taskIdx].status = status;

    try {
        await apiFetch(`/tasks/${taskId}`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
        
        // Success: Replace loader with status icon
        card.querySelector('.task-actions').innerHTML = `
            <div class="status-badge ${status}">
                <span>${status === 'completed' ? t('completed') + ' ✔' : t('failed') + ' ✖'}</span>
            </div>
        `;
        showToast(t('task_updated'), 'success');
        
        // Motivation feedback
        if (status === 'completed') {
            const messages = [t('well_done'), t('keep_going')];
            const randomMsg = messages[Math.floor(Math.random() * messages.length)];
            showToast(randomMsg, 'success');
        }

        // If in dashboard, refresh stats silently
        smartPersonalizationCache = { timestamp: 0, data: null };
        if (currentView === 'reports') loadReports();
        if (currentView === 'me') loadMe();
        loadGoals();
    } catch (err) {
        // Rollback on error
        card.className = originalStatus;
        card.querySelector('.task-actions').innerHTML = originalActions;
        if (taskIdx !== -1) cachedTasks[taskIdx].status = 'pending';
        showToast(err.message, 'error');
    }
}

function toggleTaskGoalLink(isEnabled) {
    const select = document.getElementById('task-goal-select');
    if (!select) return;
    select.disabled = !isEnabled;
    if (!isEnabled) {
        select.value = '';
    } else if (cachedGoals.length === 0) {
        loadGoals();
    }
}

async function loadGoals() {
    const list = document.getElementById('goals-list');
    try {
        const goals = await apiFetch('/goals');
        cachedGoals = goals;
        populateGoalOptions();
        if (list) {
            renderGoals(goals);
        }
    } catch (err) {
        if (list) {
            list.innerHTML = `<div class="empty-state"><p class="error-msg">${err.message}</p></div>`;
        }
    }
}

function populateGoalOptions() {
    const select = document.getElementById('task-goal-select');
    if (!select) return;
    const activeGoals = cachedGoals.filter(g => g.status === 'active');
    select.innerHTML = `<option value="">Select goal</option>` + activeGoals.map(g => `<option value="${g.id}">${g.title}</option>`).join('');
}

function renderGoals(goals) {
    const list = document.getElementById('goals-list');
    if (!list) return;
    if (!goals || goals.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <span class="empty-state-icon">🎯</span>
                <h3 class="empty-state-title">No goals yet</h3>
                <p class="empty-state-text">Create your first goal to track long-term progress.</p>
                <button onclick="toggleGoalForm()" class="btn primary">Create Goal</button>
            </div>
        `;
        return;
    }
    list.innerHTML = goals.map(goal => `
        <div class="task-card goal-card ${goal.status}">
            <div class="task-info">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    <h3>${goal.title}</h3>
                    <span class="priority-badge priority-low">${goal.category}</span>
                </div>
                <div class="task-meta">
                    <p>Deadline: ${goal.deadline}</p>
                    <p>Tasks: ${goal.completed_tasks_count}/${goal.linked_tasks_count}</p>
                </div>
                <div class="progress-bar" style="margin-top:0.75rem;">
                    <div id="goal-progress-${goal.id}" style="height:100%; width:${goal.progress_percent}%; background:linear-gradient(90deg,#0066FF,#10B981);"></div>
                </div>
                <div class="goal-progress-meta">
                    <span>${goal.progress_percent.toFixed(0)}%</span>
                    <span>${goal.status}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function toggleGoalForm() {
    const container = document.getElementById('goal-form-container');
    container.classList.toggle('active');
    if (container.classList.contains('active')) {
        document.getElementById('goal-title').value = '';
        document.getElementById('goal-category').value = 'General';
        document.getElementById('goal-type').value = 'two_weeks';
        handleGoalTypeChange();
    }
}

function handleGoalTypeChange() {
    const goalType = document.getElementById('goal-type').value;
    const deadlinePresetEl = document.getElementById('goal-deadline-preset');
    
    const goalTypeConfig = {
        today: {
            presets: ['today', 'custom'],
            default: 'today'
        },
        tomorrow: {
            presets: ['tomorrow', 'custom'],
            default: 'tomorrow'
        },
        three_days: {
            presets: ['tomorrow', 'three_days', 'custom'],
            default: 'three_days'
        },
        one_week: {
            presets: ['three_days', 'one_week', 'custom'],
            default: 'one_week'
        },
        two_weeks: {
            presets: ['one_week', 'two_weeks', 'custom'],
            default: 'two_weeks'
        },
        one_month: {
            presets: ['two_weeks', 'one_month', 'custom'],
            default: 'one_month'
        },
        three_months: {
            presets: ['one_month', 'three_months', 'custom'],
            default: 'three_months'
        },
        six_months: {
            presets: ['three_months', 'six_months', 'custom'],
            default: 'six_months'
        },
        one_year: {
            presets: ['six_months', 'one_year', 'custom'],
            default: 'one_year'
        },
        one_year_plus: {
            presets: ['one_year', 'one_year_plus', 'custom'],
            default: 'one_year_plus'
        }
    };
    
    const config = goalTypeConfig[goalType] || goalTypeConfig['two_weeks'];
    
    const presetLabels = {
        today: 'Today',
        tomorrow: 'Tomorrow',
        three_days: '3 days',
        one_week: '1 week',
        two_weeks: '2 weeks',
        one_month: '1 month',
        three_months: '3 months',
        six_months: '6 months',
        one_year: '1 year',
        one_year_plus: '1 year+',
        custom: 'Custom Date'
    };
    
    deadlinePresetEl.innerHTML = config.presets.map(preset => 
        `<option value="${preset}">${presetLabels[preset]}</option>`
    ).join('');
    
    deadlinePresetEl.value = config.default;
    handleGoalDeadlinePreset();
    restrictCustomDeadline();
}

function validateGoalDeadline() {
    const goalType = document.getElementById('goal-type').value;
    const preset = document.getElementById('goal-deadline-preset').value;
    const customInput = document.getElementById('goal-custom-deadline');
    
    let deadline;
    if (preset === 'custom') {
        if (!customInput.value) {
            return { valid: false, message: 'Please select a custom deadline' };
        }
        deadline = new Date(customInput.value);
    } else {
        deadline = new Date(resolveGoalDeadline());
    }
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    deadline.setHours(0, 0, 0, 0);
    
    const goalTypeRanges = {
        today: { min: 0, max: 0 },
        tomorrow: { min: 1, max: 1 },
        three_days: { min: 1, max: 3 },
        one_week: { min: 1, max: 7 },
        two_weeks: { min: 7, max: 14 },
        one_month: { min: 14, max: 30 },
        three_months: { min: 30, max: 90 },
        six_months: { min: 90, max: 180 },
        one_year: { min: 180, max: 365 },
        one_year_plus: { min: 365, max: 3650 },
    };
    
    const range = goalTypeRanges[goalType] || goalTypeRanges['two_weeks'];
    
    if (deadline < today) {
        return { valid: false, message: 'Deadline cannot be in the past' };
    }
    
    const daysUntilDeadline = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
    
    if (daysUntilDeadline < range.min || daysUntilDeadline > range.max) {
        const typeLabels = {
            today: 'Today',
            tomorrow: 'Tomorrow',
            three_days: '1-3 days',
            one_week: '1 week',
            two_weeks: '1-2 weeks',
            one_month: '1 month',
            three_months: '3 months',
            six_months: '6 months',
            one_year: '1 year',
            one_year_plus: '1 year+',
        };
        return { 
            valid: false, 
            message: `This deadline is outside the range for ${typeLabels[goalType]} goals` 
        };
    }
    
    return { valid: true };
}

function restrictCustomDeadline() {
    const goalType = document.getElementById('goal-type').value;
    const customInput = document.getElementById('goal-custom-deadline');
    if (!customInput.disabled) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const goalTypeRanges = {
            today: { min: 0, max: 0 },
            tomorrow: { min: 1, max: 1 },
            three_days: { min: 1, max: 3 },
            one_week: { min: 1, max: 7 },
            two_weeks: { min: 7, max: 14 },
            one_month: { min: 14, max: 30 },
            three_months: { min: 30, max: 90 },
            six_months: { min: 90, max: 180 },
            one_year: { min: 180, max: 365 },
            one_year_plus: { min: 365, max: 3650 },
        };
        
        const range = goalTypeRanges[goalType] || goalTypeRanges['two_weeks'];
        
        const minDate = new Date(today);
        minDate.setDate(today.getDate() + range.min);
        
        const maxDate = new Date(today);
        maxDate.setDate(today.getDate() + range.max);
        
        customInput.min = minDate.toISOString().split('T')[0];
        customInput.max = maxDate.toISOString().split('T')[0];
    }
}

function handleGoalDeadlinePreset() {
    const preset = document.getElementById('goal-deadline-preset').value;
    const customInput = document.getElementById('goal-custom-deadline');
    customInput.disabled = preset !== 'custom';
    if (preset !== 'custom') {
        customInput.value = '';
    } else {
        restrictCustomDeadline();
    }
}

function resolveGoalDeadline() {
    const preset = document.getElementById('goal-deadline-preset').value;
    const custom = document.getElementById('goal-custom-deadline').value;
    const base = new Date();
    if (preset === 'custom') {
        return custom;
    }
    if (preset === 'today') {
    } else if (preset === 'tomorrow') {
        base.setDate(base.getDate() + 1);
    } else if (preset === 'three_days') {
        base.setDate(base.getDate() + 3);
    } else if (preset === 'one_week') {
        base.setDate(base.getDate() + 7);
    } else if (preset === 'two_weeks') {
        base.setDate(base.getDate() + 14);
    } else if (preset === 'one_month') {
        base.setMonth(base.getMonth() + 1);
    } else if (preset === 'three_months') {
        base.setMonth(base.getMonth() + 3);
    } else if (preset === 'six_months') {
        base.setMonth(base.getMonth() + 6);
    } else if (preset === 'one_year') {
        base.setFullYear(base.getFullYear() + 1);
    } else if (preset === 'one_year_plus') {
        base.setFullYear(base.getFullYear() + 2);
    }
    return base.toISOString().split('T')[0];
}

function switchTasksGoalsTab(tab) {
    currentTasksGoalsTab = tab;
    document.getElementById('tab-tasks-only').classList.toggle('active', tab === 'tasks');
    document.getElementById('tab-goals-only').classList.toggle('active', tab === 'goals');
    document.getElementById('tab-habits-only').classList.toggle('active', tab === 'habits');
    document.getElementById('tasks-only-container').style.display = tab === 'tasks' ? 'block' : 'none';
    document.getElementById('goals-only-container').style.display = tab === 'goals' ? 'block' : 'none';
    document.getElementById('habits-only-container').style.display = tab === 'habits' ? 'block' : 'none';
    document.getElementById('smart-suggestion-container').style.display = tab === 'tasks' ? 'block' : 'none';
    
    const titleEl = document.getElementById('tasks-goals-title');
    const addBtn = document.getElementById('tasks-goals-add-btn');
    if (tab === 'tasks') {
        titleEl.textContent = t('tasks');
        addBtn.textContent = '+ Add Task';
        loadTasks();
    } else if (tab === 'goals') {
        titleEl.textContent = 'Goals';
        addBtn.textContent = '+ New Goal';
        loadGoals();
    } else {
        titleEl.textContent = 'Habits';
        addBtn.textContent = '+ New Habit';
        loadHabits();
    }
}

function toggleCurrentForm() {
    if (currentTasksGoalsTab === 'tasks') {
        toggleTaskForm();
    } else if (currentTasksGoalsTab === 'goals') {
        toggleGoalForm();
    } else {
        toggleHabitForm();
    }
}

function calculatePressureStatus(goal) {
    const deadline = new Date(goal.deadline);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    deadline.setHours(0, 0, 0, 0);

    const daysRemaining = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
    const progress = goal.progress_percent || 0;

    if (daysRemaining < 0) {
        return { status: 'overdue', color: '#EF4444', daysRemaining };
    } else if (daysRemaining <= 2 && progress < 60) {
        return { status: 'at_risk', color: '#F59E0B', daysRemaining };
    } else {
        return { status: 'on_track', color: '#0066FF', daysRemaining };
    }
}

function getGoalTypeLabel(type) {
    const labels = {
        today: 'Today (Short)',
        tomorrow: 'Tomorrow (Short)',
        three_days: '1-3 days (Short)',
        one_week: '1 week (Medium)',
        two_weeks: '1-2 weeks (Medium)',
        one_month: '1 month (Medium)',
        three_months: '3 months (Long)',
        six_months: '6 months (Long)',
        one_year: '1 year (Long)',
        one_year_plus: '1 year+ (Long)'
    };
    return labels[type] || type;
}

async function addGoal(title, category) {
    const validation = validateGoalDeadline();
    if (!validation.valid) {
        showToast(validation.message, 'error');
        return;
    }
    
    const deadline = resolveGoalDeadline();
    const goalType = document.getElementById('goal-type').value;
    
    await apiFetch('/goals', {
        method: 'POST',
        body: JSON.stringify({ title, category, deadline, goal_type: goalType })
    });
    smartPersonalizationCache = { timestamp: 0, data: null };
    toggleGoalForm();
    await loadGoals();
    showToast('Goal created', 'success');
}

async function handleGoalComplete(goalId) {
    try {
        currentGoalForReflection = goalId;
        await apiFetch(`/goals/${goalId}`, {
            method: 'PATCH',
            body: JSON.stringify({ status: 'achieved' })
        });
        smartPersonalizationCache = { timestamp: 0, data: null };
        document.getElementById('goal-reflection-modal').classList.add('active');
        loadGoals();
        if (currentView === 'reports') loadReports();
        if (currentView === 'me') loadMe();
    } catch (err) {
        console.error('Failed to complete goal:', err);
    }
}

async function handleGoalFail(goalId) {
    try {
        await apiFetch(`/goals/${goalId}`, {
            method: 'PATCH',
            body: JSON.stringify({ status: 'failed' })
        });
        smartPersonalizationCache = { timestamp: 0, data: null };
        loadGoals();
        if (currentView === 'reports') loadReports();
        if (currentView === 'me') loadMe();
        showToast('Goal marked as failed', 'error');
    } catch (err) {
        console.error('Failed to update goal:', err);
    }
}

async function saveGoalReflection() {
    const wentWell = document.getElementById('reflection-went-well').value;
    const didntGoWell = document.getElementById('reflection-didnt-go-well').value;
    try {
        await apiFetch(`/goals/${currentGoalForReflection}`, {
            method: 'PATCH',
            body: JSON.stringify({
                reflection_went_well: wentWell,
                reflection_didnt_go_well: didntGoWell
            })
        });
        closeReflectionModal();
        showToast('Reflection saved!', 'success');
    } catch (err) {
        console.error('Failed to save reflection:', err);
    }
}

function closeReflectionModal() {
    document.getElementById('goal-reflection-modal').classList.remove('active');
    document.getElementById('reflection-went-well').value = '';
    document.getElementById('reflection-didnt-go-well').value = '';
    currentGoalForReflection = null;
}

function renderGoals(goals) {
    const list = document.getElementById('goals-list');
    if (!list) return;
    if (!goals || goals.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <span class="empty-state-icon">🎯</span>
                <h3 class="empty-state-title">No goals yet</h3>
                <p class="empty-state-text">Create your first goal to track long-term progress.</p>
                <button onclick="toggleGoalForm()" class="btn primary">Create Goal</button>
            </div>
        `;
        return;
    }
    list.innerHTML = goals.map(goal => {
        const pressure = calculatePressureStatus(goal);
        const typeLabel = getGoalTypeLabel(goal.goal_type);
        return `
        <div class="task-card goal-card ${goal.status}" style="border-left: 4px solid ${pressure.color};">
            <div class="task-info">
                <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap: wrap;">
                    <h3 style="margin: 0;">${goal.title}</h3>
                    <span class="priority-badge priority-low">${goal.category}</span>
                    <span class="priority-badge priority-medium">${typeLabel}</span>
                    <span class="priority-badge" style="background: ${pressure.color}20; color: ${pressure.color}; border-color: ${pressure.color};">
                        ${pressure.status === 'on_track' ? 'On Track' : pressure.status === 'at_risk' ? 'At Risk' : 'Overdue'}
                    </span>
                </div>
                <div class="task-meta">
                    <p>Deadline: ${goal.deadline} (${pressure.daysRemaining} days left)</p>
                    <p>Tasks: ${goal.completed_tasks_count}/${goal.linked_tasks_count}</p>
                </div>
                <div class="progress-bar" style="margin-top:0.75rem;">
                    <div style="height:100%; width:${goal.progress_percent}%; background:linear-gradient(90deg,#0066FF,#10B981);"></div>
                </div>
                <div class="goal-progress-meta">
                    <span>${goal.progress_percent.toFixed(0)}%</span>
                    <span>${goal.status}</span>
                </div>
                ${goal.reflection_went_well || goal.reflection_didnt_go_well ? `
                <div style="margin-top:0.75rem; padding:0.75rem; background:rgba(255,255,255,0.05); border-radius:8px;">
                    ${goal.reflection_went_well ? `<p><strong>What went well:</strong> ${goal.reflection_went_well}</p>` : ''}
                    ${goal.reflection_didnt_go_well ? `<p><strong>What didn't:</strong> ${goal.reflection_didnt_go_well}</p>` : ''}
                </div>
                ` : ''}
            </div>
            <div class="task-actions">
                ${goal.status === 'active' ? `
                    <button class="btn task-btn completed" onclick="handleGoalComplete(${goal.id})">
                        <span>Achieved</span>
                        <span class="btn-icon">✔</span>
                    </button>
                    <button class="btn task-btn failed" onclick="handleGoalFail(${goal.id})">
                        <span>Failed</span>
                        <span class="btn-icon">✖</span>
                    </button>
                ` : `
                    <div class="status-badge ${goal.status}">
                        <span>${goal.status === 'achieved' ? 'Achieved ✔' : 'Failed ✖'}</span>
                    </div>
                `}
            </div>
        </div>
    `}).join('');
}

async function loadIdentityProfile() {
    try {
        const identity = await apiFetch('/identity/profile');
        if (identityInitialized) {
            if (identity.level > identitySnapshot.level) {
                showToast(`Level Up! You reached Level ${identity.level}`, 'success');
            }
            const currentUnlocked = identity.badges.filter(b => b.unlocked).map(b => b.id);
            const previousUnlocked = new Set(identitySnapshot.unlockedBadgeIds);
            const newlyUnlocked = currentUnlocked.filter(id => !previousUnlocked.has(id));
            newlyUnlocked.forEach(() => showToast('New Badge Unlocked', 'info'));
        }
        renderIdentity(identity);
        identitySnapshot = {
            level: identity.level,
            unlockedBadgeIds: identity.badges.filter(b => b.unlocked).map(b => b.id),
        };
        identityInitialized = true;
        const achievementList = document.getElementById('achievements-list');
        if (achievementList) {
            achievementList.innerHTML = identity.badges.map(b => `
                <div class="achievement-badge ${b.unlocked ? 'unlocked' : ''}">
                    <span class="icon">${b.unlocked ? '🏅' : '🔒'}</span>
                    <span class="name">${b.label}</span>
                </div>
            `).join('');
        }
    } catch (err) {
        console.error('Identity load failed', err);
    }
}

function renderIdentity(identity) {
    const levelEl = document.getElementById('identity-level-badge');
    const statsEl = document.getElementById('identity-stats');
    const badgesEl = document.getElementById('identity-badges');
    const xpFillEl = document.getElementById('identity-xp-fill');
    const xpTextEl = document.getElementById('identity-xp-text');
    const trustEl = document.getElementById('identity-trust-value');
    if (!levelEl || !statsEl || !badgesEl || !xpFillEl || !xpTextEl || !trustEl) return;

    levelEl.textContent = `Level ${identity.level}`;
    xpFillEl.style.width = `${identity.level_progress_percent || 0}%`;
    xpTextEl.textContent = `XP ${identity.xp_into_current_level}/${identity.xp_for_next_level} Total ${identity.total_xp}`;
    trustEl.textContent = `${(identity.trust_score || 0).toFixed(1)}`;
    statsEl.innerHTML = `
        <div class="identity-stat-item"><span class="label">Completed Tasks</span><span class="value">${identity.completed_tasks}</span></div>
        <div class="identity-stat-item"><span class="label">Completed Goals</span><span class="value">${identity.completed_goals}</span></div>
        <div class="identity-stat-item"><span class="label">Streak</span><span class="value">${identity.streak}</span></div>
    `;
    badgesEl.innerHTML = identity.badges.map(b => `<span class="identity-badge ${b.unlocked ? 'unlocked' : ''}">${b.label}</span>`).join('');
}

// --- Helpers & Listeners ---
function setupEventListeners() {
    // Auth Tab Switch
    const tabLogin = document.getElementById('tab-login');
    const tabSignup = document.getElementById('tab-signup');
    if (tabLogin) tabLogin.onclick = () => switchAuthTab('login');
    if (tabSignup) tabSignup.onclick = () => switchAuthTab('signup');

    // Auth
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            login(document.getElementById('login-email').value, document.getElementById('login-password').value);
        });
    }

    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            signup(
                document.getElementById('signup-name').value,
                document.getElementById('signup-username').value,
                document.getElementById('signup-email').value,
                document.getElementById('signup-password').value
            );
        });
    }

    const googleBtn = document.getElementById('google-signin-btn');
    if (googleBtn) {
        googleBtn.addEventListener('click', async () => {
            await signInWithGoogle();
        });
    }

    document.querySelectorAll('.password-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            if (!targetId) return;
            const input = document.getElementById(targetId);
            if (!input) return;
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            const icon = btn.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-eye', !isPassword);
                icon.classList.toggle('fa-eye-slash', isPassword);
            }
        });
    });

    const forgotLink = document.getElementById('forgot-password-link');
    if (forgotLink) forgotLink.addEventListener('click', () => setAuthView('forgot'));

    const forgotBack = document.getElementById('forgot-back-link');
    if (forgotBack) forgotBack.addEventListener('click', () => setAuthView('login'));

    const verifyBack = document.getElementById('verify-back-link');
    if (verifyBack) verifyBack.addEventListener('click', () => setAuthView('login'));

    const resendBtn = document.getElementById('resend-verification-btn');
    if (resendBtn) resendBtn.addEventListener('click', async () => await resendVerificationEmail());

    const verifyOtpBtn = document.getElementById('verify-otp-btn');
    if (verifyOtpBtn) verifyOtpBtn.addEventListener('click', async () => await verifyEmailCode());

    const forgotForm = document.getElementById('forgot-form');
    if (forgotForm) {
        forgotForm.addEventListener('submit', (e) => {
            e.preventDefault();
            sendPasswordReset(document.getElementById('forgot-email').value);
        });
    }

    const recoveryOtpBtn = document.getElementById('recovery-otp-btn');
    if (recoveryOtpBtn) recoveryOtpBtn.addEventListener('click', async () => await verifyRecoveryCode());

    const resetForm = document.getElementById('reset-form');
    if (resetForm) {
        resetForm.addEventListener('submit', (e) => {
            e.preventDefault();
            updatePassword(
                document.getElementById('reset-password').value,
                document.getElementById('reset-password-confirm').value
            );
        });
    }

    // Task Form
    const addTaskForm = document.getElementById('add-task-form');
    if (addTaskForm) {
        addTaskForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const title = document.getElementById('task-title').value;
            const category = document.getElementById('task-category').value;
            const difficulty = document.getElementById('task-difficulty').value;
            const date = document.getElementById('task-date') ? document.getElementById('task-date').value : null;
            const time = document.getElementById('task-time') ? document.getElementById('task-time').value : null;
            addTask(title, category, difficulty, date, time);
        });
    }

    const addGoalForm = document.getElementById('add-goal-form');
    if (addGoalForm) {
        addGoalForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const title = document.getElementById('goal-title').value.trim();
            const category = document.getElementById('goal-category').value.trim();
            addGoal(title, category || 'general');
        });
    }

    const addHabitForm = document.getElementById('add-habit-form');
    if (addHabitForm) {
        addHabitForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await addHabit();
        });
    }

    const reflectionForm = document.getElementById('goal-reflection-form');
    if (reflectionForm) {
        reflectionForm.addEventListener('submit', (e) => {
            e.preventDefault();
            saveGoalReflection();
        });
    }

    const goalTypeSelect = document.getElementById('goal-type');
    if (goalTypeSelect) {
        goalTypeSelect.addEventListener('change', handleGoalTypeChange);
    }

    const customDeadlineInput = document.getElementById('goal-custom-deadline');
    if (customDeadlineInput) {
        customDeadlineInput.addEventListener('change', restrictCustomDeadline);
    }

    // Profile Form
    const profileForm = document.getElementById('profile-edit-form');
    if (profileForm) {
        profileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                showLoading(true);
                const name = document.getElementById('profile-name-input')?.value || '';
                const username = document.getElementById('profile-username-input')?.value || '';
                await updateProfile(name, username);
                showToast('Profile updated', 'success');
            } catch (err) {
                showToast(err.message || 'Failed to update profile', 'error');
            } finally {
                showLoading(false);
            }
        });
    }

    const cancelBtn = document.getElementById('profile-cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            cancelProfileChanges();
            showToast('Changes discarded', 'info');
        });
    }

    const nameInput = document.getElementById('profile-name-input');
    if (nameInput) {
        nameInput.addEventListener('input', () => {
            profileDraft.name = nameInput.value;
            updateProfileSaveState();
        });
    }

    const usernameInput = document.getElementById('profile-username-input');
    if (usernameInput) {
        usernameInput.addEventListener('input', () => {
            profileDraft.username = usernameInput.value;
            updateProfileSaveState();
        });
    }

    const avatarBtn = document.getElementById('profile-avatar-edit');
    const avatarInput = document.getElementById('profile-avatar-input');
    if (avatarBtn && avatarInput) {
        avatarBtn.addEventListener('click', () => {
            console.log("Avatar edit button clicked");
            avatarInput.click();
        });
        avatarInput.addEventListener('change', (event) => {
            console.log("Avatar input changed");
            const file = event.target.files && event.target.files[0];
            if (!file) {
                console.log("No file selected");
                return;
            }
            
            console.log("File selected:", file.name);
            currentCropFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                console.log("File read complete, opening crop modal");
                const cropImg = document.getElementById('crop-image');
                cropImg.src = e.target.result;
                document.getElementById('crop-modal').classList.add('active');
                
                if (cropper) cropper.destroy();
                cropper = new Cropper(cropImg, {
                    aspectRatio: 1,
                    viewMode: 1,
                    dragMode: 'move',
                    autoCropArea: 1,
                    restore: false,
                    guides: false,
                    center: true,
                    highlight: false,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false,
                });
            };
            reader.readAsDataURL(file);
        });
    }

    const cropCancelBtn = document.getElementById('crop-cancel-btn');
    if (cropCancelBtn) {
        cropCancelBtn.addEventListener('click', () => {
            document.getElementById('crop-modal').classList.remove('active');
            if (cropper) cropper.destroy();
            cropper = null;
        });
    }

    const cropSaveBtn = document.getElementById('crop-save-btn');
    if (cropSaveBtn) {
        cropSaveBtn.addEventListener('click', () => {
            if (!cropper) return;
            
            const canvas = cropper.getCroppedCanvas({
                width: 256,
                height: 256,
            });
            
            const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
            profileDraft.avatar_url = dataUrl;
            const avatarEl = document.getElementById('profile-avatar');
            if (avatarEl) avatarEl.src = dataUrl;
            
            updateProfileSaveState();
            showToast('Photo adjusted (pending save)', 'info');
            
            document.getElementById('crop-modal').classList.remove('active');
            cropper.destroy();
            cropper = null;
        });
    }

    // Set default date/time in form
    const taskDateInput = document.getElementById('task-date');
    const taskTimeInput = document.getElementById('task-time');
    if (taskDateInput) taskDateInput.value = new Date().toISOString().split('T')[0];
    if (taskTimeInput) {
        const now = new Date();
        taskTimeInput.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    }

    // Reminders check every minute
    setInterval(() => {
        if (typeof checkReminders === 'function') checkReminders();
    }, 60000);
}

function switchAuthTab(tab) {
    setAuthView(tab);
}

function showAuthError(msg) {
    const el = document.getElementById('auth-error');
    if (el) el.textContent = msg;
}

function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    localStorage.setItem('tm_dark_mode', isDarkMode ? '1' : '0');
    applyTheme();
    if (currentUser) {
        if (currentView === 'reports') loadReports();
        if (currentView === 'me') loadMe();
        if (currentView === 'tasks') renderTasks(cachedTasks);
    }
    showToast(t('task_updated'), 'success');
}

function toggleTaskForm() {
    const container = document.getElementById('task-form-container');
    container.classList.toggle('active');
    document.getElementById('task-title').value = '';
    if (container.classList.contains('active')) {
        populateGoalOptions();
        const checkbox = document.getElementById('task-link-goal-checkbox');
        checkbox.checked = false;
        toggleTaskGoalLink(false);
    }
}

// === Swipe Navigation (Mobile Only) ===
(function() {
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;
    let startedOnBottomNav = false;
    
    const viewOrder = ['tasks', 'reports', 'insights', 'me'];
    
    document.addEventListener('touchstart', e => {
        startedOnBottomNav = Boolean(e.target && e.target.closest && e.target.closest('.bottom-nav'));
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });
    
    document.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    }, { passive: true });
    
    function handleSwipe() {
        const isMobile = window.innerWidth <= 768;
        if (!isMobile) return;
        if (startedOnBottomNav) return;
        
        const diffX = touchEndX - touchStartX;
        const diffY = touchEndY - touchStartY;
        
        // Only handle swipes that are mostly horizontal
        if (Math.abs(diffX) > Math.abs(diffY) * 2 && Math.abs(diffX) > 50) {
            const currentIndex = viewOrder.indexOf(currentView);
            let targetIndex;
            
            if (diffX < 0) {
                // Swipe left - next view
                targetIndex = (currentIndex + 1) % viewOrder.length;
            } else {
                // Swipe right - previous view
                targetIndex = (currentIndex - 1 + viewOrder.length) % viewOrder.length;
            }
            
            showView(viewOrder[targetIndex]);
        }
    }
})();

async function forceUpdateApp() {
    if (confirm("This will clear all cache and reload the app. Continue?")) {
        showLoading(true);
        try {
            // 1. Unregister all service workers
            if ('serviceWorker' in navigator) {
                const registrations = await navigator.serviceWorker.getRegistrations();
                for (let registration of registrations) {
                    await registration.unregister();
                }
            }
            // 2. Clear all caches
            if ('caches' in window) {
                const cacheNames = await caches.keys();
                for (let name of cacheNames) {
                    await caches.delete(name);
                }
            }
            // 3. Hard reload
            window.location.reload(true);
        } catch (err) {
            console.error("Force update failed", err);
            window.location.reload(true);
        }
    }
}

function showLoading(show) {
    // We only show full loading overlay for major operations like initial load or auth
    // For smaller tasks, we use skeleton or inline loaders
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.toggle('active', show);
}

// --- PWA Service Worker Registration ---
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => {
                console.log('SW registered');
                
                // Check for updates
                reg.onupdatefound = () => {
                    const installingWorker = reg.installing;
                    installingWorker.onstatechange = () => {
                        if (installingWorker.state === 'installed') {
                            if (navigator.serviceWorker.controller) {
                                // New content is available, show toast
                                showToast("New version available! Refreshing...", "info");
                                setTimeout(() => {
                                    window.location.reload();
                                }, 2000);
                            }
                        }
                    };
                };
            })
            .catch(err => console.log('SW failed', err));
    });
}

// PWA Install Prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const installBtn = document.getElementById('install-btn');
    const topInstallBtn = document.getElementById('top-install-btn');
    if (installBtn) installBtn.style.display = 'block';
    if (topInstallBtn) topInstallBtn.style.display = 'grid'; // matches .icon-btn display
});

async function handleInstallClick() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
            deferredPrompt = null;
            const installBtn = document.getElementById('install-btn');
            const topInstallBtn = document.getElementById('top-install-btn');
            if (installBtn) installBtn.style.display = 'none';
            if (topInstallBtn) topInstallBtn.style.display = 'none';
        }
    }
}

const installBtn = document.getElementById('install-btn');
if (installBtn) installBtn.addEventListener('click', handleInstallClick);

const topInstallBtn = document.getElementById('top-install-btn');
if (topInstallBtn) topInstallBtn.addEventListener('click', handleInstallClick);


// --- Share Functions ---
let shareData = {
    level: 1,
    xp: 0,
    streak: 0,
    completedTasks: 0,
    goalsAchieved: 0
};

async function openShareModal() {
    const modal = document.getElementById('share-modal');
    modal.classList.add('active');
    
    try {
        const [identity, socialProfile, allTasks] = await Promise.all([
            apiFetch('/identity/profile'),
            apiFetch('/social/profile'),
            apiFetch('/tasks/range?start_date=2000-01-01&end_date=2100-12-31')
        ]);
        
        shareData = {
            level: identity.level,
            xp: identity.total_xp,
            streak: identity.streak,
            completedTasks: identity.completed_tasks,
            goalsAchieved: socialProfile.goals_achieved || 0
        };
        
        document.getElementById('share-username').textContent = currentUser.name || currentUser.username;
        document.getElementById('share-level').textContent = shareData.level;
        document.getElementById('share-xp').textContent = shareData.xp;
        document.getElementById('share-streak').textContent = shareData.streak;
        document.getElementById('share-completed-tasks').textContent = shareData.completedTasks;
        document.getElementById('share-goals-achieved').textContent = shareData.goalsAchieved;
        document.getElementById('profile-link').value = `${window.location.origin}/user/${currentUser.username}`;
        
    } catch (err) {
        console.error('Failed to load share data:', err);
        showToast('Failed to load share data', 'error');
    }
}

function closeShareModal() {
    const modal = document.getElementById('share-modal');
    modal.classList.remove('active');
}

async function downloadShareCard() {
    try {
        const shareCard = document.getElementById('share-card');
        
        const html2canvasScript = document.createElement('script');
        html2canvasScript.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
        html2canvasScript.onload = async () => {
            const canvas = await html2canvas(shareCard, {
                backgroundColor: '#0a0f25',
                scale: 2
            });
            
            const link = document.createElement('a');
            link.download = 'tobedone-progress.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
            
            showToast('Image downloaded!', 'success');
        };
        document.head.appendChild(html2canvasScript);
        
    } catch (err) {
        console.error('Download failed:', err);
        showToast('Download failed', 'error');
    }
}

function copyShareText() {
    const text = `Check out my progress on Tobedone! 🎯
Level: ${shareData.level}
XP: ${shareData.xp}
Streak: ${shareData.streak} days
Completed Tasks: ${shareData.completedTasks}
Goals Achieved: ${shareData.goalsAchieved}`;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Text copied!', 'success');
    }).catch(() => {
        showToast('Failed to copy text', 'error');
    });
}

async function nativeShare() {
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'My Tobedone Progress',
                text: `Check out my progress on Tobedone! Level ${shareData.level}, ${shareData.streak} day streak!`,
                url: document.getElementById('profile-link').value
            });
            showToast('Shared successfully!', 'success');
        } catch (err) {
            console.log('Share cancelled or failed');
        }
    } else {
        copyShareText();
    }
}

function copyProfileLink() {
    const linkInput = document.getElementById('profile-link');
    navigator.clipboard.writeText(linkInput.value).then(() => {
        showToast('Profile link copied!', 'success');
    }).catch(() => {
        showToast('Failed to copy link', 'error');
    });
}

// --- Dashboard Calendar Functions ---
async function renderDashboardCalendar() {
    const grid = document.getElementById('dashboard-calendar-grid');
    const title = document.getElementById('dashboard-calendar-month-year');
    if (!grid || !title) return;

    grid.innerHTML = '';
    const month = dashboardCalendarDate.getMonth();
    const year = dashboardCalendarDate.getFullYear();

    const monthNames = [t('january'), t('february'), t('march'), t('april'), t('may'), t('june'), t('july'), t('august'), t('september'), t('october'), t('november'), t('december')];
    title.textContent = `${monthNames[month]} ${year}`;

    // Days Labels
    const days = [t('mon'), t('tue'), t('wed'), t('thu'), t('fri'), t('sat'), t('sun')];
    days.forEach(d => grid.innerHTML += `<div class="calendar-day-label">${d}</div>`);

    // Get all tasks for the month to check active days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startStr = firstDay.toISOString().split('T')[0];
    const endStr = lastDay.toISOString().split('T')[0];

    let monthTasks = [];
    try {
        monthTasks = await apiFetch(`/tasks/range?start_date=${startStr}&end_date=${endStr}`);
    } catch (err) {
        console.error('Failed to load month tasks for calendar', err);
    }

    // Determine active days: days with at least one completed task
    const activeDays = new Set();
    monthTasks.forEach(task => {
        if (task.status === 'completed') {
            activeDays.add(task.date);
        }
    });

    const firstDayIdx = (firstDay.getDay() + 6) % 7; // Monday start
    const daysInMonth = lastDay.getDate();
    const todayStr = new Date().toISOString().split('T')[0];

    // Padding for previous month
    for (let i = 0; i < firstDayIdx; i++) {
        grid.innerHTML += `<div class="calendar-day other-month"></div>`;
    }

    // Days in current month
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const isToday = dateStr === todayStr;
        const isActive = activeDays.has(dateStr);
        const hasTasks = monthTasks.some(t => t.date === dateStr);

        const dayEl = document.createElement('div');
        dayEl.className = `calendar-day ${isToday ? 'today' : ''} ${isActive ? 'active-day' : ''}`;
        dayEl.textContent = d;
        dayEl.onclick = () => renderDayTasks(dateStr);
        grid.appendChild(dayEl);
    }
}

function changeDashboardMonth(delta) {
    dashboardCalendarDate.setMonth(dashboardCalendarDate.getMonth() + delta);
    renderDashboardCalendar();
}
