document.addEventListener("DOMContentLoaded", function () {

    var socket = io("https://mylocation-app.onrender.com", {
        transports: ['websocket', 'polling'],
        reconnection: true
    });

    // Function to request data from the server
    function fetchData() {
        socket.emit('fetch_data');
    }

    function requestUpdateData() {
        socket.emit('request_data');
    }

    // Function to update header information
    function updateHeaderData(data) {
        const climaticEl = document.getElementById('climatic');
        const headerEl = document.getElementById('header');

        if (climaticEl) climaticEl.innerText = data.climatic;
        if (headerEl) headerEl.innerText = data.header;
    }

    // Function to update graphs
    function updateGraphs(graph1, graph2) {
        if (graph1 && graph2) {
            Plotly.react('graph-container-1', graph1.data, graph1.layout);
            Plotly.react('graph-container-2', graph2.data, graph2.layout);
        }
    }

    // Function to update weather icons and details
    function updateWeatherIcons(data) {
        var iconsContainer = document.getElementById('icons');
        if (!iconsContainer) return;

        iconsContainer.innerHTML = '';

        Object.keys(data.icons || {}).forEach(period => {
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

            var forecastDetails = data.forecast?.[period] || {};

            Object.keys(forecastDetails).forEach(metric => {
                var value = forecastDetails[metric];

                var metricDiv = document.createElement('div');
                metricDiv.className = 'weather-metrics';

                var metricName = document.createElement('h4');
                metricName.className = 'metric';
                metricName.innerText = metric;

                var metricValue = document.createElement('p');
                metricValue.className = 'metric-value';
                metricValue.innerText = value;

                metricDiv.appendChild(metricName);
                metricDiv.appendChild(metricValue);
                periodDiv.appendChild(metricDiv);
            });

            iconsContainer.appendChild(periodDiv);
        });
    }

    // Socket events
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

    // Intervals
    setInterval(fetchData, 50000);
    setInterval(requestUpdateData, 600000);

    // Initial load
    fetchData();
    requestUpdateData();

});
