<template>
  <div id="app">
    <header class="app-header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <div class="logo-icon">
            <img src="/logo.svg" alt="MindCast Logo" width="24" height="24" />
          </div>
          <div class="logo-text">
            <span class="logo-name">MindCast</span>
            <span class="logo-sub">AI PODCAST GENERATOR</span>
          </div>
        </router-link>
        <nav class="header-nav">
          <a href="/" class="nav-link" :class="{ active: $route.path === '/' }" @click.prevent="goHome">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9,22 9,12 15,12 15,22"/>
            </svg>
            工作台
          </a>
          <button class="nav-settings-btn" @click="settingsPanelOpen = true" title="系统配置">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
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
        <span class="footer-copyright">· 更优质的AI播客创作体验 ·</span>
      </div>
    </footer>

    <!-- Settings Panel -->
    <SettingsPanel v-model="settingsPanelOpen" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from './stores/workflow'
import SettingsPanel from './components/SettingsPanel.vue'

const router = useRouter()
const workflowStore = useWorkflowStore()
const settingsPanelOpen = ref(false)

function goHome() {
  workflowStore.dismissNewEpisode()
  workflowStore.resetWizard()
  if (router.currentRoute.value.path !== '/') {
    router.push('/')
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700;900&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  /* ── Core Palette: Warm & Playful (Figma-inspired) ── */
  --c-primary: #FF6B35;
  --c-primary-hover: #E85D2C;
  --c-primary-soft: rgba(255, 107, 53, 0.1);
  --c-primary-muted: rgba(255, 107, 53, 0.18);
  --c-accent: #4046E3;
  --c-accent-soft: rgba(64, 70, 227, 0.08);
  --c-accent-hover: #3539C0;
  --c-purple: #403285;
  --c-purple-soft: rgba(64, 50, 133, 0.08);
  --c-blue: #01C3FF;
  --c-blue-soft: rgba(1, 195, 255, 0.1);
  --c-yellow: #F1C644;
  --c-yellow-soft: rgba(241, 198, 68, 0.15);
  --c-green: #2ECC71;
  --c-green-soft: rgba(46, 204, 113, 0.1);
  --c-success: #2ECC71;
  --c-error: #E74C3C;
  --c-warning: #F1C644;

  /* ── Surface system: Warm cream tones ── */
  --c-bg: #FFF5ED;
  --c-bg-warm: #FFEEE1;
  --c-bg-card: #FFF9F4;
  --c-surface: #FFFFFF;
  --c-surface-raised: #FFFFFF;
  --c-surface-overlay: rgba(255, 245, 237, 0.92);

  /* ── Text ── */
  --c-text-1: #1A1A2E;
  --c-text-2: #5C6370;
  --c-text-3: #9CA3AF;
  --c-text-inv: #FFFFFF;

  /* ── Border ── */
  --c-border: #F0E0D4;
  --c-border-light: #F7EDE5;
  --c-divider: #F5EDE6;

  /* ── Typography ── */
  --font-sans: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-display: 'Noto Sans SC', 'Inter', sans-serif;

  /* ── Radii (generous, playful) ── */
  --r-sm: 8px;
  --r-md: 14px;
  --r-lg: 20px;
  --r-xl: 28px;
  --r-2xl: 36px;
  --r-full: 9999px;

  /* ── Shadows (warm-toned) ── */
  --shadow-xs: 0 1px 2px rgba(26, 26, 46, 0.03);
  --shadow-sm: 0 2px 8px rgba(26, 26, 46, 0.05);
  --shadow-md: 0 4px 16px rgba(26, 26, 46, 0.06);
  --shadow-lg: 0 8px 32px rgba(26, 26, 46, 0.08);
  --shadow-xl: 0 16px 48px rgba(26, 26, 46, 0.1);
  --shadow-focus: 0 0 0 3px rgba(255, 107, 53, 0.25);
  --shadow-card: 0 2px 12px rgba(26, 26, 46, 0.04), 0 0 0 1px rgba(240, 224, 212, 0.5);

  /* ── Timing ── */
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
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
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid var(--c-border);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: var(--c-text-1);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: var(--c-primary);
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 3px 10px rgba(255, 107, 53, 0.3);
  transition: transform var(--dur-normal) var(--ease-bounce);
}

.logo:hover .logo-icon {
  transform: rotate(-8deg) scale(1.05);
}

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.logo-name {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: var(--c-text-1);
}

.logo-sub {
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: var(--c-primary);
  text-transform: uppercase;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--r-full);
  color: var(--c-text-2);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all var(--dur-fast) var(--ease);
}

.nav-link:hover {
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.nav-link.active {
  background: var(--c-primary);
  color: white;
  box-shadow: 0 2px 8px rgba(255, 107, 53, 0.25);
}

.nav-settings-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--r-full);
  border: none;
  background: transparent;
  color: var(--c-text-3);
  cursor: pointer;
  font-family: inherit;
  transition: all var(--dur-normal) var(--ease);
}

.nav-settings-btn:hover {
  background: var(--c-accent-soft);
  color: var(--c-accent);
  transform: rotate(45deg);
}

/* ── Main ── */
.app-main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
}

/* ── Footer ── */
.app-footer {
  border-top: 1px solid var(--c-border);
  padding: 1.5rem 2rem;
  background: var(--c-bg-warm);
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-copyright {
  color: var(--c-text-3);
  font-size: 0.85rem;
  font-weight: 500;
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
  background: #D4C4B8;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #B8A89C;
}

::selection {
  background: rgba(255, 107, 53, 0.15);
}

/* ── Utility classes ── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s var(--ease);
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .header-content {
    padding: 0 1rem;
  }
  .app-main {
    padding: 1.5rem 1rem;
  }
  .footer-content {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
}
</style>
