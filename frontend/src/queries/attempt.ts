/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineMutation, defineQuery, useMutation, useQuery, useQueryCache } from '@pinia/colada'
import { storeToRefs } from 'pinia'

import { get, post } from '@/queries/fetch'
import useDisplayOptionsStore from '@/stores/useDisplayOptionsStore'
import type { AttemptRenderData } from '@/types'

/** Get attempt data query. */
const useAttemptDataQuery = defineQuery(() => {
    const { displayOptions } = storeToRefs(useDisplayOptionsStore())

    return useQuery({
        key: () => ['attempt-data', displayOptions.value],
        query: () => get<AttemptRenderData>('attempt', displayOptions.value),
    })
})

/** Save attempt query. */
const usePostAttemptQuery = defineMutation(() => {
    const queryCache = useQueryCache()
    return useMutation({
        mutation: (formData: Record<string, unknown>) => post('attempt', JSON.stringify(formData)),
        onSettled: () => queryCache.invalidateQueries({ key: ['attempt-data'] }),
    })
})

/** Restart attempt query. */
const usePostAttemptRestartQuery = defineMutation(() => {
    const queryCache = useQueryCache()
    return useMutation({
        mutation: () => post('attempt/restart'),
        onSettled: () => queryCache.invalidateQueries({ key: ['attempt-data'] }),
    })
})

/** Score attempt query. */
const usePostAttemptScoreQuery = defineMutation(() => {
    const queryCache = useQueryCache()
    return useMutation({
        mutation: () => post('attempt/score'),
        onSettled: () => queryCache.invalidateQueries({ key: ['attempt-data'] }),
    })
})

export { useAttemptDataQuery, usePostAttemptQuery, usePostAttemptRestartQuery, usePostAttemptScoreQuery }
