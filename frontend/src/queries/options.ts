/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import {
    defineMutation,
    defineQuery,
    useMutation,
    type UseMutationOptions,
    useQuery,
    useQueryCache,
} from '@pinia/colada'

import { get, post } from '@/queries/fetch'
import type { OptionsFormData, OptionsFormDefinition, ServerValidationErrors } from '@/types'

/** Get options form data query. */
const useOptionsFormDataQuery = defineQuery(() =>
    useQuery({
        key: ['options', 'data'],
        query: () => get<OptionsFormData>('options/state'),
    }),
)

/** Get options form definition query. */
const useOptionsFormDefinitionQuery = defineQuery(() =>
    useQuery({
        key: ['options', 'definition'],
        query: () => get<OptionsFormDefinition>('options'),
    }),
)

type SubscribeCallback = NonNullable<UseMutationOptions<ServerValidationErrors, OptionsFormData>['onSuccess']>

/** Post options form data query. */
const usePostOptionsFormDataQuery = defineMutation(() => {
    const queryCache = useQueryCache()
    const onSuccessSubscribers = new Set<SubscribeCallback>()

    const mutation = useMutation({
        mutation: async (formData: OptionsFormData) =>
            (await post<ServerValidationErrors>('options/state', JSON.stringify(formData))) ?? {},
        onSettled: () => {
            queryCache.invalidateQueries({ key: ['options', 'data'] })
            queryCache.invalidateQueries({ key: ['attempt-data'] })
        },
        onSuccess: (data, vars, context) => {
            for (const cb of onSuccessSubscribers) {
                cb(data, vars, context)
            }
        },
    })

    const onSuccess = (callback: SubscribeCallback) => {
        onSuccessSubscribers.add(callback)
        return () => () => {
            onSuccessSubscribers.delete(callback)
        }
    }

    return { ...mutation, onSuccess }
})

export { useOptionsFormDataQuery, useOptionsFormDefinitionQuery, usePostOptionsFormDataQuery }
