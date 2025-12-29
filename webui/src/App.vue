<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from './store/auth'
import { useSystemStore } from './store/system'
import { useTheme } from './composables/useTheme'
import { getSubscription, validateSubscription, unsubscribe } from './services/notifications'
import ConnectionError from './components/shared/ConnectionError.vue'
import NotificationPrompt from './components/shared/NotificationPrompt.vue'
import ThemeToggle from './components/ui/ThemeToggle.vue'
import { Menu, X } from 'lucide-vue-next'

const auth = useAuthStore()
const system = useSystemStore()
const { initTheme } = useTheme()
const mobileMenuOpen = ref(false)
const showNotificationPrompt = ref(false)

initTheme()

async function checkNotifications() {
  if (!auth.isAuthenticated) {
    showNotificationPrompt.value = false
    return
  }

  const sub = await getSubscription()
  const isValid = await validateSubscription(sub)
  
  if (!isValid) {
    if (sub) await unsubscribe()
    showNotificationPrompt.value = true
  } else {
    showNotificationPrompt.value = false
  }
}

watch(() => auth.isAuthenticated, checkNotifications, { immediate: true })

function reload() {
  window.location.reload()
}

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>

<template>
  <div :class="$style.app">
    <template v-if="system.isApiDown">
      <div :class="$style.apiDown">
        <ConnectionError
          title="PrintGuard Offline"
          :message="system.lastError || undefined"
          @retry="reload"
        />
      </div>
    </template>

    <template v-else>
      <nav v-if="auth.isAuthenticated" :class="$style.nav">
        <div :class="$style.container">
          <div :class="$style.logo">PrintGuard</div>

          <!-- Desktop Navigation -->
          <div :class="$style.links">
            <RouterLink to="/" :class="$style.link" active-class="active" @click="closeMobileMenu">Dashboard</RouterLink>
            <RouterLink to="/connections" :class="$style.link" active-class="active" @click="closeMobileMenu">Connections</RouterLink>
            <RouterLink to="/components" :class="$style.link" active-class="active" @click="closeMobileMenu">Components</RouterLink>
            <RouterLink to="/settings" :class="$style.link" active-class="active" @click="closeMobileMenu">Settings</RouterLink>
            <ThemeToggle :class="$style.themeToggle" />
            <button @click="auth.logout()" :class="$style.logout">Logout</button>
          </div>

          <!-- Mobile Menu Toggle -->
          <button
            :class="$style.mobileMenuToggle"
            @click="toggleMobileMenu"
            :aria-expanded="mobileMenuOpen"
            aria-label="Toggle navigation menu"
          >
            <Menu v-if="!mobileMenuOpen" :size="24" />
            <X v-else :size="24" />
          </button>
        </div>

        <!-- Mobile Navigation Menu -->
        <div :class="[$style.mobileMenu, { [$style.mobileMenuOpen]: mobileMenuOpen }]">
          <div :class="$style.mobileMenuContent">
            <RouterLink to="/" :class="$style.mobileLink" active-class="active" @click="closeMobileMenu">Dashboard</RouterLink>
            <RouterLink to="/connections" :class="$style.mobileLink" active-class="active" @click="closeMobileMenu">Connections</RouterLink>
            <RouterLink to="/components" :class="$style.mobileLink" active-class="active" @click="closeMobileMenu">Components</RouterLink>
            <RouterLink to="/settings" :class="$style.mobileLink" active-class="active" @click="closeMobileMenu">Settings</RouterLink>
            <div :class="$style.mobileMenuDivider"></div>
            <div :class="$style.mobileMenuActions">
              <ThemeToggle />
              <button @click="auth.logout()" :class="$style.mobileLogout">Logout</button>
            </div>
          </div>
        </div>
      </nav>

      <main :class="$style.main">
        <div :class="$style.container">
          <RouterView />
        </div>
      </main>
      
      <NotificationPrompt
        :show="showNotificationPrompt"
        @success="showNotificationPrompt = false"
      />
    </template>
  </div>
</template>

<style module>
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.apiDown {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-primary);
}

.nav {
  background-color: var(--card-bg);
  border-bottom: 1px solid var(--border-subtle);
  padding: var(--space-4) 0;
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  box-shadow: var(--shadow-sm);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-6);
  width: 100%;
}

.nav .container {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-extrabold);
  color: var(--primary);
  letter-spacing: var(--letter-spacing-tight);
}

.links {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.link {
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  transition: color var(--transition-fast);
  position: relative;
}

.link:hover {
  color: var(--text-primary);
}

.link :global(.active) {
  color: var(--primary);
}

.link :global(.active)::after {
  content: '';
  position: absolute;
  bottom: calc(-1 * var(--space-5));
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--primary);
  border-radius: var(--radius-full);
}

.themeToggle {
  margin-left: var(--space-2);
}

.logout {
  color: var(--danger);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  margin-left: var(--space-4);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.logout:hover {
  background-color: var(--danger-bg);
}

.main {
  flex: 1;
  padding: var(--space-8) 0;
}

/* ============================================
   Mobile Navigation Styles
   ============================================ */

.mobileMenuToggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: var(--mobile-tap-target);
  height: var(--mobile-tap-target);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.mobileMenuToggle:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.mobileMenu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: var(--card-bg);
  border-bottom: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-dropdown);
  overflow: hidden;
  max-height: 0;
  transition: max-height var(--transition-base) ease-out;
}

.mobileMenuOpen {
  max-height: 500px;
}

.mobileMenuContent {
  display: flex;
  flex-direction: column;
  padding: var(--space-4);
  gap: var(--space-2);
}

.mobileLink {
  padding: var(--space-3) var(--space-4);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-base);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
  text-decoration: none;
}

.mobileLink:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.mobileLink :global(.active) {
  background-color: var(--primary-50);
  color: var(--primary);
}

.mobileMenuDivider {
  height: 1px;
  background-color: var(--border-subtle);
  margin: var(--space-2) 0;
}

.mobileMenuActions {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding-top: var(--space-2);
}

.mobileLogout {
  padding: var(--space-3) var(--space-4);
  color: var(--danger);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-base);
  background: none;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
}

.mobileLogout:hover {
  background-color: var(--danger-bg);
  border-color: var(--danger-200);
}

/* ============================================
   Mobile Responsive Styles
   ============================================ */

@media (max-width: 768px) {
  .links {
    display: none;
  }

  .mobileMenuToggle {
    display: flex;
  }

  .mobileMenu {
    display: block;
  }

  .nav .container {
    position: relative;
  }

  .main {
    padding: var(--space-6) 0;
  }
}
</style>
