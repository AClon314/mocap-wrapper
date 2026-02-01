import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const __name__ = 'settings'
export const useStore = defineStore(
  __name__,
  () => {
    const prefersReducedMotion =
      typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    console.debug(prefersReducedMotion)
    /** user actual store value, `undefined` for system prefer */
    const _motion = ref<boolean>()
    const motion = computed(() => _motion.value ?? prefersReducedMotion)
    return { _motion, motion }
  },
  {
    persist: true,
  },
)
