var socket = io();

// Function to request data from the server
function fetchData() {
    socket.emit('fetch_data');
}

function requestUpdateData() {
    socket.emit('request_data');
}

// Function to update header information
function updateHeaderData(data) {
    document.getElementById('climatic').innerText = data.climatic;
    document.getElementById('header').innerText = data.header;
}

// Function to update graphs
function updateGraphs(graph1, graph2) {
    Plotly.react('graph-container-1', graph1.data, graph1.layout);
    Plotly.react('graph-container-2', graph2.data, graph2.layout);
}

// Function to update weather icons and details
function updateWeatherIcons(data) {
    var iconsContainer = document.getElementById('icons');
    iconsContainer.innerHTML = '';  // Clear any existing content

    Object.keys(data.icons).forEach(period => {
        var icon = data.icons[period];
        var periodDiv = document.createElement('div');

        var periodName = document.createElement('h3');
        periodName.innerText = `Next ${period}`;
        periodDiv.appendChild(periodName);

        var iconImg = document.createElement('img');
        iconImg.src = `/static/weather-icons/${icon}.svg`;
        iconImg.className = 'weather-icon';
        iconImg.alt = 'No image';
        periodDiv.appendChild(iconImg);

        var forecastDetails = data.forecast[period];

        Object.keys(forecastDetails).forEach(metric => {
            var value = forecastDetails[metric];
            var metricDiv = document.createElement('div');
            metricDiv.className = 'weather-metrics';

            var metricName = document.createElement('h4');
            metricName.className = 'metric';
            metricName.innerText = metric;
            metricDiv.appendChild(metricName);

            var metricValue = document.createElement('p');
            metricValue.className = 'metric-value';
            metricValue.innerText = value;
            metricDiv.appendChild(metricValue);

            periodDiv.appendChild(metricDiv);
        });

        iconsContainer.appendChild(periodDiv);
    });
}

// Set up event listeners for socket events
socket.on('connect', function () {
    console.log('Connected to server');
});

socket.on('header_data', function (data) {
    updateHeaderData(data);
});

socket.on('update_data', function (data) {
    updateGraphs(data.graph1, data.graph2);
    updateWeatherIcons(data);
});

// Fetch data every 1 minute and 10 minutes
setInterval(fetchData, 50000);
setInterval(requestUpdateData, 600000);

// Fetch data immediately when the page loads
(function initialize() {
    fetchData();
    requestUpdateData();
})();
