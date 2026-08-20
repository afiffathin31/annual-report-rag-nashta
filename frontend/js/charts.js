/**
 * Chart.js Integration for Nashta 10 Pillars Radar & 5-Year Trend Visualization
 */

let radarChartInstance = null;
let trendChartInstance = null;

const PILLAR_LABELS = [
  "Managed Service",
  "IT Hybrid Infra",
  "Business App",
  "Cyber Security",
  "Data & AI",
  "Digital Platform",
  "IoT & Edge",
  "Consulting",
  "Cloud Services",
  "Bootcamp"
];

function initRadarChart(canvasId, issuerScores, benchmarkScores) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (radarChartInstance) {
    radarChartInstance.destroy();
  }

  const scores = issuerScores.map(p => p.score);
  const bench = benchmarkScores ? benchmarkScores.map(b => b.overall_industry_avg) : [60, 65, 70, 75, 68, 62, 55, 60, 68, 58];

  radarChartInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: PILLAR_LABELS,
      datasets: [
        {
          label: 'Skor Peluang Emiten',
          data: scores,
          fill: true,
          backgroundColor: 'rgba(6, 182, 212, 0.25)',
          borderColor: '#06b6d4',
          pointBackgroundColor: '#06b6d4',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: '#06b6d4',
          borderWidth: 2,
        },
        {
          label: 'Rata-rata Industri',
          data: bench,
          fill: true,
          backgroundColor: 'rgba(148, 163, 184, 0.1)',
          borderColor: '#64748b',
          pointBackgroundColor: '#64748b',
          pointBorderColor: '#fff',
          borderWidth: 1.5,
          borderDash: [4, 4],
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.08)'
          },
          pointLabels: {
            color: '#94a3b8',
            font: {
              size: 10,
              family: "'Plus Jakarta Sans', sans-serif",
              weight: '600'
            }
          },
          ticks: {
            backdropColor: 'transparent',
            color: '#64748b',
            stepSize: 20,
            font: {
              size: 9
            }
          },
          suggestedMin: 30,
          suggestedMax: 100
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#cbd5e1',
            font: {
              size: 11,
              family: "'Plus Jakarta Sans', sans-serif",
              weight: '500'
            },
            padding: 15
          }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#06b6d4',
          bodyColor: '#f8fafc',
          borderColor: '#3b82f6',
          borderWidth: 1,
          padding: 10,
          boxPadding: 4,
          callbacks: {
            label: function(context) {
              return ` ${context.dataset.label}: ${context.raw} / 100`;
            }
          }
        }
      }
    }
  });
}

function initTrendChart(canvasId, trendData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  const labels = trendData.map(t => t.year.toString());
  const scores = trendData.map(t => t.score);

  trendChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Tingkat Kesiapan & Kebutuhan Solusi IT (2020-2024)',
        data: scores,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        fill: true,
        tension: 0.35,
        borderWidth: 3,
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#fff',
        pointRadius: 5,
        pointHoverRadius: 7
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#94a3b8',
            font: {
              weight: '600'
            }
          }
        },
        y: {
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#64748b'
          },
          suggestedMin: 30,
          suggestedMax: 100
        }
      },
      plugins: {
        legend: {
          display: true,
          labels: {
            color: '#cbd5e1',
            font: {
              size: 11
            }
          }
        },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#34d399',
          bodyColor: '#f8fafc',
          borderColor: '#10b981',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            afterLabel: function(context) {
              const item = trendData[context.dataIndex];
              return item.it_focus ? `Fokus: ${item.it_focus}` : '';
            }
          }
        }
      }
    }
  });
}
