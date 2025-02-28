/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

const conditionValueSchema = z.union([z.string(), z.number().int(), z.boolean()])

const baseConditionSchema = z
    .object({
        kind: z.string(),
        name: z.string(),
    })
    .strict()

const isCheckedSchema = baseConditionSchema.extend({
    kind: z.literal('is_checked'),
})

const isNotCheckedSchema = baseConditionSchema.extend({
    kind: z.literal('is_not_checked'),
})

const equalsSchema = baseConditionSchema.extend({
    kind: z.literal('equals'),
    value: conditionValueSchema,
})

const doesNotEqualSchema = baseConditionSchema.extend({
    kind: z.literal('does_not_equal'),
    value: conditionValueSchema,
})

const inSchema = baseConditionSchema.extend({
    kind: z.literal('in'),
    value: conditionValueSchema.array(),
})

const conditionSchema = z.discriminatedUnion('kind', [
    isCheckedSchema,
    isNotCheckedSchema,
    equalsSchema,
    doesNotEqualSchema,
    inSchema,
])

export { conditionSchema }
