// =============================================
// LITTO-WATCH - Dashboard JavaScript
// =============================================

// ==================== CONFIGURATION ====================
const API_URL = 'https://litto-watch-api.onrender.com';

// ==================== AUTHENTIFICATION ====================
const token = localStorage.getItem('token');
const utilisateur = JSON.parse(localStorage.getItem('utilisateur') || '{}');

// Rediriger si pas connecté
if (!token) {
    window.location.href = 'connexion.html';
}

// Headers pour toutes les requêtes API
const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
};

// Afficher les infos utilisateur dans la sidebar
function afficherInfosUtilisateur() {
    const avatarEl = document.getElementById('user-avatar');
    const nomEl = document.getElementById('user-name');
    const emailEl = document.getElementById('user-email');

    if (avatarEl) avatarEl.textContent = (utilisateur.nom || '?')[0].toUpperCase();
    if (nomEl) nomEl.textContent = utilisateur.nom || 'Utilisateur';
    if (emailEl) emailEl.textContent = utilisateur.email || '';
}

// Déconnexion
function deconnexion() {
    localStorage.removeItem('token');
    localStorage.removeItem('utilisateur');
    window.location.href = 'connexion.html';
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ==================== NAVIGATION ====================
function initNavigation() {
    const navLinks = document.querySelectorAll('.sidebar-nav a, .nav-item');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const page = this.dataset.page;
            if (!page) return;
            
            // Activer le lien dans la sidebar
            document.querySelectorAll('.sidebar-nav a, .nav-item').forEach(l => {
                l.classList.remove('active');
            });
            this.classList.add('active');
            
            // Afficher la bonne page
            document.querySelectorAll('.page').forEach(p => {
                p.classList.remove('active');
            });
            
            const pageEl = document.getElementById('page-' + page) || document.getElementById(page);
            if (pageEl) {
                pageEl.classList.add('active');
            }
            
            // Charger les données selon la page
            switch(page) {
                case 'dashboard':
                    chargerDashboard();
                    break;
                case 'map':
                    if (!window.map) {
                        setTimeout(initMap, 200);
                    }
                    break;
                case 'observations':
                    chargerObservations();
                    break;
                case 'alerts':
                    chargerAlertes();
                    break;
                case 'field':
                    break;
                case 'import':
                    break;
            }
        });
    });
}

// ==================== DATE DU JOUR ====================
function afficherDate() {
    const dateEl = document.getElementById('current-date');
    if (!dateEl) return;
    
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString('fr-FR', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// ==================== DASHBOARD ====================
async function chargerDashboard() {
    try {
        // Charger les stats
        const statsRes = await fetch(API_URL + '/stats', { headers });
        const stats = await statsRes.json();
        
        // Charger les observations
        const obsRes = await fetch(API_URL + '/observations', { headers });
        const observations = await obsRes.json();
        
        // Charger les alertes
        const alertesRes = await fetch(API_URL + '/alertes', { headers });
        const alertes = await alertesRes.json();
        
        // Mettre à jour les KPI
        const nbObs = document.getElementById('stat-obs') || document.getElementById('nb-observations');
        const tempMoy = document.getElementById('stat-temp') || document.getElementById('temp-moyenne');
        const salMoy = document.getElementById('stat-sal') || document.getElementById('salinite-moyenne');
        const nbAlertes = document.getElementById('stat-alert') || document.getElementById('nb-alertes');
        
        if (nbObs) nbObs.textContent = stats.nombre_observations || 0;
        if (tempMoy) tempMoy.textContent = stats.temperature_moyenne ? stats.temperature_moyenne.toFixed(1) + ' °C' : '--';
        if (salMoy) salMoy.textContent = stats.salinite_moyenne ? stats.salinite_moyenne.toFixed(1) + ' ppt' : '--';
        if (nbAlertes) nbAlertes.textContent = Array.isArray(alertes) ? alertes.length : 0;
        
        // Mettre à jour le tableau des observations récentes
        const tbodyRecent = document.getElementById('recent-obs');
        if (tbodyRecent) {
            if (Array.isArray(observations) && observations.length > 0) {
                const recent = observations.slice(-10).reverse();
                tbodyRecent.innerHTML = recent.map(obs => `
                    <tr>
                        <td>${obs.date || '--'}</td>
                        <td>${obs.latitude || '--'}, ${obs.longitude || '--'}</td>
                        <td>${obs.type_mangrove || '--'}</td>
                        <td>${obs.niveau_degradation || '--'}</td>
                        <td>${obs.temperature_eau || '--'}</td>
                        <td>${obs.ph || '--'}</td>
                        <td>${obs.salinite || '--'}</td>
                    </tr>
                `).join('');
            } else {
                tbodyRecent.innerHTML = '<tr><td colspan="7" style="text-align:center;">Aucune observation</td></tr>';
            }
        }
        
    } catch (error) {
        console.error('Erreur chargement dashboard:', error);
        showToast('Erreur de connexion au serveur', 'error');
    }
}

// ==================== CARTE INTERACTIVE ====================
let map = null;
let markers = [];

function initMap() {
    const mapContainer = document.getElementById('map') || document.getElementById('map-container');
    if (!mapContainer || map) return;
    
    map = L.map(mapContainer).setView([14.5, -17.0], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap | LittoWatch',
        maxZoom: 19
    }).addTo(map);
    
    chargerMarqueurs();
}

async function chargerMarqueurs() {
    if (!map) return;
    
    try {
        const response = await fetch(API_URL + '/observations', { headers });
        const data = await response.json();
        
        // Supprimer les anciens marqueurs
        markers.forEach(m => map.removeLayer(m));
        markers = [];
        
        if (!Array.isArray(data)) return;
        
        data.forEach(obs => {
            if (!obs.latitude || !obs.longitude) return;
            
            let couleur = '#2d6a4f'; // vert par défaut
            
            if (obs.niveau_degradation === 'Critique') {
                couleur = '#e63946';
            } else if (obs.niveau_degradation === 'Élevé') {
                couleur = '#f4a261';
            } else if (obs.niveau_degradation === 'Moyen') {
                couleur = '#ffc107';
            }
            
            const marker = L.circleMarker([obs.latitude, obs.longitude], {
                radius: 8,
                fillColor: couleur,
                color: '#ffffff',
                weight: 2,
                fillOpacity: 0.8
            }).addTo(map);
            
            marker.bindPopup(`
                <div style="font-family:sans-serif;">
                    <b>${obs.type_mangrove || 'Mangrove'}</b><br>
                    <small>Date : ${obs.date || '--'}</small><br>
                    <small>Dégradation : ${obs.niveau_degradation || '--'}</small><br>
                    <small>Temp : ${obs.temperature_eau || '--'}°C</small><br>
                    <small>pH : ${obs.ph || '--'} | Salinité : ${obs.salinite || '--'} ppt</small>
                </div>
            `);
            
            markers.push(marker);
        });
        
    } catch (error) {
        console.error('Erreur chargement marqueurs:', error);
    }
}

// ==================== SAISIE TERRAIN ====================
function initFormulaireObservation() {
    const form = document.getElementById('obs-form') || document.getElementById('observation-form');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const data = {
            latitude: parseFloat(document.getElementById('latitude')?.value),
            longitude: parseFloat(document.getElementById('longitude')?.value),
            date: document.getElementById('date')?.value,
            type_mangrove: document.getElementById('type_mangrove')?.value || null,
            nature_sol: document.getElementById('nature_sol')?.value || null,
            niveau_degradation: document.getElementById('niveau_degradation')?.value || null,
            temperature_eau: parseFloat(document.getElementById('temperature_eau')?.value) || null,
            salinite: parseFloat(document.getElementById('salinite')?.value) || null,
            ph: parseFloat(document.getElementById('ph')?.value) || null,
            oxygene_dissous: parseFloat(document.getElementById('oxygene_dissous')?.value) || null,
            turbidite: parseFloat(document.getElementById('turbidite')?.value) || null,
            conductivite: parseFloat(document.getElementById('conductivite')?.value) || null,
            profondeur: parseFloat(document.getElementById('profondeur')?.value) || null,
            nitrates: parseFloat(document.getElementById('nitrates')?.value) || null,
            phosphates: parseFloat(document.getElementById('phosphates')?.value) || null,
            matiere_organique: parseFloat(document.getElementById('matiere_organique')?.value) || null,
            especes_presentes: document.getElementById('especes_presentes')?.value || null,
            notes: document.getElementById('notes')?.value || null
        };
        
        // Validation basique
        if (!data.latitude || !data.longitude || !data.date) {
            showToast('Veuillez remplir la localisation et la date', 'error');
            return;
        }
        
        try {
            const response = await fetch(API_URL + '/observations', {
                method: 'POST',
                headers,
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                showToast('Observation enregistrée avec succès !', 'success');
                form.reset();
                chargerDashboard();
                if (map) chargerMarqueurs();
            } else {
                const err = await response.json();
                showToast(err.detail || 'Erreur lors de l\'enregistrement', 'error');
            }
        } catch (error) {
            showToast('Erreur de connexion au serveur', 'error');
        }
    });
}

// ==================== OBSERVATIONS (TABLEAU COMPLET) ====================
async function chargerObservations() {
    const tbody = document.getElementById('all-obs');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">Chargement...</td></tr>';
    
    try {
        const response = await fetch(API_URL + '/observations', { headers });
        const data = await response.json();
        
        if (Array.isArray(data) && data.length > 0) {
            tbody.innerHTML = data.reverse().map(obs => `
                <tr>
                    <td>${obs.id || '--'}</td>
                    <td>${obs.date || '--'}</td>
                    <td>${obs.latitude || '--'}</td>
                    <td>${obs.longitude || '--'}</td>
                    <td>${obs.type_mangrove || '--'}</td>
                    <td>${obs.niveau_degradation || '--'}</td>
                    <td>${obs.temperature_eau || '--'}</td>
                    <td>${obs.ph || '--'}</td>
                    <td>${obs.salinite || '--'}</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">Aucune observation</td></tr>';
        }
    } catch (error) {
        console.error('Erreur chargement observations:', error);
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">Erreur de chargement</td></tr>';
    }
}

// ==================== ALERTES ====================
async function chargerAlertes() {
    const container = document.getElementById('alerts-container') || document.getElementById('alerts-list');
    if (!container) return;
    
    container.innerHTML = '<p style="color:#666;">Chargement...</p>';
    
    try {
        const response = await fetch(API_URL + '/alertes', { headers });
        const data = await response.json();
        
        if (Array.isArray(data) && data.length > 0) {
            container.innerHTML = data.map(a => {
                const isDanger = a.valeur > (a.seuil_max || 100);
                return `
                    <div class="alert-item ${isDanger ? 'danger' : 'warning'}">
                        <span class="alert-param">${a.parametre}</span> = <strong>${a.valeur}</strong>
                        (seuil: ${a.seuil_min || '--'} - ${a.seuil_max || '--'})<br>
                        <span class="alert-date">${a.date || '--'} - ${a.message || ''}</span>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<p style="color:#666;">Aucune alerte active.</p>';
        }
    } catch (error) {
        console.error('Erreur chargement alertes:', error);
        container.innerHTML = '<p style="color:#e63946;">Erreur de chargement des alertes.</p>';
    }
}

// ==================== IMPORT CSV ====================
function initImportExport() {
    const fileInput = document.getElementById('file-csv');
    const statusEl = document.getElementById('import-status');
    
    if (fileInput) {
        fileInput.addEventListener('change', async function(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            if (statusEl) statusEl.textContent = 'Import en cours...';
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch(API_URL + '/upload/csv', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (statusEl) statusEl.textContent = data.lignes_importées + ' lignes importées avec succès';
                    showToast(data.lignes_importées + ' lignes importées', 'success');
                    chargerDashboard();
                } else {
                    if (statusEl) statusEl.textContent = 'Erreur lors de l\'import';
                    showToast('Erreur lors de l\'import', 'error');
                }
            } catch (error) {
                if (statusEl) statusEl.textContent = 'Erreur de connexion';
                showToast('Erreur de connexion', 'error');
            }
        });
    }
    
    // Bouton export (peut être dans le dashboard ou dans la page import)
    const exportBtns = document.querySelectorAll('[onclick="exporterCSV()"]');
    exportBtns.forEach(btn => {
        btn.addEventListener('click', exporterCSV);
    });
}

async function exporterCSV() {
    try {
        const response = await fetch(API_URL + '/export/csv', { headers });
        const data = await response.json();
        
        const blob = new Blob([data.data], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'littowatch-export-' + new Date().toISOString().split('T')[0] + '.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('Export réussi !', 'success');
    } catch (error) {
        console.error('Erreur export:', error);
        showToast('Erreur lors de l\'export', 'error');
    }
}

// ==================== INITIALISATION ====================
document.addEventListener('DOMContentLoaded', function() {
    // Afficher les infos utilisateur
    afficherInfosUtilisateur();
    
    // Afficher la date
    afficherDate();
    
    // Initialiser la navigation
    initNavigation();
    
    // Initialiser le formulaire d'observation
    initFormulaireObservation();
    
    // Initialiser l'import/export
    initImportExport();
    
    // Charger le dashboard au démarrage
    chargerDashboard();
    
    // Bouton déconnexion
    const logoutBtn = document.querySelector('.btn-logout') || document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', deconnexion);
    }
});
