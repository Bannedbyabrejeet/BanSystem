<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { fetchBans, fetchHistory, requestUnban } from '../api/client';
import ConfirmDialog from '../components/ConfirmDialog.vue';
import { MESSAGES } from '../constants/messages';
import {
  actionLabel,
  formatDateTime,
  formatDuration,
  formatRemaining,
  unbanReasonLabel,
} from '../utils/format';

const tab = ref('active');
const activeBans = ref([]);
const history = ref([]);
const historyTotal = ref(0);
const loadingActive = ref(false);
const loadingHistory = ref(false);
const error = ref('');
const success = ref('');
const pendingUnban = ref(null);
const unbanBusy = ref(false);

let timer = null;
let requestId = 0;

const activeCount = computed(() => activeBans.value.length);
const historyCount = computed(() => historyTotal.value);

async function loadActive({ silent = false } = {}) {
  if (!silent) loadingActive.value = true;
  try {
    const data = await fetchBans();
    activeBans.value = data.items;
    error.value = '';
  } catch (err) {
    if (!silent) error.value = err.message;
  } finally {
    if (!silent) loadingActive.value = false;
  }
}

async function loadHistory({ silent = false } = {}) {
  const current = ++requestId;
  if (!silent) loadingHistory.value = true;
  try {
    const data = await fetchHistory({ limit: 50 });
    if (current !== requestId) return;
    history.value = data.items;
    historyTotal.value = data.total;
    error.value = '';
  } catch (err) {
    if (current === requestId && !silent) error.value = err.message;
  } finally {
    if (current === requestId && !silent) loadingHistory.value = false;
  }
}

function refreshCurrent() {
  success.value = '';
  if (tab.value === 'active') loadActive();
  else loadHistory();
}

function askUnban(ip) {
  success.value = '';
  pendingUnban.value = ip;
}

async function confirmUnban() {
  if (!pendingUnban.value) return;
  const ip = pendingUnban.value;
  unbanBusy.value = true;
  error.value = '';
  try {
    const response = await requestUnban(ip);
    success.value = `${MESSAGES.UNBAN_QUEUED} (${response.ip})`;
    pendingUnban.value = null;
    window.setTimeout(() => {
      loadActive({ silent: true });
      loadHistory({ silent: true });
    }, 1800);
  } catch (err) {
    error.value = err.message;
  } finally {
    unbanBusy.value = false;
  }
}

function startTimer() {
  stopTimer();
  timer = window.setInterval(() => {
    if (tab.value === 'active') loadActive({ silent: true });
    else loadHistory({ silent: true });
  }, 5000);
}

function stopTimer() {
  if (timer) {
    window.clearInterval(timer);
    timer = null;
  }
}

watch(tab, () => {
  error.value = '';
  success.value = '';
  if (tab.value === 'active') loadActive();
  else loadHistory();
});

onMounted(() => {
  loadActive();
  loadHistory({ silent: true });
  startTimer();
});
onBeforeUnmount(stopTimer);
</script>

<template>
  <section class="page">
    <header class="page__header">
      <div>
        <p class="page__eyebrow">US-06 · US-07 · FRONT-05</p>
        <h2 class="page__title">IPs y baneos</h2>
        <p class="page__description">
          Sanciones activas e historial completo. El botón “Desbanear” encola la
          remoción inmediata de la regla de UFW y del timeout en Redis.
        </p>
      </div>
      <div class="page__actions">
        <button type="button" class="btn btn--secondary" @click="refreshCurrent">
          {{ MESSAGES.REFRESH }}
        </button>
      </div>
    </header>

    <div v-if="error" class="alert alert--error" role="alert">{{ error }}</div>
    <div v-if="success" class="alert alert--success" role="status">{{ success }}</div>

    <div class="tabs" role="tablist" aria-label="Estado de las IPs">
      <button
        type="button"
        role="tab"
        class="tabs__button"
        :class="{ 'tabs__button--active': tab === 'active' }"
        :aria-selected="tab === 'active'"
        @click="tab = 'active'"
      >
        Baneadas en el momento
        <span class="tabs__count">{{ activeCount }}</span>
      </button>
      <button
        type="button"
        role="tab"
        class="tabs__button"
        :class="{ 'tabs__button--active': tab === 'history' }"
        :aria-selected="tab === 'history'"
        @click="tab = 'history'"
      >
        Historial de baneadas anteriormente
        <span class="tabs__count">{{ historyCount }}</span>
      </button>
    </div>

    <div v-if="tab === 'active'" class="table-card" role="tabpanel">
      <div class="table-card__header">
        <span class="table-card__meta">{{ activeCount }} sanciones activas</span>
        <span v-if="loadingActive" class="table-card__loading" role="status">Cargando…</span>
      </div>

      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col">IP</th>
              <th scope="col">Baneada desde</th>
              <th scope="col">Vence</th>
              <th scope="col">Restante</th>
              <th scope="col">Duración</th>
              <th scope="col">Motivo</th>
              <th scope="col">Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ban in activeBans" :key="ban.ip" class="ban-row">
              <td class="mono">{{ ban.ip }}</td>
              <td>{{ formatDateTime(ban.banned_at) }}</td>
              <td>{{ formatDateTime(ban.expires_at) }}</td>
              <td>
                <span class="badge badge--warning">{{ formatRemaining(ban.expires_at) }}</span>
              </td>
              <td>{{ formatDuration(ban.duration_min) }}</td>
              <td>{{ ban.reason }}</td>
              <td>
                <button type="button" class="btn btn--danger btn--sm" @click="askUnban(ban.ip)">
                  Desbanear
                </button>
              </td>
            </tr>
            <tr v-if="!loadingActive && activeBans.length === 0">
              <td colspan="7" class="empty-state">{{ MESSAGES.BANS_EMPTY }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="table-card" role="tabpanel">
      <div class="table-card__header">
        <span class="table-card__meta">{{ historyTotal }} entradas de historial</span>
        <span v-if="loadingHistory" class="table-card__loading" role="status">Cargando…</span>
      </div>

      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col">IP</th>
              <th scope="col">Acción</th>
              <th scope="col">Baneada desde</th>
              <th scope="col">Desbaneada</th>
              <th scope="col">Duración</th>
              <th scope="col">Motivo</th>
              <th scope="col">Origen del desbaneo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in history" :key="`${entry.ip}-${entry.banned_at}-${index}`">
              <td class="mono">{{ entry.ip }}</td>
              <td>
                <span :class="`badge badge--${entry.action === 'banned' ? 'failed' : 'success'}`">
                  {{ actionLabel(entry.action) }}
                </span>
              </td>
              <td>{{ formatDateTime(entry.banned_at) }}</td>
              <td>{{ formatDateTime(entry.unbanned_at) }}</td>
              <td>{{ formatDuration(entry.duration_min) }}</td>
              <td>{{ entry.reason || '—' }}</td>
              <td>{{ unbanReasonLabel(entry.unban_reason) }}</td>
            </tr>
            <tr v-if="!loadingHistory && history.length === 0">
              <td colspan="7" class="empty-state">{{ MESSAGES.HISTORY_EMPTY }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ConfirmDialog
      :open="Boolean(pendingUnban)"
      title="Desbanear IP"
      :message="`${MESSAGES.UNBAN_CONFIRM}\n${pendingUnban || ''}`"
      confirm-label="Desbanear"
      :busy="unbanBusy"
      @confirm="confirmUnban"
      @cancel="pendingUnban = null"
    />
  </section>
</template>
