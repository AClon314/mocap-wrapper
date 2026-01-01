import type { App } from "vue";
// Import global Tailwind CSS so it's included in the app entrypoint.
import "./styles/global.css";
import { createPinia } from "pinia";
import piniaPluginPersistedstate from "pinia-plugin-persistedstate";
// import { vaporInteropPlugin } from "vue";

export default (app: App) => {
  const pinia = createPinia();
  pinia.use(piniaPluginPersistedstate);
  // https://github.com/vuejs/core/blob/minor/CHANGELOG.md#opting-in-to-vapor-mode
  app.use(pinia);
};
