<script setup>
import { RouterLink } from 'vue-router';

defineProps({
  admin: { type: Object, default: null },
  adminUrl: { type: String, default: '/dashboard' },
});

defineEmits(['logout']);
</script>

<template>
  <div class="shell">
    <header class="shell__header">
      <div class="shell__brand">
        <span class="brand__shield" aria-hidden="true" />
        <div>
          <p class="shell__eyebrow">Bannedbyabrejeet</p>
          <h1 class="shell__title">Consola operativa</h1>
        </div>
      </div>

      <nav class="shell__nav" aria-label="Secciones de la consola">
        <RouterLink to="/" class="shell__nav-link">Logs SSH</RouterLink>
        <RouterLink to="/bans" class="shell__nav-link">IPs y baneos</RouterLink>
      </nav>

      <div class="shell__session">
        <span class="shell__user">{{ admin?.username || 'administrador' }}</span>
        <a class="shell__admin-link" :href="adminUrl">Panel admin</a>
        <button type="button" class="btn btn--ghost btn--sm" @click="$emit('logout')">
          Salir
        </button>
      </div>
    </header>

    <main class="shell__main">
      <slot />
    </main>
  </div>
</template>
