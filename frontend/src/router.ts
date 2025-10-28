/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { storeToRefs } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { handleHotUpdate, routes } from 'vue-router/auto-routes'

import useAppStateStore from '@/stores/useAppStateStore'
import usePendingOperationsStore from '@/stores/usePendingOperationsStore'

// Catch-all route
routes.push({
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
})

const history = createWebHistory(import.meta.env.BASE_URL)
const router = createRouter({ history, routes })

// Prevent navigation while operations are pending
router.beforeEach(() => {
    const { hasPendingOperations } = storeToRefs(usePendingOperationsStore())
    if (hasPendingOperations.value) {
        return false
    }
})

// Update page title
router.beforeEach((to) => {
    const store = useAppStateStore()
    store.pageTitle = to.meta.title
})

// This will update routes at runtime without reloading the page
if (import.meta.hot) {
    handleHotUpdate(router)
}

export default router
