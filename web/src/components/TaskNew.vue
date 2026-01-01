<!-- select css https://una.im/select-updates/ -->
<template>
  <MotionConfig :reduced-motion="store?.motion ? 'always' : 'never'">
    <div class="p-6 rounded-2xl border border/5 shadow-xl w-full mx-auto font-sans">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-bold bg-gradient-to-br to-white/60 bg-clip-text text-transparent">
          Configuration
        </h2>
        <div class="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(74,222,128,0.5)]"></div>
      </div>

      <div class="space-y-5">
        <!-- Switch Control -->
        <div class="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
          <Switch></Switch>
          <div class="w-20"></div>
          <SwitchI></SwitchI>
        </div>

        <!-- Premium Select Control -->
        <div class="space-y-2">
          <label class="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Selection Mode</label>
          
          <div class="relative group">
            <select class="premium-select">
              <option value="1">✨ Creative Mode</option>
              <option value="2">🚀 Performance</option>
              <option value="3">🛡️ Safe Mode</option>
              <option value="4" disabled>🔒 Developer (Locked)</option>
            </select>
            
            <!-- Custom Chevron (Decorative, fallback for appearance:none) -->
            <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500 group-hover:text-white transition-colors duration-200">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-down"><path d="m6 9 6 6 6-6"/></svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MotionConfig>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { MotionConfig } from "motion-v";
import { useStore } from "../store/settings";
import Switch from "./Switch.vue";
import SwitchI from "./SwitchI.vue";

const store = ref<ReturnType<typeof useStore>>();

onMounted(() => {
  store.value = useStore();
});
</script>

<style scoped>
/* Base styling for the select functionality */
.premium-select {
  /* Reset default styles */
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  
  width: 100%;
  background-color: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px 16px;
  padding-right: 40px; /* Space for chevron */
  
  color: #e4e4e7; /* zinc-200 */
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  outline: none;
}

/* Hover State */
.premium-select:hover {
  background-color: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transform: translateY(-1px);
}

/* Focus/Active State */
.premium-select:focus {
  border-color: #8b5cf6; /* violet-500 */
  background-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.15);
}

/* Styling the options (Works in some modern browsers / darker themes) */
.premium-select option {
  background-color: #1f1f22;
  color: #e4e4e7;
  padding: 12px;
  font-size: 14px;
}

/* 
  -----------------------------------------------------------------------
   EXPERIMENTAL: "appearance: base-select" 
   (From una.im/select-updates/)
   This requires browser flag support (Chrome 130+ experimental).
  -----------------------------------------------------------------------
*/
@supports (appearance: base-select) {
  .premium-select {
    appearance: base-select;
  }
  
  /* The popup/dropdown container */
  .premium-select::picker(select) {
    background: #18181b;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 12px;
    padding: 6px;
    box-shadow: 
      0 10px 15px -3px rgba(0, 0, 0, 0.5), 
      0 4px 6px -2px rgba(0, 0, 0, 0.3);
    animation: scaleIn 0.15s ease-out;
  }

  /* Each option in the dropdown */
  .premium-select option {
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    display: flex; /* Allow flex inside option if supported */
    align-items: center;
    gap: 8px;
    transition: background 0.1s;
  }

  .premium-select option:hover,
  .premium-select option:checked {
    background-color: #8b5cf6;
    color: white;
  }
  
  .premium-select option:checked::before {
     content: "✓";
     margin-right: 8px;
     font-weight: bold;
  }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>
