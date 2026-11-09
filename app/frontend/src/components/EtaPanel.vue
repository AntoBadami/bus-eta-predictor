<script setup>
import { computed } from 'vue'

const props = defineProps({ result: Object, loading: Boolean, error: String })

const eta = computed(() => {
  const s = props.result?.eta_seconds
  if (s == null) return null
  const t = Math.round(s)
  return { seconds: t, text: `${Math.floor(t / 60)} min ${t % 60} s` }
})

const sections = computed(() => {
  const r = props.result
  if (!r) return []
  return [
    { title: '🚌 Colectivo', data: r.bus },
    { title: '📍 Parada', data: r.stop },
    { title: '🛣️ Traza (GTFS)', data: r.trace },
    { title: '🌤️ Clima', data: r.weather },
    { title: '🚦 Tránsito', data: r.traffic },
    { title: '🕒 Horario', data: r.time },
  ]
})
</script>

<template>
  <section class="panel">
    <p v-if="loading" class="muted">Calculando…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <p v-else-if="!result" class="muted">Elegí un colectivo de la lista para estimar su llegada.</p>

    <template v-else>
      <div class="eta" v-if="eta">
        <small>Llegada estimada</small>
        <strong>{{ eta.text }}</strong>
        <small>({{ eta.seconds }} s)</small>
        <small v-if="result.is_mock" class="mock">⚠️ Valor de prueba: todavía no hay modelo conectado</small>
      </div>

      <ul v-if="result.warnings.length" class="warnings">
        <li v-for="w in result.warnings" :key="w">{{ w }}</li>
      </ul>

      <div v-for="s in sections" :key="s.title" class="card">
        <h3>{{ s.title }}</h3>
        <dl v-if="s.data">
          <template v-for="(v, k) in s.data" :key="k">
            <dt>{{ k }}</dt>
            <dd>{{ v ?? '—' }}</dd>
          </template>
        </dl>
        <p v-else class="muted">Sin datos</p>
      </div>

      <details class="card">
        <summary>Features enviadas al modelo</summary>
        <pre>{{ JSON.stringify(result.features, null, 2) }}</pre>
      </details>
    </template>
  </section>
</template>