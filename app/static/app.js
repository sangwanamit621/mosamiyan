// ==========================================
// Mosamiyan Weather Platform — Phase 2 Engine
// ==========================================

// Carto Basemaps API Key from .env / window configuration
const CARTO_BASEMAPS_API_KEY = window.CARTO_BASEMAPS_API_KEY || "";

// Global State
let currentCoords = { lat: 28.6139, lon: 77.2090, name: "New Delhi", country: "IN" };
let currentUnits = "metric"; // 'metric' or 'imperial'
let activeFavorites = [];
let currentTheme = localStorage.getItem('mosamiyan_theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
let activeAlertsData = null;

// Map & Radar State
let weatherMap = null;
let locationMarker = null;
let baseTileLayer = null;
let radarTileLayer = null;
let radarFrames = []; // Combined array of past + nowcast frames
let currentFrameIndex = 0;
let radarInterval = null;
let isRadarPlaying = false;
let activeLayerType = 'radar'; // 'radar' or 'clouds'
let radarHost = "https://tilecache.rainviewer.com";

// DOM Elements
const searchInput = document.getElementById('city-search');
const searchResults = document.getElementById('search-results');
const clearSearchBtn = document.getElementById('clear-search');
const geolocateBtn = document.getElementById('geolocate-btn');
const unitMetricBtn = document.getElementById('unit-metric');
const unitImperialBtn = document.getElementById('unit-imperial');
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const themeIcon = document.getElementById('theme-icon');
const starBtn = document.getElementById('star-btn');
const favoritesContainer = document.getElementById('favorites-container');

// Alert Elements
const alertBanner = document.getElementById('alert-banner');
const alertBannerInner = document.getElementById('alert-banner-inner');
const alertBannerIcon = document.getElementById('alert-banner-icon');
const alertBadge = document.getElementById('alert-badge');
const alertAgency = document.getElementById('alert-agency');
const alertTitle = document.getElementById('alert-title');
const openAlertModalBtn = document.getElementById('open-alert-modal-btn');
const alertModal = document.getElementById('alert-modal');
const closeAlertModal = document.getElementById('close-alert-modal');
const modalCloseBtn = document.getElementById('modal-close-btn');

// Radar Elements
const radarPlayPauseBtn = document.getElementById('radar-play-pause');
const radarPlayIcon = document.getElementById('radar-play-icon');
const radarPlayText = document.getElementById('radar-play-text');
const radarStepBackBtn = document.getElementById('radar-step-back');
const radarStepForwardBtn = document.getElementById('radar-step-forward');
const radarTimeSlider = document.getElementById('radar-time-slider');
const radarFrameType = document.getElementById('radar-frame-type');
const radarFrameTime = document.getElementById('radar-frame-time');
const layerRadarBtn = document.getElementById('layer-radar');
const layerCloudsBtn = document.getElementById('layer-clouds');
const mapRecenterBtn = document.getElementById('map-recenter-btn');
const mapFullscreenBtn = document.getElementById('map-fullscreen-btn');

// Weather Condition Icons Mapping
function getConditionIcon(code) {
    const map = {
        'clear_day': 'fa-sun text-amber-400',
        'mainly_clear': 'fa-cloud-sun text-amber-300',
        'partly_cloudy': 'fa-cloud-sun text-sky-400',
        'overcast': 'fa-cloud text-slate-400',
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
    return map[code] || 'fa-cloud text-sky-400';
}

// ==========================================
// Initial Boot & Event Listeners
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    setupEventListeners();
    initMap(currentCoords.lat, currentCoords.lon);
    await loadFavorites();
    await fetchRadarMetadata();
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

    // Theme toggle
    themeToggleBtn.addEventListener('click', toggleTheme);

    // Geolocation trigger
    geolocateBtn.addEventListener('click', () => detectGeolocation(true));

    // Star / Favorite toggle
    starBtn.addEventListener('click', toggleFavorite);

    // Alert Modal
    openAlertModalBtn.addEventListener('click', openAlertModal);
    closeAlertModal.addEventListener('click', closeAlertModalDialog);
    modalCloseBtn.addEventListener('click', closeAlertModalDialog);
    alertModal.addEventListener('click', (e) => {
        if (e.target === alertModal) closeAlertModalDialog();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !alertModal.classList.contains('hidden')) {
            closeAlertModalDialog();
        }
    });

    // Radar Playback Controls
    radarPlayPauseBtn.addEventListener('click', toggleRadarPlayback);
    radarStepBackBtn.addEventListener('click', () => stepRadar(-1));
    radarStepForwardBtn.addEventListener('click', () => stepRadar(1));
    radarTimeSlider.addEventListener('input', (e) => {
        pauseRadar();
        setRadarFrame(parseInt(e.target.value, 10));
    });

    // Layer Controls
    layerRadarBtn.addEventListener('click', () => setRadarLayerType('radar'));
    layerCloudsBtn.addEventListener('click', () => setRadarLayerType('clouds'));

    // Map Controls
    mapRecenterBtn.addEventListener('click', () => {
        if (weatherMap && currentCoords) {
            weatherMap.flyTo([currentCoords.lat, currentCoords.lon], 9, { duration: 1.2 });
        }
    });
    mapFullscreenBtn.addEventListener('click', toggleMapFullscreen);
}

// ==========================================
// Theme Engine (Dark / Light Mode)
// ==========================================
function initTheme() {
    if (currentTheme === 'dark') {
        document.documentElement.classList.add('dark');
        themeIcon.className = 'fa-solid fa-sun text-sm text-amber-300';
    } else {
        document.documentElement.classList.remove('dark');
        themeIcon.className = 'fa-solid fa-moon text-sm text-slate-700';
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('mosamiyan_theme', currentTheme);
    initTheme();
    updateMapTileLayer();
}

function updateMapTileLayer() {
    if (!weatherMap) return;
    if (baseTileLayer) {
        weatherMap.removeLayer(baseTileLayer);
    }
    const keyParam = CARTO_BASEMAPS_API_KEY ? `?key=${CARTO_BASEMAPS_API_KEY}` : '';
    const tileUrl = currentTheme === 'dark'
        ? `https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png${keyParam}`
        : `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png${keyParam}`;

    baseTileLayer = L.tileLayer(tileUrl, {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a>, &copy; OpenStreetMap',
        maxZoom: 18
    }).addTo(weatherMap);

    if (radarTileLayer) {
        radarTileLayer.bringToFront();
    }
}

// ==========================================
// Unit Switching Engine
// ==========================================
function switchUnits(newUnit) {
    if (currentUnits === newUnit) return;
    currentUnits = newUnit;

    if (newUnit === 'metric') {
        unitMetricBtn.className = "px-2.5 py-1 rounded-full bg-sky-500 text-white transition-all";
        unitImperialBtn.className = "px-2.5 py-1 rounded-full text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-all";
        document.getElementById('unit-wind').innerText = "km/h";
        document.getElementById('unit-vis').innerText = "km";
    } else {
        unitImperialBtn.className = "px-2.5 py-1 rounded-full bg-sky-500 text-white transition-all";
        unitMetricBtn.className = "px-2.5 py-1 rounded-full text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-all";
        document.getElementById('unit-wind').innerText = "mph";
        document.getElementById('unit-vis').innerText = "mi";
    }

    refreshWeatherData();
}

// ==========================================
// Geolocation & Data Refresh
// ==========================================
function detectGeolocation(userInitiated = false) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                currentCoords.lat = pos.coords.latitude;
                currentCoords.lon = pos.coords.longitude;
                currentCoords.name = "My Location";
                currentCoords.country = "";
                updateMapMarker();
                refreshWeatherData();
            },
            (err) => {
                console.warn("Geolocation denied or unavailable:", err.message);
                if (userInitiated) {
                    alert("Location access denied or unavailable. Showing default city.");
                }
                updateMapMarker();
                refreshWeatherData();
            },
            { timeout: 8000 }
        );
    } else {
        updateMapMarker();
        refreshWeatherData();
    }
}

function resetToDefault() {
    currentCoords = { lat: 28.6139, lon: 77.2090, name: "New Delhi", country: "IN" };
    searchInput.value = '';
    clearSearchBtn.classList.add('hidden');
    searchResults.classList.add('hidden');
    updateMapMarker();
    refreshWeatherData();
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

    // 2. Fetch 48-Hour Hourly & 14-Day Daily Forecast
    try {
        const fcRes = await fetch(`/api/v1/weather/forecast?lat=${lat}&lon=${lon}&hourly_steps=48&daily_steps=14&units=${currentUnits}`);
        if (fcRes.ok) {
            const fcData = await fcRes.json();
            renderForecast(fcData);
        }
    } catch (e) {
        console.error("Forecast error:", e);
    }

    // 3. Fetch Severe Weather Alerts
    try {
        const alRes = await fetch(`/api/v1/weather/alerts?lat=${lat}&lon=${lon}`);
        if (alRes.ok) {
            const alData = await alRes.json();
            renderAlerts(alData);
        }
    } catch (e) {
        console.error("Alerts fetch error:", e);
    }
}

// ==========================================
// Current Weather Rendering
// ==========================================
function renderCurrentWeather(data) {
    const loc = data.location;
    const c = data.current;
    const life = data.lifestyle_indices || {};

    const displayName = currentCoords.name !== "My Location" ? currentCoords.name : loc.name;
    document.getElementById('location-name').innerText = displayName;
    document.getElementById('location-meta').innerText = `${loc.region ? loc.region + ', ' : ''}${loc.country || ''} • Timezone: ${loc.timezone}`;

    // Format target location's current local time
    try {
        const targetLocalTime = new Intl.DateTimeFormat('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
            timeZone: loc.timezone || undefined
        }).format(new Date());
        const localTimeElem = document.getElementById('local-time');
        if (localTimeElem) localTimeElem.innerText = targetLocalTime;
    } catch (e) {
        console.debug("Local time formatting fallback:", e);
    }

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

// ==========================================
// 48-Hour & 14-Day Forecast Rendering
// ==========================================
function renderForecast(data) {
    // 1. Render 48-Hour Scrubber
    const timeline = document.getElementById('hourly-timeline');
    timeline.innerHTML = '';

    const targetTimezone = (data.location && data.location.timezone) ? data.location.timezone : undefined;

    (data.hourly || []).forEach((h, idx) => {
        let timeFormatted = '';
        try {
            const timeObj = new Date(h.time);
            if (!isNaN(timeObj)) {
                timeFormatted = new Intl.DateTimeFormat('en-US', {
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true,
                    timeZone: targetTimezone
                }).format(timeObj);
            } else {
                timeFormatted = h.time.split('T')[1] || h.time;
            }
        } catch (e) {
            timeFormatted = h.time.includes('T') ? h.time.split('T')[1].substring(0, 5) : h.time;
        }

        const iconClass = getConditionIcon(h.condition_code);

        const card = document.createElement('div');
        card.className = "flex-shrink-0 w-24 bg-slate-50 dark:bg-slate-800/80 hover:bg-sky-50 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-sky-800/30 rounded-2xl p-3 text-center flex flex-col items-center justify-between transition-all shadow-sm hover:shadow-md cursor-pointer";
        card.title = `${timeFormatted}: ${h.condition}, Temp: ${Math.round(h.temp)}°, Wind: ${h.wind_speed_kmh} ${currentUnits === 'metric' ? 'km/h' : 'mph'}, Rain: ${h.precip_probability}%`;

        card.innerHTML = `
            <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-300 whitespace-nowrap">${timeFormatted}</span>
            <i class="fa-solid ${iconClass} my-2 text-lg"></i>
            <span class="text-sm font-extrabold text-slate-900 dark:text-white">${Math.round(h.temp)}°</span>
            
            <!-- Precipitation Vertical Probability Bar -->
            <div class="w-full mt-2 flex flex-col items-center gap-1">
                <div class="w-2.5 h-10 bg-slate-200 dark:bg-slate-700/70 rounded-full overflow-hidden flex flex-col justify-end p-0.5">
                    <div class="w-full bg-gradient-to-t from-sky-500 to-teal-400 rounded-full" style="height: ${h.precip_probability}%"></div>
                </div>
                <span class="text-[10px] text-sky-600 dark:text-sky-400 font-bold">${h.precip_probability}%</span>
            </div>
        `;
        timeline.appendChild(card);
    });

    // 2. Render 14-Day Extended Daily Forecast with Accordion Drilldown
    const dailyList = document.getElementById('daily-forecast-list');
    dailyList.innerHTML = '';

    (data.daily || []).forEach((d, idx) => {
        const iconClass = getConditionIcon(d.condition_code);
        const isToday = idx === 0 || d.day_name === "Today";
        const precipUnit = currentUnits === "metric" ? "mm" : "in";
        const windUnit = currentUnits === "metric" ? "km/h" : "mph";

        const row = document.createElement('div');
        row.className = "rounded-2xl border border-slate-200 dark:border-sky-900/30 overflow-hidden bg-slate-50 dark:bg-slate-800/40 transition-all";

        row.innerHTML = `
            <!-- Accordion Header -->
            <div class="accordion-header p-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800/70 transition-colors select-none">
                <div class="flex items-center space-x-3 w-40">
                    <span class="font-bold text-xs sm:text-sm text-slate-900 dark:text-white">${d.day_name}</span>
                    ${isToday ? '<span class="text-[10px] bg-sky-500 text-white font-extrabold px-2 py-0.5 rounded-full uppercase">Today</span>' : `<span class="text-[11px] text-slate-400 font-medium">${d.date.substring(5)}</span>`}
                </div>
                
                <div class="flex items-center space-x-2 w-32">
                    <i class="fa-solid ${iconClass} text-sm"></i>
                    <span class="text-slate-600 dark:text-slate-300 text-xs truncate">${d.condition}</span>
                </div>

                <div class="flex items-center space-x-1.5 text-sky-600 dark:text-sky-400 text-xs w-16">
                    <i class="fa-solid fa-droplet text-[10px]"></i>
                    <span class="font-semibold">${d.precip_probability}%</span>
                </div>

                <div class="flex items-center space-x-3">
                    <div class="flex items-center space-x-2 text-right">
                        <span class="font-bold text-slate-900 dark:text-white text-xs sm:text-sm">${Math.round(d.temp_max)}°</span>
                        <span class="text-slate-400 text-xs">${Math.round(d.temp_min)}°</span>
                    </div>
                    <i class="fa-solid fa-chevron-down text-slate-400 text-xs transition-transform duration-200 accordion-chevron"></i>
                </div>
            </div>

            <!-- Accordion Details Panel -->
            <div class="accordion-body hidden px-4 py-3 bg-white/70 dark:bg-slate-900/60 border-t border-slate-200 dark:border-sky-900/30 text-xs text-slate-600 dark:text-slate-300 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                    <span class="text-slate-400 text-[11px] block"><i class="fa-solid fa-sun text-amber-400 mr-1"></i> Sunrise / Sunset</span>
                    <span class="font-bold text-slate-900 dark:text-white">${d.sunrise ? d.sunrise.substring(11, 16) : '--:--'} • ${d.sunset ? d.sunset.substring(11, 16) : '--:--'}</span>
                </div>
                <div>
                    <span class="text-slate-400 text-[11px] block"><i class="fa-solid fa-hourglass-half text-sky-400 mr-1"></i> Daylight Duration</span>
                    <span class="font-bold text-slate-900 dark:text-white">${d.daylight_duration || '12h 00m'}</span>
                </div>
                <div>
                    <span class="text-slate-400 text-[11px] block"><i class="fa-solid fa-shield-sun text-amber-400 mr-1"></i> Max UV Index</span>
                    <span class="font-bold text-amber-500 dark:text-amber-300">${d.uv_max}</span>
                </div>
                <div>
                    <span class="text-slate-400 text-[11px] block"><i class="fa-solid fa-wind text-sky-400 mr-1"></i> Peak Wind & Rain</span>
                    <span class="font-bold text-slate-900 dark:text-white">${d.wind_speed_max_kmh} ${windUnit} (${d.wind_direction_dominant || 'NW'}) • ${d.precip_accumulation_mm} ${precipUnit}</span>
                </div>
            </div>
        `;

        // Accordion click toggle
        const header = row.querySelector('.accordion-header');
        const body = row.querySelector('.accordion-body');
        const chevron = row.querySelector('.accordion-chevron');

        header.addEventListener('click', () => {
            const isHidden = body.classList.contains('hidden');
            body.classList.toggle('hidden', !isHidden);
            chevron.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
        });

        dailyList.appendChild(row);
    });
}

// ==========================================
// Severe Weather Alerts Engine
// ==========================================
function renderAlerts(data) {
    activeAlertsData = data;
    if (!data || data.alerts_count === 0 || !data.alerts || data.alerts.length === 0) {
        alertBanner.classList.add('hidden');
        return;
    }

    const primaryAlert = data.alerts[0];
    const sev = primaryAlert.severity || 'advisory';

    // Color styling classes based on severity level
    const severityStyles = {
        'advisory': {
            bg: 'bg-amber-500/15 border-amber-500/40 text-amber-900 dark:text-amber-100',
            badge: 'bg-amber-500 text-white',
            iconBg: 'bg-amber-500',
            icon: 'fa-triangle-exclamation'
        },
        'watch': {
            bg: 'bg-orange-500/15 border-orange-500/40 text-orange-900 dark:text-orange-100',
            badge: 'bg-orange-500 text-white',
            iconBg: 'bg-orange-500',
            icon: 'fa-triangle-exclamation'
        },
        'warning': {
            bg: 'bg-rose-500/20 border-rose-500/50 text-rose-900 dark:text-rose-100',
            badge: 'bg-rose-500 text-white',
            iconBg: 'bg-rose-600',
            icon: 'fa-radiation'
        },
        'emergency': {
            bg: 'bg-purple-600/25 border-purple-500/60 text-purple-900 dark:text-purple-100',
            badge: 'bg-purple-600 text-white',
            iconBg: 'bg-purple-700',
            icon: 'fa-skull-crossbones'
        }
    };

    const style = severityStyles[sev] || severityStyles['advisory'];
    alertBannerInner.className = `rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg border animate-subtle-pulse ${style.bg}`;
    document.getElementById('alert-icon-wrap').className = `w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-white font-bold ${style.iconBg}`;
    alertBannerIcon.className = `fa-solid ${style.icon}`;
    alertBadge.className = `text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full tracking-wider ${style.badge}`;
    alertBadge.innerText = sev;
    alertAgency.innerText = primaryAlert.issuing_agency || 'Official Meteorological Alert';
    alertTitle.innerText = primaryAlert.headline || primaryAlert.event_title;

    alertBanner.classList.remove('hidden');
}

function openAlertModal() {
    if (!activeAlertsData || !activeAlertsData.alerts || activeAlertsData.alerts.length === 0) return;
    const alert = activeAlertsData.alerts[0];
    const sev = alert.severity || 'advisory';

    const modalIcon = document.getElementById('modal-alert-icon');
    const modalSev = document.getElementById('modal-alert-severity');

    const badgeColors = {
        'advisory': 'bg-amber-500 text-white',
        'watch': 'bg-orange-500 text-white',
        'warning': 'bg-rose-600 text-white',
        'emergency': 'bg-purple-700 text-white'
    };

    modalIcon.className = `w-10 h-10 rounded-2xl flex items-center justify-center text-white text-lg ${badgeColors[sev] || 'bg-amber-500'}`;
    modalSev.className = `text-xs font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${badgeColors[sev] || 'bg-amber-500'}`;
    modalSev.innerText = sev;

    document.getElementById('modal-alert-title').innerText = alert.event_title;
    document.getElementById('modal-alert-agency').innerText = alert.issuing_agency;
    document.getElementById('modal-alert-timing').innerText = `Effective: ${alert.starts_at.substring(0, 16).replace('T', ' ')} UTC • Expiry: ${alert.expires_at.substring(0, 16).replace('T', ' ')} UTC`;
    document.getElementById('modal-alert-headline').innerText = alert.headline;
    document.getElementById('modal-alert-desc').innerText = alert.description;

    const instructionsElem = document.getElementById('modal-alert-instructions');
    const instructionsCont = document.getElementById('modal-instructions-container');
    if (alert.instructions) {
        instructionsElem.innerText = alert.instructions;
        instructionsCont.classList.remove('hidden');
    } else {
        instructionsCont.classList.add('hidden');
    }

    alertModal.classList.remove('hidden');
}

function closeAlertModalDialog() {
    alertModal.classList.add('hidden');
}

// ==========================================
// Interactive Weather Radar & Leaflet Map
// ==========================================
function initMap(lat, lon) {
    if (weatherMap) {
        weatherMap.remove();
    }

    weatherMap = L.map('weather-map', {
        center: [lat, lon],
        zoom: 8,
        zoomControl: true,
        attributionControl: false
    });

    updateMapTileLayer();
    updateMapMarker();
}

function updateMapTileLayer() {
    if (!weatherMap) return;
    if (baseTileLayer) {
        weatherMap.removeLayer(baseTileLayer);
    }
    const keyParam = CARTO_BASEMAPS_API_KEY ? `?key=${CARTO_BASEMAPS_API_KEY}` : '';
    const tileUrl = currentTheme === 'dark'
        ? `https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png${keyParam}`
        : `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png${keyParam}`;

    baseTileLayer = L.tileLayer(tileUrl, {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a>, &copy; OpenStreetMap',
        maxZoom: 18
    }).addTo(weatherMap);

    if (radarTileLayer) {
        radarTileLayer.bringToFront();
    }
}

function updateMapMarker() {
    if (!weatherMap) return;
    const { lat, lon, name } = currentCoords;

    if (locationMarker) {
        locationMarker.setLatLng([lat, lon]);
    } else {
        const customPin = L.divIcon({
            className: 'custom-map-pin',
            html: `<div class="w-6 h-6 rounded-full bg-sky-500 border-2 border-white shadow-lg flex items-center justify-center text-white text-[10px] animate-bounce"><i class="fa-solid fa-location-dot"></i></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 24]
        });
        locationMarker = L.marker([lat, lon], { icon: customPin }).addTo(weatherMap);
    }
    locationMarker.bindPopup(`<b>${name}</b><br>${lat.toFixed(2)}°, ${lon.toFixed(2)}°`).openPopup();
    weatherMap.setView([lat, lon], 8);
}

async function fetchRadarMetadata() {
    try {
        const res = await fetch('/api/v1/weather/radar-tiles');
        if (res.ok) {
            const data = await res.json();
            radarHost = data.host || "https://tilecache.rainviewer.com";
            radarFrames = [...(data.past_frames || []), ...(data.nowcast_frames || [])];

            if (radarFrames.length > 0) {
                radarTimeSlider.max = radarFrames.length - 1;
                // Default to latest past frame or nowcast
                const pastCount = (data.past_frames || []).length;
                currentFrameIndex = Math.max(0, pastCount - 1);
                radarTimeSlider.value = currentFrameIndex;
                setRadarFrame(currentFrameIndex);
            }
        }
    } catch (e) {
        console.warn("Radar tile metadata fetch error:", e);
    }
}

function setRadarFrame(index) {
    if (!radarFrames || radarFrames.length === 0 || !weatherMap) return;
    if (index < 0 || index >= radarFrames.length) return;

    currentFrameIndex = index;
    radarTimeSlider.value = index;

    const frame = radarFrames[index];
    const tileUrl = `${radarHost}${frame.path}`;

    if (radarTileLayer) {
        weatherMap.removeLayer(radarTileLayer);
    }

    radarTileLayer = L.tileLayer(tileUrl, {
        opacity: 0.7,
        zIndex: 20
    }).addTo(weatherMap);

    // Update Status Labels
    const frameDate = new Date(frame.time * 1000);
    const timeFormatted = frameDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    radarFrameTime.innerText = `${timeFormatted}`;

    if (frame.type === 'nowcast') {
        radarFrameType.className = "px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-600 dark:text-indigo-300 font-bold uppercase text-[10px]";
        radarFrameType.innerText = "Forecast";
    } else {
        radarFrameType.className = "px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-600 dark:text-sky-300 font-bold uppercase text-[10px]";
        radarFrameType.innerText = "History";
    }
}

function toggleRadarPlayback() {
    if (isRadarPlaying) {
        pauseRadar();
    } else {
        playRadar();
    }
}

function playRadar() {
    if (radarFrames.length === 0) return;
    isRadarPlaying = true;
    radarPlayIcon.className = "fa-solid fa-pause";
    radarPlayText.innerText = "Pause";

    clearInterval(radarInterval);
    radarInterval = setInterval(() => {
        let nextIndex = currentFrameIndex + 1;
        if (nextIndex >= radarFrames.length) {
            nextIndex = 0;
        }
        setRadarFrame(nextIndex);
    }, 750);
}

function pauseRadar() {
    isRadarPlaying = false;
    radarPlayIcon.className = "fa-solid fa-play";
    radarPlayText.innerText = "Play Loop";
    clearInterval(radarInterval);
}

function stepRadar(delta) {
    pauseRadar();
    let nextIndex = currentFrameIndex + delta;
    if (nextIndex < 0) nextIndex = radarFrames.length - 1;
    if (nextIndex >= radarFrames.length) nextIndex = 0;
    setRadarFrame(nextIndex);
}

function setRadarLayerType(type) {
    activeLayerType = type;
    if (type === 'radar') {
        layerRadarBtn.className = "px-3 py-1 rounded-lg bg-sky-500 text-white transition-all";
        layerCloudsBtn.className = "px-3 py-1 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-all";
        setRadarFrame(currentFrameIndex);
    } else {
        layerCloudsBtn.className = "px-3 py-1 rounded-lg bg-sky-500 text-white transition-all";
        layerRadarBtn.className = "px-3 py-1 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-all";
        if (radarTileLayer && weatherMap) {
            weatherMap.removeLayer(radarTileLayer);
        }
        // Satellite Cloud Overlay
        radarTileLayer = L.tileLayer('https://tilecache.rainviewer.com/v2/satellite/{z}/{x}/{y}/0/1_0.png', {
            opacity: 0.65,
            zIndex: 20
        }).addTo(weatherMap);
        radarFrameType.innerText = "Satellite";
        radarFrameTime.innerText = "Global Clouds";
    }
}

function toggleMapFullscreen() {
    const mapEl = document.getElementById('weather-map');
    if (!document.fullscreenElement) {
        mapEl.requestFullscreen().catch(err => console.debug("Fullscreen request error:", err));
    } else {
        document.exitFullscreen();
    }
}

// ==========================================
// Omnibox Geocoding Search Engine
// ==========================================
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
        item.className = "p-3 hover:bg-slate-100 dark:hover:bg-slate-700/60 cursor-pointer flex items-center justify-between text-xs transition-colors";
        item.innerHTML = `
            <div>
                <span class="font-bold text-slate-900 dark:text-white">${loc.name}</span>
                <span class="text-slate-500 dark:text-slate-400 ml-1">${loc.administrative_area ? loc.administrative_area + ', ' : ''}${loc.country}</span>
            </div>
            <span class="text-[11px] text-sky-600 dark:text-sky-400 font-mono font-bold">${loc.country_code}</span>
        `;
        item.addEventListener('click', () => {
            currentCoords = { lat: loc.lat, lon: loc.lon, name: loc.name, country: loc.country_code };
            searchInput.value = `${loc.name}, ${loc.country}`;
            searchResults.classList.add('hidden');
            updateMapMarker();
            refreshWeatherData();
        });
        searchResults.appendChild(item);
    });

    searchResults.classList.remove('hidden');
}

// ==========================================
// Favorites Management Engine (Raw SQL CRUD)
// ==========================================
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
        favoritesContainer.innerHTML = '<span class="text-xs text-slate-400 dark:text-slate-500 italic">No favorite cities saved (click star to save)</span>';
        return;
    }

    activeFavorites.forEach(fav => {
        const btn = document.createElement('div');
        btn.className = "group flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-sky-100 dark:hover:bg-sky-900/50 border border-slate-300 dark:border-sky-800/50 text-xs text-slate-700 dark:text-slate-200 cursor-pointer transition-all shadow-sm";
        btn.innerHTML = `
            <i class="fa-solid fa-location-dot text-[10px] text-sky-500"></i>
            <span class="font-medium">${fav.city_name}</span>
            <button class="delete-fav-btn opacity-0 group-hover:opacity-100 hover:text-rose-400 text-[10px] ml-1 transition-opacity" title="Remove">
                <i class="fa-solid fa-xmark"></i>
            </button>
        `;

        // Switch to this favorite
        btn.addEventListener('click', (e) => {
            if (e.target.closest('.delete-fav-btn')) return;
            currentCoords = {
                lat: fav.latitude,
                lon: fav.longitude,
                name: fav.city_name,
                country: fav.country_code
            };
            searchInput.value = fav.city_name;
            updateMapMarker();
            refreshWeatherData();
        });

        // Delete button
        btn.querySelector('.delete-fav-btn').addEventListener('click', async (e) => {
            e.stopPropagation();
            try {
                const delRes = await fetch(`/api/v1/locations/favorites/${fav.id}`, { method: 'DELETE' });
                if (delRes.ok) {
                    await loadFavorites();
                    updateStarStatus();
                }
            } catch (err) {
                console.error("Failed to delete favorite:", err);
            }
        });

        favoritesContainer.appendChild(btn);
    });
}

function updateStarStatus() {
    const isSaved = activeFavorites.some(f => 
        Math.abs(f.latitude - currentCoords.lat) < 0.05 && 
        Math.abs(f.longitude - currentCoords.lon) < 0.05
    );
    starBtn.innerHTML = isSaved 
        ? '<i class="fa-solid fa-star text-amber-400"></i>' 
        : '<i class="fa-regular fa-star text-slate-400 hover:text-amber-400"></i>';
}

async function toggleFavorite() {
    const isSaved = activeFavorites.find(f => 
        Math.abs(f.latitude - currentCoords.lat) < 0.05 && 
        Math.abs(f.longitude - currentCoords.lon) < 0.05
    );

    if (isSaved) {
        try {
            const delRes = await fetch(`/api/v1/locations/favorites/${isSaved.id}`, { method: 'DELETE' });
            if (delRes.ok) {
                await loadFavorites();
                updateStarStatus();
            }
        } catch (e) {
            console.error("Error removing favorite:", e);
        }
    } else {
        try {
            const payload = {
                city_name: currentCoords.name !== "My Location" ? currentCoords.name : "Saved City",
                country_code: currentCoords.country || "IN",
                latitude: currentCoords.lat,
                longitude: currentCoords.lon,
                display_order: activeFavorites.length + 1
            };
            const postRes = await fetch('/api/v1/locations/favorites', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (postRes.ok) {
                await loadFavorites();
                updateStarStatus();
            } else {
                const err = await postRes.json();
                alert(err.detail || "Could not save favorite");
            }
        } catch (e) {
            console.error("Error adding favorite:", e);
        }
    }
}
