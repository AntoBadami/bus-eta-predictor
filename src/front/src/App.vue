<script setup>
import { ref, onMounted } from 'vue'
import { getVehicles, getStops, getEta } from './api'

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

const direction = ref(0)
const vehicles = ref([])
const stops = ref([])
const selectedVehicle = ref(null)
const selectedStop = ref('')
const result = ref(null)
const error = ref('')
const loadingList = ref(false)
const loadingEta = ref(false)

async function loadDirection() {
  error.value = ''
  result.value = null
  selectedVehicle.value = null
  selectedStop.value = ''
  loadingList.value = true
  try {
    vehicles.value = await getVehicles(direction.value)
    stops.value = await getStops(direction.value)
  } catch (e) {
    error.value = e.message
  } finally {
    loadingList.value = false
  }
}

async function refreshVehicles() {
  try {
    vehicles.value = await getVehicles(direction.value)
  } catch (e) {
    error.value = e.message
  }
}

async function calculate() {
  error.value = ''
  result.value = null
  loadingEta.value = true
  try {
    result.value = await getEta({
      vehicle_id: selectedVehicle.value,
      direction_id: direction.value,
      stop_id: selectedStop.value,
    })
  } catch (e) {
    error.value = e.message
  } finally {
    loadingEta.value = false
  }
}

function formatEta(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m} min ${s} s`
}

onMounted(loadDirection)
</script>

<template>
  <main class="app">
    <h1>🚌 ETA – Ruta 1 (Harvard Square ↔ Nubian Station)</h1>

    <section>
      <h2>1. Sentido</h2>
      <label><input type="radio" :value="0" v-model="direction" @change="loadDirection" /> Sentido 0 (hacia Harvard Square)</label>
      <label><input type="radio" :value="1" v-model="direction" @change="loadDirection" /> Sentido 1 (hacia Nubian Station)</label>
    </section>

    <section>
      <h2>2. Colectivo <button @click="refreshVehicles">Actualizar</button></h2>
      <p v-if="loadingList">Cargando…</p>
      <p v-else-if="!vehicles.length">No hay colectivos circulando en este sentido.</p>
      <ul class="buses">
        <li v-for="v in vehicles" :key="v.id">
          <button :class="{ active: selectedVehicle === v.id }" @click="selectedVehicle = v.id">
            🚌 {{ v.label }}
          </button>
        </li>
      </ul>
    </section>

    <section>
      <h2>3. Parada</h2>
      <select v-model="selectedStop">
        <option value="" disabled>Elegí una parada</option>
        <option v-for="s in stops" :key="s.stop_id" :value="s.stop_id">
          {{ s.stop_sequence }}. {{ s.stop_name }} ({{ s.stop_id }})
        </option>
      </select>
    </section>

    <button class="calc" :disabled="!selectedVehicle || !selectedStop || loadingEta" @click="calculate">
      {{ loadingEta ? 'Calculando…' : 'Calcular ETA' }}
    </button>

    <p v-if="error" class="error">⚠️ {{ error }}</p>

    <section v-if="result" class="result">
      <h2>⏱️ El colectivo {{ result.vehicle.label }} llega en {{ formatEta(result.eta_seconds) }}</h2>
      <p>({{ result.eta_seconds }} segundos) a {{ result.stop.stop_name }}</p>

      <div class="cards">
        <div>
          <h3>Clima</h3>
          <p>Temperatura: {{ result.clima.temperature_2m }} °C</p>
          <p>Precipitación: {{ result.clima.precipitation }} mm</p>
          <p>Humedad: {{ result.clima.relative_humidity_2m }} %</p>
          <p>Código WMO: {{ result.clima.weather_code }}</p>
          <p>{{ result.clima.is_day ? 'De día' : 'De noche' }}</p>
        </div>
        <div>
          <h3>Tráfico</h3>
          <p>Velocidad actual: {{ result.trafico.current_speed }} km/h</p>
          <p>Velocidad libre: {{ result.trafico.free_flow_speed }} km/h</p>
          <p>Tiempo de viaje actual: {{ result.trafico.current_travel_time }} s</p>
          <p>Tiempo libre: {{ result.trafico.freeflow_travel_time }} s</p>
        </div>
        <div>
          <h3>Horario</h3>
          <p>Hora en Boston: {{ result.horario.hora_boston }}</p>
          <p>UTC: {{ result.horario.timestamp_utc }}</p>
          <p>Día: {{ DIAS[result.horario.dia_semana] }}</p>
        </div>
        <div>
          <h3>Recorrido</h3>
          <p>Recorrido en traza: {{ result.distancias.distancia_en_traza_km }} km</p>
          <p>Distancia restante: {{ result.distancias.distancia_restante_km }} km</p>
          <p>Desvío de la traza: {{ result.distancias.desvio_traza_m }} m</p>
          <p>Estado: {{ result.vehicle.current_status }}</p>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.app { max-width: 900px; margin: 0 auto; padding: 1rem; font-family: sans-serif; }
section { margin-bottom: 1.5rem; }
label { margin-right: 1rem; }
.buses { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: .5rem; }
.buses button.active { background: #1a73e8; color: #fff; }
.calc { padding: .6rem 1.2rem; font-size: 1rem; }
.error { color: #c62828; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
.cards > div { border: 1px solid #ccc; border-radius: 8px; padding: .5rem 1rem; }
</style>