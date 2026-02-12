import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Home from './views/Home.vue'
import Episode from './views/Episode.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/episode/:id', component: Episode, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
