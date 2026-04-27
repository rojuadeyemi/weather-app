var socket = io({
    transports: ['websocket']
});

socket.on('connect', () => {
    navigator.geolocation.getCurrentPosition((pos) => {
        socket.emit('set_location', {
            lat: pos.coords.latitude,
            lon: pos.coords.longitude
        });
    });
});


function setWeatherBackground(symbol) {
    if (!symbol) return;

    const body = document.body;

    body.classList.add("bg-transition"); // add once

    body.classList.remove(
        "bg-clear",
        "bg-cloudy",
        "bg-rain",
        "bg-thunder",
        "bg-night"
    );

    const s = symbol.toLowerCase();

    if (s.includes("clear")) body.classList.add("bg-clear");
    else if (s.includes("cloud")) body.classList.add("bg-cloudy");
    else if (s.includes("rain")) body.classList.add("bg-rain");
    else if (s.includes("thunder")) body.classList.add("bg-thunder");
    else body.classList.add("bg-clear");
}

/* -----------------------------
   Header update (optimized)
----------------------------- */
let currentCondition = "";

function updateHeaderData(data) {
    if (!data) return;

    if (data.header) {
        document.getElementById('header').innerText = data.header ;
    }

    if (data.climatic) {
        currentCondition = data.climatic;  // store ONLY condition
    }
}

//Graph updates
function updateGraphs(graph1, graph2) {
    if (graph1 && graph1.data && graph1.layout) {
        Plotly.react('graph-container-1', graph1.data, graph1.layout);
    }

    if (graph2 && graph2.data && graph2.layout) {
        Plotly.react('graph-container-2', graph2.data, graph2.layout);
    }
}

/* -----------------------------
   Weather icons rendering
----------------------------- */
function updateWeatherIcons(data) {
    var iconsContainer = document.getElementById('icons');
    iconsContainer.innerHTML = '';

    Object.keys(data.icons).forEach(period => {
        var icon = data.icons[period];

        var periodDiv = document.createElement('div');

        var periodName = document.createElement('h3');
        periodName.innerText = `Next ${period}`;
        periodDiv.appendChild(periodName);

        var iconImg = document.createElement('img');
        iconImg.src = `/static/weather-icons/${icon}.svg`;
        iconImg.className = 'weather-icon';
        periodDiv.appendChild(iconImg);

        var forecastDetails = data.forecast[period];

        Object.keys(forecastDetails).forEach(metric => {
            var metricDiv = document.createElement('div');

            var metricName = document.createElement('h4');
            metricName.innerText = metric;

            var metricValue = document.createElement('p');
            metricValue.innerText = forecastDetails[metric];

            metricDiv.appendChild(metricName);
            metricDiv.appendChild(metricValue);
            periodDiv.appendChild(metricDiv);
        });

        iconsContainer.appendChild(periodDiv);
    });
}

/* -----------------------------
   Socket events
----------------------------- */
socket.on('live_update', function (data) {
    if (!data) return;

    // ---- HEADER (only if exists)
    if (data.header || data.climatic) {
        updateHeaderData(data);
    }

    // ---- GRAPHS (only if exists)
    if (data.graph1 && data.graph2) {
        updateGraphs(data.graph1, data.graph2);
    }

    // ---- ICONS (only if exists)
    if (data.icons && data.forecast) {
        updateWeatherIcons(data);
    }

    // ---- BACKGROUND (lightweight)
    if (data.symbol) {
        setWeatherBackground(data.symbol);
    }

    setState("ready");
});

/* -----------------------------
   Smart real-time refresh
----------------------------- */

function setState(state) {
    const el = document.body;

    el.classList.remove("loading", "updating", "ready");

    el.classList.add(state);
}

/* -----------------------------
   Live clock (UI feels real-time)
----------------------------- */
function formatTime(now) {
    const weekday = now.toLocaleString('en-US', { weekday: 'short' });
    const day = now.getDate();

    const time = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });

    return `${weekday} ${day}, ${time}`;
}

function startLiveClock() {
    setInterval(() => {
        const el = document.getElementById('climatic');
        if (!el || !currentCondition) return;

        const now = new Date();
        const formatted = formatTime(now);

        el.innerText = `${currentCondition} • ${formatted}`;
    }, 1000);
}

function initGraphs() {
    Plotly.newPlot('graph-container-1', [], {
        title: "Loading..."
    });

    Plotly.newPlot('graph-container-2', [], {
        title: "Loading..."
    });
}

//Initialize app
document.addEventListener("DOMContentLoaded", () => {
    initGraphs();

    document.getElementById('header').innerText = "Loading...";
    document.getElementById('climatic').innerText = "...";

    startLiveClock();
});
