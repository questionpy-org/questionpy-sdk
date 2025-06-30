import pluginVitest from '@vitest/eslint-plugin'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import eslintPluginSimpleImportSort from 'eslint-plugin-simple-import-sort'
import pluginVue from 'eslint-plugin-vue'

const BASE_NAME = 'qpy-frontend'
const groupWithTypes = (/** @type {string} */ re) => [re, `${re}.*\\u0000$`]

const config = defineConfigWithVueTs(
    {
        name: `${BASE_NAME}/files-to-lint`,
        files: ['**/*.{ts,mts,tsx,vue}'],
    },

    {
        name: `${BASE_NAME}/files-to-ignore`,
        ignores: ['**/dist/**', '**/.vite/**', 'components.d.ts'],
    },

    ...pluginVue.configs['flat/essential'],
    vueTsConfigs.recommended,

    {
        ...pluginVitest.configs.recommended,
        files: ['src/**/__tests__/*'],
    },

    skipFormatting,

    {
        name: `${BASE_NAME}/sort-imports`,
        plugins: {
            'simple-import-sort': eslintPluginSimpleImportSort,
        },
        rules: {
            'simple-import-sort/imports': [
                'error',
                {
                    // https://github.com/lydell/eslint-plugin-simple-import-sort#custom-grouping
                    // custom groups with type imports last in each group
                    groups: [
                        ['^\\u0000'], // side-effects
                        groupWithTypes('^node:'), // node modules
                        groupWithTypes('^[@~]?(?:(?!\\/))\\w'), // 3rd party imports
                        groupWithTypes('^@\\/'), // project imports
                        ['(?<!\\u0000)$'], // absolute imports
                        groupWithTypes('^\\.'), // relative imports
                    ],
                },
            ],
            'simple-import-sort/exports': 'error',
        },
    },

    {
        name: `${BASE_NAME}/custom-overrides`,
        languageOptions: {
            globals: {
                // Ignore macro from Unplugin Vue Router
                definePage: 'readonly',
            },
        },
        rules: {
            // Allow removing keys by destructuring
            '@typescript-eslint/no-unused-vars': [
                'error',
                {
                    ignoreRestSiblings: true,
                },
            ],
        },
    },

    // Follows file based routing naming scheme (https://uvr.esm.is/guide/file-based-routing)
    {
        name: `${BASE_NAME}/unplugin-vue-router`,
        files: ['src/pages/**'],
        rules: { 'vue/multi-word-component-names': 'off' },
    },
)

export default config
