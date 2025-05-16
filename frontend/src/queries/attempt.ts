/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineMutation, defineQuery, useMutation, useQuery, useQueryCache } from '@pinia/colada'
import { storeToRefs } from 'pinia'

import { get, post } from '@/queries/fetch'
import { attemptDataSchema } from '@/schema/attempt'
import useDisplayOptionsStore from '@/stores/useDisplayOptionsStore'

/** Get attempt data query. */
const useAttemptData = defineQuery(() => {
    const { cacheKey, displayOptions } = storeToRefs(useDisplayOptionsStore())

    return useQuery({
        key: () => ['attempt-data', cacheKey.value],
        query: () =>
            get('attempt', attemptDataSchema, {
                generalFeedback: displayOptions.value.generalFeedback,
                specificFeedback: displayOptions.value.specificFeedback,
                rightAnswer: displayOptions.value.rightAnswer,
                roles: Array.from(displayOptions.value.roles),
            }),
    })
})

/** Save attempt query. */
const usePostAttempt = defineMutation(() => {
    const queryCache = useQueryCache()
    return useMutation({
        mutation: (formData: Record<string, unknown>) => post('attempt', JSON.stringify(formData)),
        onSettled: () => queryCache.invalidateQueries({ key: ['attempt-data'] }),
    })
})

/** Restart attempt query. */
const usePostAttemptRestart = defineMutation(() => {
    const queryCache = useQueryCache()
    return useMutation({
        mutation: () => post('attempt/restart'),
        onSettled: () => queryCache.invalidateQueries({ key: ['attempt-data'] }),
    })
})

/** Score attempt query. */
const usePostAttemptScore = defineMutation(() => {
    const queryCache = useQueryCache()
    return useMutation({
        mutation: () => post('attempt/score'),
        onSettled: () => queryCache.invalidateQueries({ key: ['attempt-data'] }),
    })
})

export { useAttemptData, usePostAttempt, usePostAttemptRestart, usePostAttemptScore }
