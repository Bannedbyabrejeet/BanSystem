import { createRouter, createWebHistory } from 'vue-router';

import BansView from '../views/BansView.vue';
import LogsView from '../views/LogsView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'logs', component: LogsView },
    { path: '/bans', name: 'bans', component: BansView },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
});

export default router;
