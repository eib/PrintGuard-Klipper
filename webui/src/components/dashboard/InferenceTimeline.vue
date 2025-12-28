<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'
import type { TimelineEntry } from '../../types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps<{
  timelineResults?: TimelineEntry[]
  threshold: number
}>()

const chartData = computed(() => {
  if (!props.timelineResults || props.timelineResults.length === 0) {
    return {
      labels: [],
      datasets: []
    }
  }

  const labels = props.timelineResults.map((entry, index) => {
    const date = new Date(entry.timestamp * 1000)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  })

  const defectData = props.timelineResults.map(entry => {
    if (entry.class_name === 'defect') {
      return (entry.defect_confidence || entry.confidence || 0) * 100
    }
    return null
  })

  const normalData = props.timelineResults.map(entry => {
    if (entry.class_name !== 'defect') {
      return (entry.defect_confidence || 0) * 100
    }
    return null
  })

  const thresholdData = Array(props.timelineResults.length).fill(props.threshold)

  return {
    labels,
    datasets: [
      {
        label: 'Defect Confidence (Active)',
        data: defectData,
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgb(239, 68, 68)',
        borderWidth: 0,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointStyle: 'circle',
        showLine: false,
        spanGaps: false
      },
      {
        label: 'Defect Confidence (Normal State)',
        data: normalData,
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgb(34, 197, 94)',
        borderWidth: 0,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointStyle: 'circle',
        showLine: false,
        spanGaps: false
      },
      {
        label: 'Threshold',
        data: thresholdData,
        borderColor: 'rgb(251, 191, 36)',
        backgroundColor: 'transparent',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 0,
        pointHoverRadius: 0,
        tension: 0,
        fill: false
      }
    ]
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false
  },
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        color: 'rgb(255, 255, 255)',
        usePointStyle: true,
        padding: 15,
        font: {
          size: 11
        }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: 'rgb(255, 255, 255)',
      bodyColor: 'rgb(255, 255, 255)',
      borderColor: 'rgb(255, 255, 255)',
      borderWidth: 1,
      padding: 12,
      displayColors: true,
      callbacks: {
        label: function(context: any) {
          if (context.dataset.label === 'Threshold') {
            return `Threshold: ${context.parsed.y.toFixed(1)}%`
          }
          if (context.parsed.y !== null) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`
          }
          return null
        }
      }
    }
  },
  scales: {
    x: {
      display: true,
      grid: {
        color: 'rgba(255, 255, 255, 0.2)',
        drawBorder: false
      },
      ticks: {
        color: 'rgb(255, 255, 255)',
        maxTicksLimit: 10,
        font: {
          size: 10
        }
      },
      padding: 10
    },
    y: {
      display: true,
      min: 0,
      max: 105,
      grid: {
        color: 'rgba(255, 255, 255, 0.2)',
        drawBorder: false
      },
      ticks: {
        color: 'rgb(255, 255, 255)',
        callback: function(value: any) {
          if (value > 100) return null
          return `${value}%`
        },
        font: {
          size: 10
        }
      }
    }
  }
}))
</script>

<template>
  <div :class="$style.timelineContainer">
    <div v-if="!timelineResults || timelineResults.length === 0" :class="$style.emptyState">
      <p>No inference data available yet</p>
    </div>
    <div v-else :class="$style.chartWrapper">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<style module>
.timelineContainer {
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.85);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
}

.emptyState {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgb(255, 255, 255);
  font-size: var(--font-size-sm);
}

.chartWrapper {
  width: 100%;
  height: 100%;
}
</style>

