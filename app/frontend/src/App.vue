<script setup>
import { ref, watch, onMounted } from 'vue'
import { getVehicles, getEta } from './api'
import BusList from './components/BusList.vue'
import EtaPanel from './components/EtaPanel.vue'

const DIRECTIONS = [
  { id: 0, label: 'Hacia Harvard Square' },
  { id: 1, label: 'Hacia Nubian Station' },
]

const direction = ref(0)
const buses = ref([])
const loadingBuses = ref(false)
const busesError = ref('')

const selectedId = ref(null)
const result = ref(null)
const loadingEta = ref(false)
const etaError = ref('')

async function loadBuses() {
  loadingBuses.value = true
  busesError.value = ''
  try {
    buses.value = await getVehicles(direction.value)
  } catch (e) {
    busesError.value = e.message
    buses.value = []
  } finally {
    loadingBuses.value = false
  }
}

async function selectBus(id) {
  selectedId.value = id
  result.value = null
  etaError.value = ''
  loadingEta.value = true
  try {
    const data = await getEta(id)
    if (selectedId.value === id) result.value = data
  } catch (e) {
    if (selectedId.value === id) etaError.value = e.message
  } finally {
    if (selectedId.value === id) loadingEta.value = false
  }
}

watch(direction, () => {
  selectedId.value = null
  result.value = null
  etaError.value = ''
  loadBuses()
})
onMounted(loadBuses)
</script>

<template>
  <main>
    <h1>🚌 Ruta 1 · ¿Cuándo llega?</h1>

    <div class="tabs">
      <button
        v-for="d in DIRECTIONS" :key="d.id"
        :class="{ active: direction === d.id }"
        @click="direction = d.id"
      >{{ d.label }}</button>
      <button class="refresh" @click="loadBuses" :disabled="loadingBuses">↻ Actualizar</button>
    </div>

    <div class="layout">
      <BusList
        :buses="buses" :selected-id="selectedId"
        :loading="loadingBuses" :error="busesError"
        @select="selectBus"
      />
      <EtaPanel :result="result" :loading="loadingEta" :error="etaError" />
    </div>
  </main>
</template>