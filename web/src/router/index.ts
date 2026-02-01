import i18n, { loadI18nJson, setI18nLang, type SupportLocales } from '@/locale'
import { createRouter, createWebHistory } from 'vue-router'

// const views: Record<string, any> = import.meta.glob("../view/**/*.vue");
// function filePathToRoute(file: string) {
//   let name = file.replace("../view/", "").replace(/\.vue$/, "");
//   let path = "/" + name.replace(/\/index$/, "").replace(/^([A-Z])/, (_, c) => c.toLowerCase());
//   name = name.replace(/\//g, "-") || "home";
//   path = path === "/index" ? "/" : path;
//   return {
//     path,
//     name,
//     component: views[file], // lazy component
//   };
// }
// const routes = Object.keys(views).map(filePathToRoute);

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ...routes,
    {
      path: '/task',
      name: 'task',
      component: () => import('@/view/TaskQueue.vue'),
      meta: { title: 'task queue' },
    },
    {
      path: '/setting',
      name: 'setting',
      component: () => import('@/view/Setting.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('@/view/About.vue'),
    },
    { path: '/', redirect: '/task' },
    {
      path: '/:pathMatch(.*)*',
      name: '404',
      component: () => import('@/view/404.vue'),
      meta: { title: 'page not found' },
    },
  ],
})

// Update document.title after navigation using route meta.title
const DEFAULT_TITLE = 'Mocap Wrapper'
router.afterEach((to) => {
  const title = (to.meta as { title?: string }).title
  document.title = title ? `${title} - ${DEFAULT_TITLE}` : DEFAULT_TITLE
})

// navigation guards
router.beforeEach(async (to, from, next) => {
  const lang = (to.query.lang ?? navigator.language) as SupportLocales | undefined
  console.debug('Router beforeEach:', to, i18n.global.availableLocales, lang)
  if (lang) {
    if (!i18n.global.availableLocales.includes(lang)) {
      await loadI18nJson(lang)
    }
    setI18nLang(lang)
  }

  return next()
})

export default router
console.debug('[web] router init', router)
