<script setup>
import { computed } from 'vue';

import { MESSAGES } from '../constants/messages';

const props = defineProps({
  loginUrl: { type: String, default: '/login' },
  error: { type: String, default: '' },
});

const redirectUrl = computed(() => {
  const current = `${window.location.pathname}${window.location.search}`;
  const separator = props.loginUrl.includes('?') ? '&' : '?';
  return `${props.loginUrl}${separator}redirect=${encodeURIComponent(current)}`;
});
</script>

<template>
  <main class="auth">
    <section class="auth__card">
      <header class="auth__header">
        <div class="brand" aria-hidden="true">
          <span class="brand__shield" />
        </div>
        <h1 class="auth__title">Consola operativa</h1>
        <p class="auth__subtitle">Observabilidad SSH y control de baneos</p>
      </header>

      <div v-if="error" class="alert alert--error" role="alert">{{ error }}</div>
      <p class="login-required__message">{{ MESSAGES.SESSION_REQUIRED }}</p>

      <a class="btn btn--primary login-required__button" :href="redirectUrl">
        Iniciar sesión
      </a>

      <footer class="auth__footer">
        <p>La autenticación se gestiona desde el panel de administración (Frontend A).</p>
      </footer>
    </section>
  </main>
</template>
