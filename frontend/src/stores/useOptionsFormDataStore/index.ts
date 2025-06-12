/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import { computed } from 'vue'

import { useOptionsFormDataQuery, useOptionsFormDefinitionQuery, usePostOptionsFormDataQuery } from '@/queries/options'

import useFormDataState from './useFormDataState'

/** Provides options form definition and manages form data. */
const useOptionsFormDataStore = defineStore('optionsFormData', () => {
    const { asyncStatus: definitionAsyncStatus, state: definitionState } = useOptionsFormDefinitionQuery()
    const { asyncStatus: dataAsyncStatus, state: dataState } = useOptionsFormDataQuery()
    const { asyncStatus: postDataAsyncStatus, state: mutationState } = usePostOptionsFormDataQuery()

    const asyncStatus = computed(() =>
        [definitionAsyncStatus, dataAsyncStatus, postDataAsyncStatus].some((status) => status.value === 'loading')
            ? 'loading'
            : 'idle',
    )
    const error = computed(() => definitionState.value.error ?? dataState.value.error ?? mutationState.value.error)
    const formDefinition = computed(() => definitionState.value.data)

    return {
        asyncStatus,
        error,
        formDefinition,

        ...useFormDataState(),
    }
})

export default useOptionsFormDataStore
