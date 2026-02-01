/** https://vue-i18n.intlify.dev/guide/advanced/lazy.html#lazy-loading */
import { nextTick } from 'vue'
import { createI18n } from 'vue-i18n'
import zhCN from '@/locale/zh-CN.json'

export const SUPPORT_LOCALES = ['en-US', 'zh-CN'] as const
export type SupportLocales = (typeof SUPPORT_LOCALES)[number]

export function setI18nLang(locale: SupportLocales, I18N = i18n) {
  I18N.global.locale.value = locale // if .value is missing, there would be very strange bug: te('about') return false, but getLocaleMessage('zh-CN').about works
  /**
   * NOTE:
   * If you need to specify the language setting for headers, such as the `fetch` API, set it here.
   * The following is an example for axios.
   *
   * axios.defaults.headers.common['Accept-Language'] = locale
   */
  document.querySelector('html')!.setAttribute('lang', locale)
}

export async function loadI18nJson(locale: SupportLocales, I18N = i18n) {
  locale ??= 'en-US'
  const currentLocale = I18N.global.locale.value
  if (locale === currentLocale) return
  const messages = await import(`./locale/${locale}.json`)
  console.debug('[web] loadI18nJson:', locale, messages.default) // .default is the actual JSON object

  I18N.global.setLocaleMessage(locale, messages.default)

  return nextTick()
}

const i18n = createI18n<[typeof zhCN], SupportLocales, false>({
  legacy: false,
  locale: '', // 故意不加载默认语言，交给router beforeEach
  globalInjection: true,
})
export default i18n
export const t = i18n.global.t
console.debug('[web] i18n init:', i18n)
