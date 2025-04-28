/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineMutation, defineQuery, useMutation, useQuery, useQueryCache } from '@pinia/colada'

import { get, post } from '@/queries/fetch'
import { optionsFormDataSchema, optionsSchema } from '@/schema/options'
import type { Options, OptionsFormData } from '@/schema/options/types'

/** Get options form data query. */
const useOptionsFormData = defineQuery(() =>
    useQuery({
        key: ['options', 'data'],
        query: () => get('options/state', optionsFormDataSchema),
    }),
)

/** Get options form definition query. */
const useOptionsFormDefinition = defineQuery(() =>
    useQuery({
        key: ['options', 'definition'],
        // Explicitly override generic argument as zod is not able to infer the type automatically.
        // See `formElementSchema` for details.
        query: () => get<Options>('options', optionsSchema),
    }),
)

/** Post options form data query. */
const usePostOptionsFormData = defineMutation(() => {
    const queryCache = useQueryCache()
    return useMutation({
        mutation: async (formData: OptionsFormData) => (await post('options/state', JSON.stringify(formData))) ?? {},
        onSettled: () => {
            queryCache.invalidateQueries({ key: ['options', 'data'] })
            queryCache.invalidateQueries({ key: ['attempt-data'] })
        },
    })
})

export { useOptionsFormData, useOptionsFormDefinition, usePostOptionsFormData }
