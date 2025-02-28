/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineQuery, useQuery } from '@pinia/colada'

import { optionsSchema } from '@/schema/options'
import type { Options } from '@/schema/options/types'

import { get } from './fetch'

/** Options form definition query. */
const useOptionsFormDefinition = defineQuery(() =>
    useQuery({
        key: ['options-form-definition'],
        // Explicitly override generic argument as zod is not able to infer the type automatically.
        // See `formElementSchema` for details.
        query: () => get<Options>('options', optionsSchema),
    }),
)

export default useOptionsFormDefinition
