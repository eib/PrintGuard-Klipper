<script setup lang="ts">
defineProps<{
  show: boolean
  title: string
  size?: 'sm' | 'md' | 'lg'
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="show" :class="$style.overlay" @click.self="emit('close')">
      <div :class="[$style.modal, $style[size || 'md']]">
        <header :class="$style.header">
          <h3>{{ title }}</h3>
          <button :class="$style.close" @click="emit('close')" aria-label="Close modal">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </header>
        <div :class="$style.body">
          <slot />
        </div>
        <footer v-if="$slots.footer" :class="$style.footer">
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style module>
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal-backdrop);
  backdrop-filter: blur(4px);
  animation: fadeIn var(--transition-base);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background-color: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-2xl);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: modal-in var(--transition-base) ease-out;
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.sm {
  width: 90%;
  max-width: 400px;
}

.md {
  width: 90%;
  max-width: 600px;
}

.lg {
  width: 90%;
  max-width: 900px;
}

.header {
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header h3 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}

.close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  color: var(--text-tertiary);
  background-color: transparent;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close:hover {
  color: var(--text-primary);
  background-color: var(--bg-secondary);
}

.body {
  padding: var(--space-6);
  overflow-y: auto;
}

.footer {
  padding: var(--space-5) var(--space-6);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

/* ============================================
   Mobile Responsive Styles
   ============================================ */

@media (max-width: 768px) {
  .modal {
    width: 95%;
    max-width: none;
    margin: var(--space-4);
    max-height: calc(100vh - var(--space-8));
  }

  .header {
    padding: var(--space-4) var(--space-5);
  }

  .header h3 {
    font-size: var(--font-size-lg);
  }

  .body {
    padding: var(--space-4) var(--space-5);
  }

  .footer {
    padding: var(--space-4) var(--space-5);
    flex-direction: column-reverse;
  }

  .footer button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .modal {
    margin: var(--space-2);
    max-height: calc(100vh - var(--space-4));
    border-radius: var(--radius-xl);
  }

  .header,
  .body,
  .footer {
    padding-left: var(--space-4);
    padding-right: var(--space-4);
  }
}
</style>
