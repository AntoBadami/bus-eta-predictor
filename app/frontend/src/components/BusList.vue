<script setup>
defineProps({
  buses: Array,
  selectedId: String,
  loading: Boolean,
  error: String,
})
defineEmits(['select'])
</script>

<template>
  <section class="panel">
    <h2>Colectivos circulando ({{ buses.length }})</h2>
    <p v-if="loading" class="muted">Cargando…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <p v-else-if="!buses.length" class="muted">No hay colectivos en este sentido.</p>
    <ul v-else class="buses">
      <li
        v-for="b in buses" :key="b.id"
        :class="{ selected: b.id === selectedId }"
        @click="$emit('select', b.id)"
      >
        <span class="icon">🚌</span>
        <strong>{{ b.id }}</strong>
        <small>{{ b.current_status === 'STOPPED_AT' ? 'En parada' : 'En camino' }}</small>
      </li>
    </ul>
  </section>
</template>