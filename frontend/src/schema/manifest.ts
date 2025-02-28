/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

const languageCodeSchema = z.string().length(2, {
    message: 'Must be exactly 2 characters long',
})

/** Represents the fields in a package manifest. */
const manifestSchema = z
    .object({
        short_name: z.string(),
        namespace: z.string(),
        version: z.string(),
        api_version: z.string(),
        author: z.string(),
        name: z.record(languageCodeSchema, z.string()),
        url: z.string().nullable(),
        languages: z.array(languageCodeSchema).nonempty(),
        description: z.record(languageCodeSchema, z.string()),
        icon: z.string().nullable(),
        type: z.enum(['LIBRARY', 'QUESTIONTYPE', 'QUESTION']),
        license: z.string().nullable(),
        tags: z.array(z.string().min(1, { message: 'Must be 1 or more characters long' })),
    })
    .strict()

type Manifest = z.infer<typeof manifestSchema>

export { manifestSchema }
export type { Manifest }
