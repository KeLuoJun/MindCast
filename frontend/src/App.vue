<template>
  <div id="app">
    <header class="app-header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5H8v-5l3.5-3.5V16.5zm5 0h-3v-8.5l3.5 3.5v5z"/>
            </svg>
          </div>
          <div class="logo-text">
            <h1>AI圆桌派</h1>
          </div>
        </router-link>
        <nav class="header-nav">
          <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9,22 9,12 15,12 15,22"/>
            </svg>
            首页
          </router-link>
        </nav>
      </div>
    </header>
    
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <footer class="app-footer">
      <div class="footer-content">
        <div class="footer-brand">
          <span class="brand-text">AI圆桌派</span>
          <p class="footer-desc">多智能体协作生成 · 每日 AI 资讯深度解读</p>
        </div>
        <p class="footer-copyright">© 2026 AI圆桌派 MVP · 基于 LangGraph + MiniMax TTS</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
  /* Primary Colors */
  --color-primary: #6366f1;
  --color-primary-dark: #4f46e5;
  --color-primary-light: #818cf8;
  --color-accent: #a855f7;
  --color-accent-warm: #f59e0b;
  
  /* Light Theme - Soft Gradient Background */
  --color-bg: #f8f9fc;
  --color-bg-gradient: linear-gradient(135deg, #f8f9fc 0%, #f0f4ff 50%, #faf5ff 100%);
  --color-bg-secondary: #ffffff;
  --color-bg-card: #ffffff;
  --color-bg-elevated: #ffffff;
  
  /* Text Colors */
  --color-text: #1e293b;
  --color-text-secondary: #64748b;
  --color-text-muted: #94a3b8;
  
  /* Border */
  --color-border: #e2e8f0;
  --color-border-light: #f1f5f9;
  
  /* Status Colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  
  /* Typography */
  --font-sans: 'Plus Jakarta Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  
  /* Border Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 12px rgba(99, 102, 241, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
  --shadow-lg: 0 12px 32px rgba(99, 102, 241, 0.12), 0 4px 8px rgba(0, 0, 0, 0.04);
  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 400ms ease;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--color-bg);
  background-image: var(--color-bg-gradient);
  background-attachment: fixed;
  color: var(--color-text);
  line-height: 1.6;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Header */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.header-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0.875rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
}

.logo-text h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-link:hover {
  background: var(--color-border-light);
  color: var(--color-text);
}

.nav-link.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  color: var(--color-primary);
}

/* Main */
.app-main {
  flex: 1;
  max-width: 1100px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem;
  width: 100%;
}

/* Footer */
.app-footer {
  background: white;
  border-top: 1px solid var(--color-border);
  padding: 2.5rem 1.5rem 2rem;
}

.footer-content {
  max-width: 1100px;
  margin: 0 auto;
  text-align: center;
}

.footer-brand {
  margin-bottom: 1rem;
}

.brand-text {
  font-weight: 600;
  color: var(--color-text);
}

.footer-desc {
  color: var(--color-text-muted);
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.footer-copyright {
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Selection */
::selection {
  background: rgba(99, 102, 241, 0.2);
  color: var(--color-text);
}
</style>
