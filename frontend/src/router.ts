/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { createRouter, createWebHistory } from 'vue-router'

import useAppStateStore from '@/stores/useAppStateStore'
import AttemptView from '@/views/AttemptView.vue'
import PackageView from '@/views/PackageView.vue'
import QuestionPreviewView from '@/views/QuestionPreviewView.vue'
import QuestionView from '@/views/QuestionView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'package-preview',
            component: PackageView,
            meta: { title: 'Package preview' },
        },
        {
            path: '/question',
            name: 'question',
            component: QuestionView,
            meta: { title: 'Question' },
        },
        {
            path: '/question/preview',
            name: 'question-preview',
            component: QuestionPreviewView,
            meta: { title: 'Question preview' },
        },
        {
            path: '/attempt',
            name: 'attempt',
            component: AttemptView,
            meta: { title: 'Attempt preview' },
        },
        {
            path: '/:pathMatch(.*)*',
            name: 'NotFound',
            redirect: '/',
        },
    ],
})

router.beforeEach((to, from, next) => {
    const store = useAppStateStore()
    store.pageTitle = to.meta.title
    next()
})

export default router
