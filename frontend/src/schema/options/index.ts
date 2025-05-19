/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

import { formElementSchema } from './elements'

const formSectionSchema = z
    .object({
        name: z.string(),
        header: z.string(),
        elements: formElementSchema.array(),
    })
    .strict()

const optionsSchema = z
    .object({
        general: formElementSchema.array(),
        sections: formSectionSchema.array(),
    })
    .strict()

const optionsFormDataValueSchema = z.union([z.string(), z.boolean(), z.array(z.string()), z.number(), z.null()])
const optionsFormDataSchema = z.record(optionsFormDataValueSchema)

const serverValidationErrorsSchema = z.record(z.string())

export type { optionsFormDataValueSchema }
export { formSectionSchema, optionsFormDataSchema, optionsSchema, serverValidationErrorsSchema }
