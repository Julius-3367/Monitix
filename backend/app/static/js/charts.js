// Chart.js configuration and helpers

// Default chart options
const defaultChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: true,
            position: 'top'
        }
    },
    scales: {
        y: {
            beginAtZero: true
        }
    }
};

// Create time series chart
function createTimeSeriesChart(canvasId, label, data, timestamps, color) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            ...defaultChartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Update chart data
function updateChartData(chart, newData, newLabels) {
    if (!chart) return;
    
    chart.data.labels = newLabels;
    chart.data.datasets[0].data = newData;
    chart.update();
}

// Auto-refresh function
let refreshInterval;

function startAutoRefresh(seconds) {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    refreshInterval = setInterval(() => {
        // Trigger HTMX refresh on elements with auto-refresh
        const elements = document.querySelectorAll('[data-auto-refresh]');
        elements.forEach(el => {
            htmx.trigger(el, 'refresh');
        });
    }, seconds * 1000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Start auto-refresh for dashboard (30 seconds)
    if (document.body.dataset.page === 'dashboard') {
        startAutoRefresh(30);
    }
});
