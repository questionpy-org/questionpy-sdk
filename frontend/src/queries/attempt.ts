/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useMutation, useQuery, useQueryCache } from '@pinia/colada'
import { storeToRefs } from 'pinia'

import useDisplayOptionsStore from '@/stores/useDisplayOptionsStore'
import type { AttemptData, AttemptRenderData } from '@/types'

import { delete_, get, post } from './fetch'
import QUERY_KEYS from './queryKeys'

type InvalidateQueries = ReturnType<typeof useQueryCache>['invalidateQueries']

function makeAttemptInvalidator(questionId: string, attemptId: string, invalidateQueries: InvalidateQueries) {
    return () => {
        invalidateQueries({ key: QUERY_KEYS.attempt.list(questionId) })
        invalidateQueries({ key: QUERY_KEYS.attempt.byId(questionId, attemptId) })
    }
}

/**
 * Get all attempts for a question.
 *
 * @param questionId The ID of the question.
 * @returns An query return object.
 */
const useAttemptListQuery = (questionId: string) =>
    useQuery({
        key: () => QUERY_KEYS.attempt.list(questionId),
        query: () => get<Record<string, AttemptData>>(`question/${questionId}/attempts`),
    })

/**
 * Get a rendered attempt by ID.
 *
 * @remarks Accessing an non-existent attempt creates the attempt server-side.
 *
 * @param questionId The ID of the question.
 * @param attemptId The ID of the attempt.
 * @returns An query return object.
 */
function useAttemptQuery(questionId: string, attemptId: string) {
    const { invalidateQueries } = useQueryCache()
    const { displayOptions } = storeToRefs(useDisplayOptionsStore())

    return useQuery({
        key: () => QUERY_KEYS.attempt.renderedbyId(questionId, attemptId, displayOptions.value),
        query: () =>
            get<AttemptRenderData>(`question/${questionId}/attempt/${attemptId}`, displayOptions.value).then((data) => {
                invalidateQueries({ key: QUERY_KEYS.attempt.list(questionId) })
                return data
            }),
    })
}

/**
 * Delete an attempt.
 *
 * @param questionId The ID of the question the attempt belongs to.
 * @param attemptId The ID of the attempt to delete.
 * @returns A mutation return object.
 */
function useDeleteAttemptMutation(questionId: string, attemptId: string) {
    const { invalidateQueries } = useQueryCache()

    return useMutation({
        mutation: () => delete_(`question/${questionId}/attempt/${attemptId}`),
        onSettled: makeAttemptInvalidator(questionId, attemptId, invalidateQueries),
    })
}

/**
 * Save an attempt state.
 *
 * @param questionId The ID of the question.
 * @param attemptId The ID of the attempt.
 * @returns An mutation return object.
 */
function usePostAttemptMutation(questionId: string, attemptId: string) {
    const { invalidateQueries } = useQueryCache()

    return useMutation({
        mutation: (formData: Record<string, unknown>) =>
            post(`question/${questionId}/attempt/${attemptId}`, JSON.stringify(formData)),
        onSettled: makeAttemptInvalidator(questionId, attemptId, invalidateQueries),
    })
}

/**
 * Score an attempt.
 *
 * @param questionId The ID of the question.
 * @param attemptId The ID of the attempt.
 * @returns An mutation return object.
 */
function usePostAttemptScoreMutation(questionId: string, attemptId: string) {
    const { invalidateQueries } = useQueryCache()

    return useMutation({
        mutation: () => post(`question/${questionId}/attempt/${attemptId}/score`),
        onSettled: makeAttemptInvalidator(questionId, attemptId, invalidateQueries),
    })
}

export {
    useAttemptListQuery,
    useAttemptQuery,
    useDeleteAttemptMutation,
    usePostAttemptMutation,
    usePostAttemptScoreMutation,
}
