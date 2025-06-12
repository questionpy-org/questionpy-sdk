/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { createPinia, setActivePinia } from 'pinia'

import useAppStateStore from '@/stores/useAppStateStore'

beforeEach(() => {
    setActivePinia(createPinia())
})

test('useAppStateStore.displayPageTitle (null pageTitle)', () => {
    const store = useAppStateStore()
    store.pageTitle = null
    expect(store.displayPageTitle).toBe('QuestionPy SDK')
})

test('useAppStateStore.displayPageTitle (set pageTitle)', () => {
    const store = useAppStateStore()
    store.pageTitle = 'Test Page'
    expect(store.displayPageTitle).toBe('QuestionPy SDK - Test Page')
})

test('useAppStateStore.setError (with Error instance)', () => {
    const store = useAppStateStore()
    const error = new Error('Test error')
    store.setError(error)
    expect(store.currentError).toBe(error)
})

test('useAppStateStore.setError (with non-Error instance)', () => {
    const store = useAppStateStore()
    store.setError('Not an error')
    expect(store.currentError).toBeNull()
})

test('useAppStateStore.clearError (resets error)', () => {
    const store = useAppStateStore()
    store.currentError = new Error('Test')
    store.clearError()
    expect(store.currentError).toBeNull()
})
