// Vérifier si l'utilisateur est connecté
const token = localStorage.getItem('token');
if (!token) {
    window.location.href = 'connexion.html';
}

// Ajouter le token à toutes les requêtes
const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
};

// Fonction de déconnexion
function deconnexion() {
    localStorage.removeItem('token');
    localStorage.removeItem('utilisateur');
    window.location.href = 'connexion.html';
}
const API_URL = 'https://litto-watch.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    document.querySelectorAll('.nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.dataset.page;
            
            document.querySelectorAll('.nav a').forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');
            
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(page).classList.add('active');
            
            if (page === 'map') setTimeout(initMap, 100);
        });
    });
    
    // Charger le dashboard
    loadDashboard();
    loadAlerts();
    
    // Formulaire d'observation
    document.getElementById('observation-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const observation = {
            latitude: parseFloat(document.getElementById('latitude').value),
            longitude: parseFloat(document.getElementById('longitude').value),
            date: document.getElementById('date').value,
            temperature_eau: parseFloat(document.getElementById('temperature_eau').value) || null,
            salinite: parseFloat(document.getElementById('salinite').value) || null,
            ph: parseFloat(document.getElementById('ph').value) || null,
            oxygene_dissous: parseFloat(document.getElementById('oxygene_dissous').value) || null,
            turbidite: parseFloat(document.getElementById('turbidite').value) || null,
            conductivite: parseFloat(document.getElementById('conductivite').value) || null,
            profondeur: parseFloat(document.getElementById('profondeur').value) || null,
            nitrates: parseFloat(document.getElementById('nitrates').value) || null,
            phosphates: parseFloat(document.getElementById('phosphates').value) || null,
            matiere_organique: parseFloat(document.getElementById('matiere_organique').value) || null,
            type_mangrove: document.getElementById('type_mangrove').value || null,
            nature_sol: document.getElementById('nature_sol').value || null,
            niveau_degradation: document.getElementById('niveau_degradation').value || null,
            especes_presentes: document.getElementById('especes_presentes').value || null,
            notes: document.getElementById('notes').value || null
        };
        
        try {
            const response = await fetch(`${API_URL}/observations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(observation)
            });
            
            if (response.ok) {
                alert('Observation enregistrée !');
                document.getElementById('observation-form').reset();
                loadDashboard();
                loadAlerts();
            }
        } catch (err) {
            console.error("Erreur:", err);
            alert("Erreur lors de l'enregistrement");
        }
    });
    
    // Import CSV
    document.getElementById('import-csv').addEventListener('click', async () => {
        const file = document.getElementById('csv-file').files[0];
        if (!file) return alert('Sélectionnez un fichier');
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_URL}/upload/csv`, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            alert(`Import réussi : ${data.lignes_importées} lignes`);
            loadDashboard();
        } catch (err) {
            console.error("Erreur import:", err);
        }
    });
    
    // Export CSV
    document.getElementById('export-csv').addEventListener('click', async () => {
        try {
            const response = await fetch(`${API_URL}/export/csv`);
            const data = await response.json();
            const blob = new Blob([data.data], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'litto-watch-export.csv';
            a.click();
        } catch (err) {
            console.error("Erreur export:", err);
        }
    });
});

async function loadDashboard() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const stats = await response.json();
        
        document.getElementById('nb-observations').textContent = stats.nombre_observations || '--';
        document.getElementById('temp-moyenne').textContent = stats.temperature_moyenne ? `${stats.temperature_moyenne.toFixed(1)} °C` : '--';
        document.getElementById('salinite-moyenne').textContent = stats.salinite_moyenne ? `${stats.salinite_moyenne.toFixed(1)} ppt` : '--';
        
        const alertsResp = await fetch(`${API_URL}/alerts`);
        const alerts = await alertsResp.json();
        document.getElementById('nb-alertes').textContent = alerts.length;
    } catch (err) {
        console.error("Erreur dashboard:", err);
    }
}

async function loadAlerts() {
    try {
        const response = await fetch(`${API_URL}/alerts`);
        const alerts = await response.json();
        
        const container = document.getElementById('alerts-list');
        if (alerts.length === 0) {
            container.innerHTML = '<p>Aucune alerte active.</p>';
            return;
        }
        
        container.innerHTML = alerts.map(a => `
            <div class="alert-card">
                <b>${a.parametre}</b> : ${a.valeur} (seuil: ${a.seuil})<br>
                <small>${a.message} - ${a.date}</small>
            </div>
        `).join('');
    } catch (err) {
        console.error("Erreur alertes:", err);
    }
}
