<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { RouterView } from 'vue-router';

import { ApiError, clearToken, fetchSession, readToken } from './api/client';
import AppShell from './components/AppShell.vue';
import FullScreenLoader from './components/FullScreenLoader.vue';
import LoginRequiredView from './views/LoginRequiredView.vue';

const state = ref('loading');
const admin = ref(null);
const error = ref('');

const adminLoginUrl = import.meta.env.VITE_ADMIN_LOGIN_URL || '/login';
const adminDashboardUrl =
  import.meta.env.VITE_ADMIN_DASHBOARD_URL ||
  adminLoginUrl.replace(/\/login\/?$/, '/dashboard');

async function bootstrap() {
  const token = readToken();
  if (!token) {
    state.value = 'anonymous';
    return;
  }

  try {
    const session = await fetchSession();
    admin.value = session.admin;
    state.value = 'ready';
  } catch (err) {
    if (err instanceof ApiError && err.isUnauthorized) {
      clearToken();
      state.value = 'anonymous';
      return;
    }
    error.value = err.message;
    state.value = 'anonymous';
  }
}

function logout() {
  clearToken();
  window.location.assign(adminLoginUrl);
}

function handleUnauthorized() {
  clearToken();
  state.value = 'anonymous';
}

onMounted(() => {
  window.addEventListener('bba:unauthorized', handleUnauthorized);
  bootstrap();
});
onBeforeUnmount(() => {
  window.removeEventListener('bba:unauthorized', handleUnauthorized);
});
</script>

<template>
  <FullScreenLoader v-if="state === 'loading'" message="Validando sesión…" />
  <LoginRequiredView
    v-else-if="state === 'anonymous'"
    :login-url="adminLoginUrl"
    :error="error"
  />
  <AppShell
    v-else
    :admin="admin"
    :admin-url="adminDashboardUrl"
    @logout="logout"
  >
    <RouterView />
  </AppShell>
</template>
