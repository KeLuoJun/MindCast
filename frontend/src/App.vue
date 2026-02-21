<template>
  <div id="app">
    <header class="app-header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.5 8.5v7l6-3.5z" fill="currentColor" stroke="none"/>
            </svg>
          </div>
          <div class="logo-text">
            <span class="logo-name">圆桌派</span>
            <span class="logo-sub">ROUNDTABLE</span>
          </div>
        </router-link>
        <nav class="header-nav">
          <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9,22 9,12 15,12 15,22"/>
            </svg>
            工作台
          </router-link>
          <button class="nav-settings-btn" @click="settingsPanelOpen = true" title="系统配置">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
            </svg>
          </button>
        </nav>
      </div>
    </header>
    
    <main class="app-main">
      <router-view v-slot="{ Component, route }">
        <keep-alive :include="['Home']">
          <component :is="Component" :key="route.fullPath" />
        </keep-alive>
      </router-view>
    </main>
    
    <footer class="app-footer">
      <div class="footer-content">
        <span class="footer-copyright">© 2026 圆桌派 · LangGraph + MiniMax TTS</span>
      </div>
    </footer>

    <!-- Settings Panel -->
    <SettingsPanel v-model="settingsPanelOpen" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SettingsPanel from './components/SettingsPanel.vue'

const settingsPanelOpen = ref(false)
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
  /* ── Core Palette: Warm Indigo + Amber ── */
  --c-primary: #5b5bd6;
  --c-primary-hover: #4e4ec9;
  --c-primary-soft: rgba(91, 91, 214, 0.08);
  --c-primary-muted: rgba(91, 91, 214, 0.15);
  --c-accent: #e5a23c;
  --c-accent-soft: rgba(229, 162, 60, 0.1);
  --c-success: #18a058;
  --c-error: #d03050;
  --c-warning: #f0a020;

  /* ── Surface system ── */
  --c-bg: #fafbfc;
  --c-bg-warm: #faf8f5;
  --c-surface: #ffffff;
  --c-surface-raised: #ffffff;
  --c-surface-overlay: rgba(255, 255, 255, 0.92);

  /* ── Text ── */
  --c-text-1: #1a1a2e;
  --c-text-2: #5c6370;
  --c-text-3: #9ca3af;
  --c-text-inv: #ffffff;

  /* ── Border ── */
  --c-border: #e8e8ec;
  --c-border-light: #f0f0f3;
  --c-divider: #f5f5f7;

  /* ── Typography ── */
  --font-sans: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-display: 'Noto Sans SC', 'Inter', sans-serif;

  /* ── Radii ── */
  --r-sm: 6px;
  --r-md: 10px;
  --r-lg: 14px;
  --r-xl: 20px;
  --r-full: 9999px;

  /* ── Shadows ── */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.08);
  --shadow-focus: 0 0 0 3px rgba(91, 91, 214, 0.2);

  /* ── Timing ── */
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --dur-fast: 150ms;
  --dur-normal: 250ms;
  --dur-slow: 400ms;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--c-bg);
  color: var(--c-text-1);
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

/* ── Header ── */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--c-surface-overlay);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid var(--c-border);
}

.header-content {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--c-text-1);
}

.logo-icon {
  width: 34px;
  height: 34px;
  background: var(--c-primary);
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.logo-name {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.logo-sub {
  font-size: 0.55rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--c-text-3);
  text-transform: uppercase;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 2px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: var(--r-md);
  color: var(--c-text-2);
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 500;
  transition: all var(--dur-fast) var(--ease);
}

.nav-link:hover {
  background: var(--c-border-light);
  color: var(--c-text-1);
}

.nav-link.active {
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.nav-settings-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: var(--r-md);
  border: none;
  background: transparent;
  color: var(--c-text-3);
  cursor: pointer;
  font-family: inherit;
  transition: all var(--dur-fast) var(--ease);
}

.nav-settings-btn:hover {
  background: var(--c-border-light);
  color: var(--c-text-2);
}

/* ── Main ── */
.app-main {
  flex: 1;
  max-width: 1080px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
  width: 100%;
}

/* ── Footer ── */
.app-footer {
  border-top: 1px solid var(--c-border);
  padding: 1.25rem 1.5rem;
}

.footer-content {
  max-width: 1080px;
  margin: 0 auto;
  text-align: center;
}

.footer-copyright {
  color: var(--c-text-3);
  font-size: 0.75rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

::selection {
  background: rgba(91, 91, 214, 0.15);
}

/* ── Utility classes ── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s var(--ease);
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
