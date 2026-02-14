<template>
  <div id="app">
    <header class="app-header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5H8v-5l3.5-3.5V16.5zm5 0h-3v-8.5l3.5 3.5v5z"/>
            </svg>
          </div>
          <h1>AI圆桌派</h1>
        </router-link>
        <p class="tagline">多智能体 AI 播客 · 每日 AI 资讯深度解读</p>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
    <footer class="app-footer">
      <div class="footer-content">
        <p>AI圆桌派 MVP &copy; 2026</p>
        <p class="footer-links">
          <router-link to="/">首页</router-link>
        </p>
      </div>
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
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  color: #1d1d1f;
  line-height: 1.6;
  min-height: 100vh;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  color: white;
  padding: 1.5rem 2rem;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
  position: relative;
  overflow: hidden;
}

.app-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  border-radius: 50%;
}

.app-header::after {
  content: '';
  position: absolute;
  bottom: -50%;
  left: -10%;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
  border-radius: 50%;
}

.header-content {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.app-header .logo {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: white;
  margin-bottom: 0.5rem;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.app-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.tagline {
  opacity: 0.9;
  font-size: 0.9rem;
  font-weight: 300;
}

.app-main {
  flex: 1;
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1.5rem;
  width: 100%;
}

.app-footer {
  background: white;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e5e7eb;
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.footer-content p {
  color: #6b7280;
  font-size: 0.85rem;
}

.footer-links {
  margin-top: 0.5rem;
}

a {
  color: #6366f1;
  text-decoration: none;
  transition: color 0.2s;
}

a:hover {
  color: #8b5cf6;
  text-decoration: none;
}
</style>
