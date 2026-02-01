import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginPlaywright from 'eslint-plugin-playwright'
import pluginVitest from '@vitest/eslint-plugin'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'
import pluginOxlint from 'eslint-plugin-oxlint'
import globals from 'globals'
import type { Linter } from 'eslint'
type Level = Linter.RuleSeverity
// eslint . --fix --cache
const PROD = process.argv[2] === '.'
const final = PROD ?? false
// console.debug('final', final)
const warn: Level = final ? 'error' : 'warn'
const off: Level = final ? 'warn' : 'off'

const files = ['**/*.{vue,ts,mts,tsx}']
// To allow more languages other than `ts` in `.vue` files, uncomment the following lines:
// import { configureVueProject } from '@vue/eslint-config-typescript'
// configureVueProject({ scriptLangs: ['ts', 'tsx'] })
// More info at https://github.com/vuejs/eslint-config-typescript/#advanced-setup

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files,
  },
  globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**']),
  ...pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,
  {
    ...pluginPlaywright.configs['flat/recommended'],
    files: ['e2e/**/*.{test,spec}.{js,ts,jsx,tsx}'],
  },
  {
    ...pluginVitest.configs.recommended,
    files: ['src/**/__tests__/*'],
  },
  skipFormatting,
  ...pluginOxlint.configs['flat/recommended'],
  {
    files,
    rules: {
      // vite tree-shake will remove unreachable code, so don't worry
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': 'off',

      'vue/multi-word-component-names': [
        'warn',
        {
          ignores: ['index'],
        },
      ],

      complexity: [
        'warn',
        {
          max: 15,
        },
      ],
    },
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
  },
  {
    files: ['./*.config.ts'],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },
)
