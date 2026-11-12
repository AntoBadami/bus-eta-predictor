<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { getVehicles, getStops, getEta } from './api'

const DIRECTIONS = [
  { value: 0, label: 'Hacia Harvard Square', dest: 'Harvard Square' },
  { value: 1, label: 'Hacia Nubian Station', dest: 'Nubian Station' },
]
const DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
const STATUS = { STOPPED_AT: 'En una parada', IN_TRANSIT_TO: 'En camino', INCOMING_AT: 'Llegando' }

const direction = ref(0)
const vehicles = ref([])
const stops = ref([])
const stopQuery = ref('')
const selectedVehicle = ref(null)
const selectedStop = ref('')
const result = ref(null)
const error = ref('')
const loadingList = ref(false)
const loadingEta = ref(false)
const asideRef = ref(null)

const destination = computed(() => DIRECTIONS.find((d) => d.value === direction.value).dest)

const filteredStops = computed(() => {
  const q = stopQuery.value.trim().toLowerCase()
  return q ? stops.value.filter((s) => s.stop_name.toLowerCase().includes(q)) : stops.value
})

const eta = computed(() => {
  if (!result.value) return null
  const total = Math.round(result.value.eta_seconds)
  if (total < 60) return { big: total, unit: 's', small: '' }
  return { big: Math.floor(total / 60), unit: 'min', small: `${total % 60} s` }
})

const arrivalClock = computed(() => {
  if (!result.value) return ''
  const t = new Date(Date.now() + result.value.eta_seconds * 1000)
  return t.toLocaleTimeString('es-AR', {
    timeZone: 'America/New_York',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
})

const flow = computed(() => {
  if (!result.value) return 0
  const { current_speed, free_flow_speed } = result.value.trafico
  return free_flow_speed ? Math.min(100, Math.round((current_speed / free_flow_speed) * 100)) : 0
})

const statusText = (s) => STATUS[s] || 'En servicio'
const fmtKm = (km) => (km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(2)} km`)

function weatherText(code) {
  const c = Number(code)
  if (c === 0) return 'Despejado'
  if (c <= 3) return 'Parcialmente nublado'
  if (c <= 48) return 'Niebla'
  if (c <= 57) return 'Llovizna'
  if (c <= 67) return 'Lluvia'
  if (c <= 77) return 'Nieve'
  if (c <= 82) return 'Chubascos'
  if (c <= 86) return 'Chubascos de nieve'
  return 'Tormenta'
}

async function loadDirection() {
  error.value = ''
  result.value = null
  selectedVehicle.value = null
  selectedStop.value = ''
  stopQuery.value = ''
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
    if (!vehicles.value.some((v) => v.id === selectedVehicle.value)) selectedVehicle.value = null
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
    await nextTick()
    if (window.matchMedia('(max-width: 899px)').matches) {
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      asideRef.value?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' })
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loadingEta.value = false
  }
}

onMounted(loadDirection)
</script>

<template>
  <div class="page">
    <svg class="sprite" aria-hidden="true" width="0" height="0">
      <symbol id="i-bus" viewBox="0 0 24 24">
        <rect x="4" y="3" width="16" height="15" rx="3" fill="none" stroke="currentColor" stroke-width="1.8" />
        <path d="M4 11h16" fill="none" stroke="currentColor" stroke-width="1.8" />
        <path d="M7.5 14.8h.01M16.5 14.8h.01" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" />
        <path d="M7.5 18v2.5M16.5 18v2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
      </symbol>
    </svg>

    <header class="top">
      <span class="roundel" aria-hidden="true">1</span>
      <div>
        <h1>Ruta 1: cuánto falta para tu colectivo</h1>
        <p class="lede">
          Estimamos la llegada con la ubicación del colectivo, el clima y el tráfico.
        </p>
      </div>
    </header>

    <div class="layout">
      <section class="planner" aria-label="Elegir colectivo y parada">
        <ol class="steps">
          <li class="step done">
            <h2>Sentido</h2>
            <fieldset class="segmented">
              <legend class="sr-only">Sentido del recorrido</legend>
              <label v-for="d in DIRECTIONS" :key="d.value">
                <input
                  class="sr-only"
                  type="radio"
                  name="direction"
                  :value="d.value"
                  v-model="direction"
                  @change="loadDirection"
                />
                <span>{{ d.label }}</span>
              </label>
            </fieldset>
          </li>

          <li class="step" :class="{ done: selectedVehicle }">
            <div class="step-head">
              <h2>Colectivo</h2>
              <button class="link" type="button" @click="refreshVehicles">Actualizar lista</button>
            </div>
            <p v-if="loadingList" class="hint">Buscando colectivos…</p>
            <p v-else-if="!vehicles.length" class="hint">
              No hay colectivos circulando en este sentido ahora. Probá actualizar la lista en un momento.
            </p>
            <ul v-else class="buses">
              <li v-for="v in vehicles" :key="v.id">
                <button
                  type="button"
                  class="bus"
                  :class="{ on: selectedVehicle === v.id }"
                  :aria-pressed="selectedVehicle === v.id"
                  @click="selectedVehicle = v.id"
                >
                  <svg class="bus-icon" aria-hidden="true"><use href="#i-bus" /></svg>
                  <span class="bus-id">{{ v.label }}</span>
                  <span class="bus-status">{{ statusText(v.current_status) }}</span>
                </button>
              </li>
            </ul>
          </li>

          <li class="step" :class="{ done: selectedStop }">
            <h2>Parada</h2>
            <input
              class="search"
              type="search"
              v-model="stopQuery"
              placeholder="Buscar parada"
              aria-label="Buscar parada"
            />
            <p v-if="!filteredStops.length" class="hint">No hay paradas con ese nombre.</p>
            <ul v-else class="stops">
              <li v-for="s in filteredStops" :key="s.stop_id">
                <button
                  type="button"
                  class="stop"
                  :class="{ on: selectedStop === s.stop_id }"
                  :aria-pressed="selectedStop === s.stop_id"
                  :title="`Parada ${s.stop_id}`"
                  @click="selectedStop = s.stop_id"
                >
                  {{ s.stop_name }}
                </button>
              </li>
            </ul>
          </li>
        </ol>

        <button class="calc" type="button" :disabled="!selectedVehicle || !selectedStop || loadingEta" @click="calculate">
          {{ loadingEta ? 'Calculando…' : 'Calcular llegada' }}
        </button>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
      </section>

      <aside class="aside" ref="asideRef" aria-label="Resultado">
        <div class="board" :aria-busy="loadingEta" aria-live="polite">
          <div class="board-head">
            <span class="roundel roundel-sm" aria-hidden="true">1</span>
            <span class="board-dest">{{ destination }}</span>
          </div>

          <template v-if="result">
            <div class="board-eta" :key="result.eta_seconds">
              <span class="digits">{{ eta.big }}</span>
              <span class="unit">{{ eta.unit }}</span>
              <span v-if="eta.small" class="secs">{{ eta.small }}</span>
            </div>
            <p class="board-line">
              Llega a <strong>{{ result.stop.stop_name }}</strong>
            </p>
            <p class="board-sub">
              Colectivo {{ result.vehicle.label }}. Llegada estimada a las {{ arrivalClock }}, hora de Boston.
            </p>
          </template>

          <template v-else>
            <div class="board-eta idle">
              <span class="digits">––</span>
              <span class="unit">min</span>
            </div>
            <p class="board-sub">
              {{ loadingEta ? 'Calculando…' : 'Elegí un colectivo y una parada para ver la estimación.' }}
            </p>
          </template>
        </div>

        <div v-if="result" class="sheet">
          <h2>Datos usados en el cálculo</h2>
          <div class="facts">
            <section>
              <h3>Clima</h3>
              <dl>
                <div><dt>Estado</dt><dd>{{ weatherText(result.clima.weather_code) }}</dd></div>
                <div><dt>Temperatura</dt><dd>{{ result.clima.temperature_2m }} °C</dd></div>
                <div><dt>Humedad</dt><dd>{{ result.clima.relative_humidity_2m }} %</dd></div>
                <div><dt>Precipitación</dt><dd>{{ result.clima.precipitation }} mm</dd></div>
                <div><dt>Luz</dt><dd>{{ result.clima.is_day ? 'De día' : 'De noche' }}</dd></div>
              </dl>
            </section>

            <section>
              <h3>Tráfico</h3>
              <dl>
                <div><dt>Velocidad actual</dt><dd>{{ result.trafico.current_speed }} km/h</dd></div>
                <div><dt>Velocidad sin tránsito</dt><dd>{{ result.trafico.free_flow_speed }} km/h</dd></div>
                <div><dt>Tiempo del tramo</dt><dd>{{ result.trafico.current_travel_time }} s</dd></div>
                <div><dt>Tiempo sin tránsito</dt><dd>{{ result.trafico.freeflow_travel_time }} s</dd></div>
                <div><dt>Fluidez de la vía</dt><dd>{{ flow }} %</dd></div>
              </dl>
              <div class="meter" role="img" :aria-label="`Fluidez de la vía ${flow} por ciento`">
                <span :style="{ width: flow + '%' }"></span>
              </div>
            </section>

            <section>
              <h3>Horario</h3>
              <dl>
                <div><dt>Hora en Boston</dt><dd>{{ result.horario.hora_boston }}</dd></div>
                <div><dt>Reporte (UTC)</dt><dd>{{ result.horario.timestamp_utc.slice(11, 19) }}</dd></div>
                <div><dt>Día (UTC)</dt><dd>{{ DIAS[result.horario.dia_semana] }}</dd></div>
              </dl>
            </section>

            <section>
              <h3>Recorrido</h3>
              <dl>
                <div><dt>Ya recorrido</dt><dd>{{ fmtKm(result.distancias.distancia_en_traza_km) }}</dd></div>
                <div><dt>Falta hasta la parada</dt><dd>{{ fmtKm(result.distancias.distancia_restante_km) }}</dd></div>
                <div><dt>Desvío de la ruta</dt><dd>{{ Math.round(result.distancias.desvio_traza_m) }} m</dd></div>
                <div><dt>Estado</dt><dd>{{ statusText(result.vehicle.current_status) }}</dd></div>
              </dl>
            </section>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.sprite {
  position: absolute;
}

/* ---------- Encabezado ---------- */
.top {
  display: flex;
  align-items: center;
  gap: 18px;
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 24px 0;
}
.top h1 {
  margin: 0;
  font: 600 clamp(32px, 5vw, 50px) / 1.02 var(--display);
}
.lede {
  margin: 8px 0 0;
  color: var(--muted);
  max-width: 56ch;
}
.roundel {
  flex: none;
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--bus);
  color: var(--ink);
  font: 700 40px/1 var(--display);
}
.roundel-sm {
  width: 44px;
  height: 44px;
  font-size: 28px;
}

/* ---------- Layout ---------- */
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
  gap: 56px;
  align-items: start;
  max-width: 1120px;
  margin: 0 auto;
  padding: 36px 24px 72px;
}
@media (max-width: 899px) {
  .layout {
    grid-template-columns: 1fr;
    gap: 36px;
  }
}

/* ---------- Pasos ---------- */
.steps {
  list-style: none;
  margin: 0;
  padding: 0;
  counter-reset: step;
}
.step {
  position: relative;
  padding: 0 0 32px 56px;
  counter-increment: step;
}
.step::before {
  content: counter(step);
  position: absolute;
  left: 0;
  top: 0;
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 2px solid var(--ink);
  border-radius: 50%;
  background: var(--sheet);
  font: 600 18px/1 var(--display);
}
.step.done::before {
  background: var(--bus);
}
.step::after {
  content: '';
  position: absolute;
  left: 17px;
  top: 44px;
  bottom: 6px;
  width: 2px;
  background: var(--rule);
}
.step:last-child::after {
  display: none;
}
.step h2 {
  margin: 0;
  font: 600 26px/36px var(--display);
}
.step-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.hint {
  margin: 12px 0 0;
  color: var(--muted);
}
.link {
  padding: 4px 0;
  border: 0;
  background: none;
  color: var(--ink);
  font: 600 15px var(--body);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}

/* ---------- Sentido ---------- */
.segmented {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin: 14px 0 0;
  padding: 0;
  border: 2px solid var(--ink);
  border-radius: 8px;
  overflow: hidden;
}
.segmented label {
  position: relative;
  cursor: pointer;
}
.segmented label + label {
  border-left: 2px solid var(--ink);
}
.segmented span {
  display: block;
  padding: 12px 14px;
  background: var(--sheet);
  font-weight: 600;
  text-align: center;
}
.segmented input:checked + span {
  background: var(--ink);
  color: #fff;
}
.segmented input:focus-visible + span {
  outline: 3px solid var(--bus);
  outline-offset: -6px;
}

/* ---------- Colectivos ---------- */
.buses {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(128px, 1fr));
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.bus {
  display: grid;
  grid-template-columns: auto 1fr;
  column-gap: 10px;
  align-items: center;
  width: 100%;
  padding: 10px 12px;
  border: 2px solid var(--rule);
  border-radius: 8px;
  background: var(--sheet);
  color: var(--ink);
  text-align: left;
  cursor: pointer;
}
.bus:hover {
  border-color: var(--ink);
}
.bus.on {
  border-color: var(--ink);
  background: var(--bus);
}
.bus-icon {
  grid-row: span 2;
  width: 28px;
  height: 28px;
}
.bus-id {
  font: 600 21px/1.1 var(--display);
}
.bus-status {
  font-size: 13px;
  line-height: 1.2;
  color: var(--muted);
}
.bus.on .bus-status {
  color: var(--ink);
}

/* ---------- Paradas (diagrama de línea) ---------- */
.search {
  width: 100%;
  margin-top: 12px;
  padding: 10px 12px;
  border: 2px solid var(--rule);
  border-radius: 8px;
  background: var(--sheet);
  color: var(--ink);
}
.stops {
  max-height: 340px;
  margin: 10px 0 0;
  padding: 6px 0;
  overflow-y: auto;
  border: 2px solid var(--rule);
  border-radius: 8px;
  background: var(--sheet);
  list-style: none;
}
.stop {
  position: relative;
  display: block;
  width: 100%;
  padding: 9px 14px 9px 48px;
  border: 0;
  background: none;
  color: var(--ink);
  text-align: left;
  cursor: pointer;
}
.stop::before {
  content: '';
  position: absolute;
  left: 21px;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--ink);
}
.stops li:first-child .stop::before {
  top: 50%;
}
.stops li:last-child .stop::before {
  bottom: 50%;
}
.stops li:only-child .stop::before {
  display: none;
}
.stop::after {
  content: '';
  position: absolute;
  left: 17px;
  top: 50%;
  width: 12px;
  height: 12px;
  margin-top: -6px;
  border: 3px solid var(--ink);
  border-radius: 50%;
  background: var(--sheet);
}
.stop:hover {
  background: #f3f6f8;
}
.stop.on {
  background: rgba(255, 199, 44, 0.22);
  font-weight: 600;
}
.stop.on::after {
  left: 14px;
  width: 18px;
  height: 18px;
  margin-top: -9px;
  background: var(--bus);
}

/* ---------- Botón y errores ---------- */
.calc {
  width: calc(100% - 56px);
  margin: 4px 0 0 56px;
  padding: 0 20px;
  height: 52px;
  border: 2px solid var(--ink);
  border-radius: 8px;
  background: var(--bus);
  color: var(--ink);
  font: 600 21px var(--display);
  cursor: pointer;
}
.calc:hover:not(:disabled) {
  background: #ffd45e;
}
.calc:disabled {
  border-color: var(--rule);
  background: #e3e8ed;
  color: var(--muted);
  cursor: not-allowed;
}
.error {
  margin: 14px 0 0 56px;
  padding: 10px 14px;
  border-left: 4px solid var(--danger);
  border-radius: 4px;
  background: #fbedec;
}

/* ---------- Cartel ---------- */
.board {
  padding: 22px 26px 26px;
  border-radius: 12px;
  background: var(--board);
  color: #fff;
}
.board-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 16px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.14);
}
.board-dest {
  font: 600 30px/1 var(--display);
}
.board-eta {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-top: 18px;
  color: var(--bus);
  animation: settle 0.45s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.board-eta.idle {
  color: rgba(255, 199, 44, 0.28);
  animation: none;
}
.digits {
  font: 700 clamp(96px, 16vw, 148px) / 0.9 var(--display);
  font-variant-numeric: tabular-nums;
}
.unit {
  font: 600 36px/1 var(--display);
}
.secs {
  margin-left: 6px;
  color: #c8d6e2;
  font: 600 36px/1 var(--display);
  font-variant-numeric: tabular-nums;
}
.board-line {
  margin: 14px 0 0;
  font-size: 22px;
  line-height: 1.25;
}
.board-line strong {
  font-weight: 600;
}
.board-sub {
  margin: 8px 0 0;
  color: #a9bccb;
}
@keyframes settle {
  from {
    opacity: 0;
    transform: translateY(-14px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .board-eta {
    animation: none;
  }
}

/* ---------- Datos del cálculo ---------- */
.sheet {
  margin-top: 20px;
  padding: 18px 22px 10px;
  border: 2px solid var(--rule);
  border-radius: 8px;
  background: var(--sheet);
}
.sheet h2 {
  margin: 0 0 8px;
  font: 600 24px/1.1 var(--display);
}
.facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  column-gap: 32px;
}
.facts section {
  padding: 10px 0 14px;
}
.facts h3 {
  margin: 0 0 4px;
  font: 600 19px/1.2 var(--display);
}
.facts dl {
  margin: 0;
}
.facts dl div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 5px 0;
  border-bottom: 1px solid var(--rule);
}
.facts dl div:last-child {
  border-bottom: 0;
}
.facts dt {
  color: var(--muted);
}
.facts dd {
  margin: 0;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.meter {
  height: 8px;
  margin: 8px 0 2px;
  overflow: hidden;
  border-radius: 4px;
  background: #e3e8ed;
}
.meter span {
  display: block;
  height: 100%;
  background: var(--ink);
}
</style>