<template>
  <div id="app">
    <header class="app-header">
      <router-link to="/" class="logo">
        <h1>🎙️ MindCast · 智想电波</h1>
      </router-link>
      <p class="tagline">多智能体 AI 播客 — 每日 AI 资讯深度解读</p>
    </header>
    <main class="app-main">
      <router-view />
    </main>
    <footer class="app-footer">
      <p>MindCast MVP &copy; 2026</p>
    </footer>
  </div>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f5f5f7;
  color: #1d1d1f;
  line-height: 1.6;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem 2rem;
  text-align: center;
}

.app-header .logo {
  text-decoration: none;
  color: white;
}

.app-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
}

.tagline {
  margin-top: 0.3rem;
  opacity: 0.85;
  font-size: 0.95rem;
}

.app-main {
  max-width: 900px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.app-footer {
  text-align: center;
  padding: 2rem;
  color: #86868b;
  font-size: 0.85rem;
}

a {
  color: #667eea;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
