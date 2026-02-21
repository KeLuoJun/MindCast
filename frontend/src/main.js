import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Home from './views/Home.vue'
import Episode from './views/Episode.vue'

const routes = [
  { path: '/', component: Home, meta: { keepAlive: true } },
  { path: '/episode/:id', component: Episode, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
