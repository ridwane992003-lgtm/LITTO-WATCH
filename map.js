let map;
let markers = [];
const API_URL = 'https://litto-watch.onrender.com';

function initMap() {
    map = L.map('map-container').setView([14.5, -17.0], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap | LITTO-WATCH',
        maxZoom: 19
    }).addTo(map);
    
    loadObservations();
}

async function loadObservations() {
    try {
        const response = await fetch(`${API_URL}/observations`);
        const data = await response.json();
        
        markers.forEach(m => map.removeLayer(m));
        markers = [];
        
        data.forEach((obs, index) => {
            const marker = L.marker([obs.latitude, obs.longitude])
                .addTo(map)
                .bindPopup(`
                    <b>Observation #${index + 1}</b><br>
                    Date: ${obs.date}<br>
                    Temp: ${obs.temperature_eau ?? 'N/A'}°C<br>
                    Salinité: ${obs.salinite ?? 'N/A'} ppt<br>
                    pH: ${obs.ph ?? 'N/A'}<br>
                    Type: ${obs.type_mangrove ?? 'N/A'}<br>
                    Dégradation: ${obs.niveau_degradation ?? 'N/A'}
                `);
            markers.push(marker);
        });
    } catch (err) {
        console.error("Erreur chargement carte:", err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const mapPage = document.querySelector('[data-page="map"]');
    mapPage.addEventListener('click', () => {
        if (!map) {
            setTimeout(initMap, 100);
        }
    });
});
