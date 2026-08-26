// State Management
let currentCoords = { lat: 28.6139, lon: 77.2090, name: "New Delhi", country: "IN" };
let currentUnits = "metric"; // 'metric' or 'imperial'
let activeFavorites = [];
let isStarred = false;

// DOM Elements
const searchInput = document.getElementById('city-search');
const searchResults = document.getElementById('search-results');
const clearSearchBtn = document.getElementById('clear-search');
const geolocateBtn = document.getElementById('geolocate-btn');
const unitMetricBtn = document.getElementById('unit-metric');
const unitImperialBtn = document.getElementById('unit-imperial');
const starBtn = document.getElementById('star-btn');
const favoritesContainer = document.getElementById('favorites-container');

// Weather Condition Icons Mapping
function getConditionIcon(code) {
    const map = {
        'clear_day': 'fa-sun text-amber-400',
        'mainly_clear': 'fa-cloud-sun text-amber-300',
        'partly_cloudy': 'fa-cloud-sun text-sky-300',
        'overcast': 'fa-cloud text-slate-300',
        'fog': 'fa-smog text-slate-400',
        'drizzle_light': 'fa-cloud-rain text-sky-400',
        'drizzle_moderate': 'fa-cloud-showers-heavy text-sky-400',
        'drizzle_dense': 'fa-cloud-showers-heavy text-sky-500',
        'rain_light': 'fa-cloud-rain text-sky-400',
        'rain_moderate': 'fa-cloud-showers-heavy text-sky-400',
        'rain_heavy': 'fa-cloud-showers-water text-indigo-400',
        'snow_light': 'fa-snowflake text-sky-200',
        'snow_moderate': 'fa-snowflake text-sky-300',
        'snow_heavy': 'fa-icicles text-indigo-200',
        'thunderstorm': 'fa-bolt text-amber-400',
        'thunderstorm_hail': 'fa-cloud-bolt text-indigo-400'
    };
    return map[code] || 'fa-cloud text-sky-300';
}

// Initial Boot
document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    await loadFavorites();
    detectGeolocation();
});

function setupEventListeners() {
    // Search input with debounce
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        clearSearchBtn.classList.toggle('hidden', !val);
        clearTimeout(debounceTimer);
        if (val.length >= 2) {
            debounceTimer = setTimeout(() => performSearch(val), 250);
        } else {
            searchResults.classList.add('hidden');
        }
    });

    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearSearchBtn.classList.add('hidden');
        searchResults.classList.add('hidden');
    });

    // Close search dropdown on click outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    // Unit toggle
    unitMetricBtn.addEventListener('click', () => switchUnits('metric'));
    unitImperialBtn.addEventListener('click', () => switchUnits('imperial'));

    // Geolocation trigger
    geolocateBtn.addEventListener('click', () => detectGeolocation(true));

    // Star / Favorite toggle
    starBtn.addEventListener('click', toggleFavorite);
}

function switchUnits(newUnit) {
    if (currentUnits === newUnit) return;
    currentUnits = newUnit;

    if (newUnit === 'metric') {
        unitMetricBtn.className = "px-2.5 py-1 rounded-full bg-sky-500 text-white transition-all";
        unitImperialBtn.className = "px-2.5 py-1 rounded-full text-slate-400 hover:text-white transition-all";
        document.getElementById('unit-wind').innerText = "km/h";
        document.getElementById('unit-vis').innerText = "km";
    } else {
        unitImperialBtn.className = "px-2.5 py-1 rounded-full bg-sky-500 text-white transition-all";
        unitMetricBtn.className = "px-2.5 py-1 rounded-full text-slate-400 hover:text-white transition-all";
        document.getElementById('unit-wind').innerText = "mph";
        document.getElementById('unit-vis').innerText = "mi";
    }

    refreshWeatherData();
}

function detectGeolocation(userInitiated = false) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                currentCoords.lat = pos.coords.latitude;
                currentCoords.lon = pos.coords.longitude;
                currentCoords.name = "My Location";
                currentCoords.country = "";
                refreshWeatherData();
            },
            (err) => {
                console.warn("Geolocation denied or unavailable:", err.message);
                if (userInitiated) {
                    alert("Location access denied or unavailable. Showing default city.");
                }
                refreshWeatherData();
            },
            { timeout: 8000 }
        );
    } else {
        refreshWeatherData();
    }
}

async function performSearch(query) {
    try {
        const res = await fetch(`/api/v1/locations/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        renderSearchResults(data.results || []);
    } catch (e) {
        console.error("Geocoding search failed:", e);
    }
}

function renderSearchResults(results) {
    searchResults.innerHTML = '';
    if (!results || results.length === 0) {
        searchResults.innerHTML = '<div class="p-3 text-xs text-slate-400">No matching cities found</div>';
        searchResults.classList.remove('hidden');
        return;
    }

    results.forEach(loc => {
        const item = document.createElement('div');
        item.className = "p-3 hover:bg-slate-700/60 cursor-pointer flex items-center justify-between text-xs transition-colors";
        item.innerHTML = `
            <div>
                <span class="font-bold text-white">${loc.name}</span>
                <span class="text-slate-400 ml-1">${loc.administrative_area ? loc.administrative_area + ', ' : ''}${loc.country}</span>
            </div>
            <span class="text-[11px] text-sky-400 font-mono">${loc.country_code}</span>
        `;
        item.addEventListener('click', () => {
            currentCoords = { lat: loc.lat, lon: loc.lon, name: loc.name, country: loc.country_code };
            searchInput.value = `${loc.name}, ${loc.country}`;
            searchResults.classList.add('hidden');
            refreshWeatherData();
        });
        searchResults.appendChild(item);
    });

    searchResults.classList.remove('hidden');
}

async function refreshWeatherData() {
    const { lat, lon, name } = currentCoords;
    updateStarStatus();

    // 1. Fetch Current Weather
    try {
        const curRes = await fetch(`/api/v1/weather/current?lat=${lat}&lon=${lon}&units=${currentUnits}`);
        if (curRes.ok) {
            const curData = await curRes.json();
            renderCurrentWeather(curData);
        }
    } catch (e) {
        console.error("Current weather error:", e);
    }

    // 2. Fetch Forecast
    try {
        const fcRes = await fetch(`/api/v1/weather/forecast?lat=${lat}&lon=${lon}&hourly_steps=24&daily_steps=7&units=${currentUnits}`);
        if (fcRes.ok) {
            const fcData = await fcRes.json();
            renderForecast(fcData);
        }
    } catch (e) {
        console.error("Forecast error:", e);
    }
}

function renderCurrentWeather(data) {
    const loc = data.location;
    const c = data.current;
    const life = data.lifestyle_indices || {};

    const displayName = currentCoords.name !== "My Location" ? currentCoords.name : loc.name;
    document.getElementById('location-name').innerText = displayName;
    document.getElementById('location-meta').innerText = `${loc.region ? loc.region + ', ' : ''}${loc.country || ''} • Timezone: ${loc.timezone}`;

    // Hero
    document.getElementById('current-temp').innerText = `${Math.round(c.temp)}°`;
    document.getElementById('feels-like').innerText = `Feels like ${Math.round(c.feels_like)}°`;
    document.getElementById('current-condition').innerText = c.condition;
    document.getElementById('temp-high').innerText = `${Math.round(c.temp_max)}°`;
    document.getElementById('temp-low').innerText = `${Math.round(c.temp_min)}°`;

    // Dynamic Hero Icon
    const iconClass = getConditionIcon(c.condition_code);
    const heroIcon = document.getElementById('hero-weather-icon');
    heroIcon.className = `fa-solid ${iconClass} text-xl`;
    const heroBgIcon = document.getElementById('hero-bg-icon');
    heroBgIcon.className = `fa-solid ${iconClass}`;

    // Atmospheric metrics
    document.getElementById('val-humidity').innerText = `${c.humidity}%`;
    document.getElementById('val-dewpoint').innerText = `Dew Point: ${Math.round(c.dew_point)}°`;
    document.getElementById('val-wind').innerText = c.wind.speed_kmh;
    document.getElementById('val-wind-dir').innerText = `${c.wind.cardinal} (${c.wind.direction_deg}°) • Gusts: ${c.wind.gust_kmh}`;
    document.getElementById('val-pressure').innerText = Math.round(c.pressure_hpa);
    document.getElementById('val-uv').innerText = c.uv_index;
    document.getElementById('val-uv-badge').innerText = c.uv_category;
    document.getElementById('val-visibility').innerText = c.visibility_km;
    document.getElementById('val-clouds').innerText = `Cloud cover: ${c.cloud_cover_pct}%`;
    document.getElementById('val-aqi').innerText = c.air_quality.aqi_us;
    document.getElementById('val-aqi-badge').innerText = c.air_quality.category;

    // Lifestyle
    if (life.outdoor_running) {
        document.getElementById('running-rating').innerText = `${life.outdoor_running.rating} (${life.outdoor_running.score}/100)`;
        document.getElementById('running-summary').innerText = life.outdoor_running.summary;
    }
    if (life.car_wash) {
        document.getElementById('carwash-rating').innerText = life.car_wash.rating;
        document.getElementById('carwash-summary').innerText = life.car_wash.summary;
    }
    if (life.sun_protection) {
        document.getElementById('sun-timer').innerText = `~${life.sun_protection.time_to_burn_mins} mins to burn`;
        document.getElementById('sun-recommendation').innerText = life.sun_protection.recommendation;
    }
}

function renderForecast(data) {
    // 1. Render 24-Hour Scrubber
    const timeline = document.getElementById('hourly-timeline');
    timeline.innerHTML = '';

    (data.hourly || []).forEach(h => {
        const timeObj = new Date(h.time);
        const timeFormatted = isNaN(timeObj) ? h.time.split('T')[1] : timeObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const iconClass = getConditionIcon(h.condition_code);

        const card = document.createElement('div');
        card.className = "flex-shrink-0 w-24 bg-slate-800/80 hover:bg-slate-700/60 border border-sky-800/30 rounded-2xl p-3 text-center flex flex-col items-center justify-between transition-all";
        card.innerHTML = `
            <span class="text-xs font-semibold text-slate-300">${timeFormatted}</span>
            <i class="fa-solid ${iconClass} my-2.5 text-lg"></i>
            <span class="text-sm font-extrabold text-white">${Math.round(h.temp)}°</span>
            <div class="mt-2 flex items-center space-x-1 text-[10px] text-sky-400 font-medium">
                <i class="fa-solid fa-droplet text-[9px]"></i>
                <span>${h.precip_probability}%</span>
            </div>
        `;
        timeline.appendChild(card);
    });

    // 2. Render 7-Day Extended Outlook
    const dailyList = document.getElementById('daily-forecast-list');
    dailyList.innerHTML = '';

    (data.daily || []).forEach(d => {
        const iconClass = getConditionIcon(d.condition_code);
        const row = document.createElement('div');
        row.className = "py-3 flex items-center justify-between text-xs sm:text-sm hover:bg-slate-800/40 px-2 rounded-xl transition-colors";
        row.innerHTML = `
            <div class="w-24 font-bold text-white">${d.day_name}</div>
            <div class="flex items-center space-x-2 w-32">
                <i class="fa-solid ${iconClass} text-sm"></i>
                <span class="text-slate-300 text-xs truncate">${d.condition}</span>
            </div>
            <div class="flex items-center space-x-1.5 text-sky-400 text-xs w-16">
                <i class="fa-solid fa-droplet text-[10px]"></i>
                <span>${d.precip_probability}%</span>
            </div>
            <div class="flex items-center space-x-2 text-right">
                <span class="font-bold text-white">${Math.round(d.temp_max)}°</span>
                <span class="text-slate-400 text-xs">${Math.round(d.temp_min)}°</span>
            </div>
        `;
        dailyList.appendChild(row);
    });
}

// Favorites Management
async function loadFavorites() {
    try {
        const res = await fetch('/api/v1/locations/favorites');
        if (res.ok) {
            activeFavorites = await res.json();
            renderFavoritesBar();
        }
    } catch (e) {
        console.error("Failed to load favorites:", e);
    }
}

function renderFavoritesBar() {
    favoritesContainer.innerHTML = '';
    if (activeFavorites.length === 0) {
        favoritesContainer.innerHTML = '<span class="text-xs text-slate-500 italic">No favorite cities saved (click star to save)</span>';
        return;
    }

    activeFavorites.forEach(fav => {
        const btn = document.createElement('div');
        btn.className = "group flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-800 hover:bg-sky-900/50 border border-sky-800/50 text-xs text-slate-200 cursor-pointer transition-all";
        btn.innerHTML = `
            <span class="font-medium">${fav.city_name}</span>
            <button class="text-slate-500 hover:text-rose-400 ml-1 text-[10px]" title="Remove favorite">&times;</button>
        `;
        btn.querySelector('span').addEventListener('click', () => {
            currentCoords = { lat: fav.latitude, lon: fav.longitude, name: fav.city_name, country: fav.country_code };
            refreshWeatherData();
        });
        btn.querySelector('button').addEventListener('click', async (e) => {
            e.stopPropagation();
            await removeFavorite(fav.id);
        });
        favoritesContainer.appendChild(btn);
    });
}

function updateStarStatus() {
    const found = activeFavorites.some(
        f => Math.abs(f.latitude - currentCoords.lat) < 0.05 && Math.abs(f.longitude - currentCoords.lon) < 0.05
    );
    isStarred = found;
    starBtn.innerHTML = isStarred ? '<i class="fa-solid fa-star text-amber-400"></i>' : '<i class="fa-regular fa-star"></i>';
}

async function toggleFavorite() {
    if (isStarred) {
        const fav = activeFavorites.find(
            f => Math.abs(f.latitude - currentCoords.lat) < 0.05 && Math.abs(f.longitude - currentCoords.lon) < 0.05
        );
        if (fav) {
            await removeFavorite(fav.id);
        }
    } else {
        if (activeFavorites.length >= 5) {
            alert("Maximum limit of 5 favorite locations reached for MVP.");
            return;
        }
        try {
            const res = await fetch('/api/v1/locations/favorites', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    city_name: currentCoords.name,
                    country_code: currentCoords.country || 'GB',
                    latitude: currentCoords.lat,
                    longitude: currentCoords.lon,
                    display_order: activeFavorites.length
                })
            });
            if (res.ok) {
                await loadFavorites();
                updateStarStatus();
            }
        } catch (e) {
            console.error("Save favorite failed:", e);
        }
    }
}

async function removeFavorite(id) {
    try {
        const res = await fetch(`/api/v1/locations/favorites/${id}`, { method: 'DELETE' });
        if (res.ok) {
            await loadFavorites();
            updateStarStatus();
        }
    } catch (e) {
        console.error("Delete favorite failed:", e);
    }
}

function resetToDefault() {
    currentCoords = { lat: 28.6139, lon: 77.2090, name: "New Delhi", country: "IN" };
    searchInput.value = '';
    refreshWeatherData();
}
