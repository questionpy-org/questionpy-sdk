/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import type { BasicColorMode } from '@vueuse/core'

const APP_TITLE = 'QuestionPy SDK'

/** Keeps transient app state (non-persisted) */
const useAppStateStore = defineStore('appState', {
    state: () => ({
        pageTitle: null as string | null,
        colorMode: 'dark' as BasicColorMode,
        currentError: null as Error | null,
    }),
    getters: {
        displayPageTitle: (state) => (state.pageTitle ? `${APP_TITLE} - ${state.pageTitle}` : APP_TITLE),
    },
    actions: {
        setError(error: unknown) {
            if (error instanceof Error) {
                this.currentError = error
            }
        },
        clearError() {
            this.currentError = null
        },
    },
})

export default useAppStateStore
