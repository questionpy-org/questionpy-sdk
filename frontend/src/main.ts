/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import 'bootstrap/scss/bootstrap.scss'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'
// Poly-fill `Regexp.escape()` (https://caniuse.com/mdn-javascript_builtins_regexp_escape)
import 'core-js/actual/regexp/escape'

import { PiniaColada } from '@pinia/colada'
import { createBootstrap } from 'bootstrap-vue-next'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createBootstrap())
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)
app.use(PiniaColada, {
    queryOptions: {
        refetchOnMount: true,
        refetchOnReconnect: true,
        refetchOnWindowFocus: false,
        staleTime: 30_000,
    },
})
app.use(router)
app.mount('#app')
