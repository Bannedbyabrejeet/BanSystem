<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: 'Confirmar acción' },
  message: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirmar' },
  busy: { type: Boolean, default: false },
});

defineEmits(['confirm', 'cancel']);
</script>

<template>
  <div v-if="open" class="modal-backdrop" @click.self="$emit('cancel')">
    <section
      class="modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <h2 id="confirm-dialog-title" class="modal__title">{{ title }}</h2>
      <p class="modal__message">{{ message }}</p>
      <div class="modal__actions">
        <button type="button" class="btn btn--ghost" :disabled="busy" @click="$emit('cancel')">
          Cancelar
        </button>
        <button type="button" class="btn btn--danger" :disabled="busy" @click="$emit('confirm')">
          {{ busy ? 'Procesando…' : confirmLabel }}
        </button>
      </div>
    </section>
  </div>
</template>
