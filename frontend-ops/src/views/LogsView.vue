<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';

import { fetchLogs } from '../api/client';
import { MESSAGES } from '../constants/messages';
import { formatDateTime, outcomeLabel } from '../utils/format';

const filters = reactive({ outcome: '', ip: '', username: '' });
const items = ref([]);
const stats = ref({ total: 0, success: 0, failed: 0 });
const loading = ref(false);
const error = ref('');
const page = ref(0);
const limit = 25;
const autoRefresh = ref(true);

let timer = null;
let requestId = 0;

const offset = computed(() => page.value * limit);
const totalPages = computed(() => Math.max(1, Math.ceil(stats.value.total / limit)));
const canPrev = computed(() => page.value > 0);
const canNext = computed(() => page.value + 1 < totalPages.value);
const rangeLabel = computed(() => {
  if (stats.value.total === 0) return '0 eventos';
  const from = offset.value + 1;
  const to = Math.min(offset.value + items.value.length, stats.value.total);
  return `${from}–${to} de ${stats.value.total}`;
});

async function load({ silent = false } = {}) {
  const current = ++requestId;
  if (!silent) loading.value = true;
  error.value = '';
  try {
    const data = await fetchLogs({
      limit,
      offset: offset.value,
      outcome: filters.outcome,
      ip: filters.ip,
      username: filters.username,
    });
    if (current !== requestId) return;
    items.value = data.items;
    stats.value = data.stats;
  } catch (err) {
    if (current === requestId) error.value = err.message;
  } finally {
    if (current === requestId) loading.value = false;
  }
}

function applyFilters() {
  page.value = 0;
  load();
}

function resetFilters() {
  filters.outcome = '';
  filters.ip = '';
  filters.username = '';
  page.value = 0;
  load();
}

function goPrev() {
  if (!canPrev.value) return;
  page.value -= 1;
  load();
}

function goNext() {
  if (!canNext.value) return;
  page.value += 1;
  load();
}

function startTimer() {
  stopTimer();
  if (autoRefresh.value) {
    timer = window.setInterval(() => load({ silent: true }), 5000);
  }
}

function stopTimer() {
  if (timer) {
    window.clearInterval(timer);
    timer = null;
  }
}

watch(autoRefresh, startTimer);
onMounted(() => {
  load();
  startTimer();
});
onBeforeUnmount(stopTimer);
</script>

<template>
  <section class="page">
    <header class="page__header">
      <div>
        <p class="page__eyebrow">US-03 · FRONT-04</p>
        <h2 class="page__title">Logs SSH</h2>
        <p class="page__description">
          Flujo de intentos de acceso parseados por el Servicio 2. Los fallos se
          resaltan en rojo y los accesos exitosos en verde.
        </p>
      </div>
      <div class="page__actions">
        <label class="switch">
          <input v-model="autoRefresh" type="checkbox" />
          <span>Actualización automática</span>
        </label>
        <button type="button" class="btn btn--secondary" :disabled="loading" @click="load()">
          {{ MESSAGES.REFRESH }}
        </button>
      </div>
    </header>

    <div class="stats" aria-label="Resumen de eventos">
      <article class="stat">
        <span class="stat__label">Eventos</span>
        <strong class="stat__value">{{ stats.total }}</strong>
      </article>
      <article class="stat stat--success">
        <span class="stat__label">Éxitos</span>
        <strong class="stat__value">{{ stats.success }}</strong>
      </article>
      <article class="stat stat--failed">
        <span class="stat__label">Fallos</span>
        <strong class="stat__value">{{ stats.failed }}</strong>
      </article>
    </div>

    <form class="filters" @submit.prevent="applyFilters">
      <label class="filters__field">
        <span>Resultado</span>
        <select v-model="filters.outcome">
          <option value="">Todos</option>
          <option value="success">Éxito</option>
          <option value="failed">Fallo</option>
        </select>
      </label>

      <label class="filters__field">
        <span>IP de origen</span>
        <input v-model="filters.ip" type="text" placeholder="203.0.113.42" inputmode="text" />
      </label>

      <label class="filters__field">
        <span>Usuario</span>
        <input v-model="filters.username" type="text" placeholder="root" />
      </label>

      <div class="filters__actions">
        <button type="submit" class="btn btn--primary">Filtrar</button>
        <button type="button" class="btn btn--ghost" @click="resetFilters">Limpiar</button>
      </div>
    </form>

    <div v-if="error" class="alert alert--error" role="alert">{{ error }}</div>

    <div class="table-card">
      <div class="table-card__header">
        <span class="table-card__meta">{{ rangeLabel }}</span>
        <span v-if="loading" class="table-card__loading" role="status">Cargando…</span>
      </div>

      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col">Fecha/Hora</th>
              <th scope="col">IP de origen</th>
              <th scope="col">Usuario</th>
              <th scope="col">Resultado</th>
              <th scope="col">Tipo</th>
              <th scope="col">Puerto</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in items"
              :key="`${item.timestamp}-${item.ip}-${index}`"
              :class="`log-row log-row--${item.outcome}`"
              :title="item.raw_line"
            >
              <td class="mono">{{ formatDateTime(item.timestamp) }}</td>
              <td class="mono">{{ item.ip }}</td>
              <td>{{ item.username || '—' }}</td>
              <td>
                <span :class="`badge badge--${item.outcome}`">
                  {{ outcomeLabel(item.outcome) }}
                </span>
                <span v-if="!item.countable" class="badge badge--muted">auxiliar</span>
              </td>
              <td class="mono">{{ item.event_type }}</td>
              <td class="mono">{{ item.port ?? '—' }}</td>
            </tr>
            <tr v-if="!loading && items.length === 0">
              <td colspan="6" class="empty-state">{{ MESSAGES.LOGS_EMPTY }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="table-card__footer">
        <button type="button" class="btn btn--ghost btn--sm" :disabled="!canPrev" @click="goPrev">
          Anterior
        </button>
        <span class="table-card__page">Página {{ page + 1 }} de {{ totalPages }}</span>
        <button type="button" class="btn btn--ghost btn--sm" :disabled="!canNext" @click="goNext">
          Siguiente
        </button>
      </footer>
    </div>
  </section>
</template>
