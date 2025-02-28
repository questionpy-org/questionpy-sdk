/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineQuery, useQuery } from '@pinia/colada'

import { optionsFormDataSchema } from '@/schema/options'

import { get } from './fetch'

/** Options form data query. */
const useOptionsFormData = defineQuery(() =>
    useQuery({
        key: ['options-form-data'],
        query: () => get('options/state', optionsFormDataSchema),
    }),
)

export default useOptionsFormData
