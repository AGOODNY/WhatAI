import { createRouter, createWebHistory } from "vue-router";

import HomeView from "../views/HomeView.vue";
import CreateChatView from "../views/CreateChatView.vue";

const routes = [
  {
  path: "/",
  component: HomeView
  },
  {
    path: "/create",
    component: CreateChatView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
