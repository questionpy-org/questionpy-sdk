import path from 'node:path'
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { BootstrapVueNextResolver } from 'bootstrap-vue-next'
import IconsResolve from 'unplugin-icons/resolver'
import Icons from 'unplugin-icons/vite'
import Components from 'unplugin-vue-components/vite'
import VueRouter from 'unplugin-vue-router/vite'
import { defineConfig } from 'vite'
import vueDevTools from 'vite-plugin-vue-devtools'

// Expose Bootstrap utilities and variables for use in SCSS style blocks.
// DO NOT include SCSS that compiles to actual CSS here, as it results in duplicate styles.
const additionalScss = `
@import "bootstrap/scss/functions";
@import "bootstrap/scss/variables";
@import "bootstrap/scss/variables-dark";
@import "bootstrap/scss/maps";
@import "bootstrap/scss/mixins";
@import "bootstrap/scss/utilities";
`

// https://vite.dev/config/
export default defineConfig({
    build: {
        emptyOutDir: true, // Suppress warning when outputting to folder outside of project dir
        outDir: path.resolve(import.meta.dirname, '..', 'questionpy_sdk', 'webserver', 'static'),
    },
    css: {
        preprocessorOptions: {
            scss: {
                additionalData: additionalScss,
                // use sass-embedded
                api: 'modern-compiler',
                // make console readable again
                silenceDeprecations: ['color-functions', 'global-builtin', 'import', 'mixed-decls'],
            },
        },
    },
    plugins: [
        VueRouter(),
        vue(),
        vueDevTools(),
        // Provide unplugin icons as Vue components
        Icons({ compiler: 'vue3' }),
        // Support auto-import of components (`src/components/**/*.vue`, Bootstrap, icons)
        Components({
            dts: true, // Auto-generate a `components.d.ts` file
            resolvers: [BootstrapVueNextResolver(), IconsResolve()],
        }),
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
    },
})
