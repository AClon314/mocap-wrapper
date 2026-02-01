import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './style/global.css' // 空文件，引入tailwind编译器
import { globalVibrate } from './components/vibrate'
import i18n from './locale'

const app = createApp(App)

globalVibrate()

app.use(createPinia())
app.use(router)
app.use(i18n)

app.mount('#app')
