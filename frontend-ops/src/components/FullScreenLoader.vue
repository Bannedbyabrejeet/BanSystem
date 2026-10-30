<script setup>
defineProps({
  message: { type: String, default: 'Cargando…' },
});
</script>

<template>
  <div class="loader-page" role="status" aria-live="polite">
    <span class="loader-page__spinner" aria-hidden="true" />
    <p>{{ message }}</p>
  </div>
</template>
