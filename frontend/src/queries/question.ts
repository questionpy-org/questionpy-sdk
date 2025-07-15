/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useMutation, useQuery, useQueryCache } from '@pinia/colada'

import type { OptionsFormData, OptionsFormDefinition, OptionsStateResponse, ServerValidationErrors } from '@/types'

import { delete_, get, post } from './fetch'
import QUERY_KEYS from './queryKeys'

/**
 * Get all question states.
 *
 * @returns An query return object.
 */
const useQuestionStatesQuery = () =>
    useQuery({
        key: QUERY_KEYS.question.list(),
        query: () => get<Record<string, OptionsFormData>>('questions'),
    })

/**
 * Get question form data by question ID.
 *
 * @param questionId The ID of the question.
 * @returns An query return object.
 */
const useOptionsFormDataQuery = (questionId: string) =>
    useQuery({
        key: () => QUERY_KEYS.question.stateById(questionId),
        query: () => get<OptionsStateResponse>(`question/${questionId}/state`),
    })

/**
 * Get options form definition.
 *
 * @param questionId The ID of the question.
 * @returns An query return object.
 */
const useOptionsFormDefinitionQuery = (questionId: string) =>
    useQuery({
        key: QUERY_KEYS.question.formDefinitionById(questionId),
        query: () => get<OptionsFormDefinition>(`question/${questionId}`),
    })

/**
 * Post question options form data.
 *
 * @param questionId The ID of the question to update.
 * @returns A mutation return object.
 */
function usePostOptionsFormDataMutation(questionId: string) {
    const { invalidateQueries } = useQueryCache()

    const invalidateKeys = [
        QUERY_KEYS.question.list(),
        QUERY_KEYS.question.stateById(questionId),
        QUERY_KEYS.attempt.byQuestionId(questionId),
    ]

    return useMutation({
        mutation: async (formData: OptionsFormData) =>
            (await post<ServerValidationErrors>(`question/${questionId}/state`, JSON.stringify(formData))) ?? {},
        onSettled: async () => {
            for (const key of invalidateKeys) {
                await invalidateQueries({ key })
            }
        },
    })
}

/**
 * Delete question options form data.
 *
 * @param questionId The ID of the question to delete.
 * @returns A mutation return object.
 */
function useDeleteOptionsFormDataMutation(questionId: string) {
    const { invalidateQueries } = useQueryCache()

    const invalidateKeys = [
        QUERY_KEYS.question.list(),
        QUERY_KEYS.question.stateById(questionId),
        QUERY_KEYS.attempt.byQuestionId(questionId),
    ]

    return useMutation({
        mutation: () => delete_(`question/${questionId}`),
        onSettled: () => {
            for (const key of invalidateKeys) {
                invalidateQueries({ key })
            }
        },
    })
}

export {
    useDeleteOptionsFormDataMutation,
    useOptionsFormDataQuery,
    useOptionsFormDefinitionQuery,
    usePostOptionsFormDataMutation,
    useQuestionStatesQuery,
}
