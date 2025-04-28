/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

const renderErrorCategorySchema = z.enum(['formulation', 'general_feedback', 'specific_feedback', 'right_answer'])

const renderErrorSchema = z
    .object({
        type: z.string().nonempty(),
        line: z.number().nullable(),
        message: z.string().nonempty(),
    })
    .strict()

const attemptStatusSchema = z.enum(['started', 'scored', 'in_progress'])

const scoringCodeSchema = z.enum([
    'AUTOMATICALLY_SCORED',
    'NEEDS_MANUAL_SCORING',
    'RESPONSE_NOT_SCORABLE',
    'INVALID_RESPONSE',
])

/** Represents the serialized attempt data. */
const attemptDataSchema = z
    .object({
        attempt_html: z.string().nonempty(),
        attempt_status: attemptStatusSchema,
        attempt_state: z.string(),
        render_errors: z.record(renderErrorCategorySchema, z.array(renderErrorSchema)),
        variant: z.number(),
        // From ScoreModel
        score: z.number().nullable(),
        scoring_code: scoringCodeSchema.nullable(),
        scoring_state: z.string().nullable(),
    })
    .strict()

type RenderErrorCategory = z.infer<typeof renderErrorCategorySchema>
type RenderError = z.infer<typeof renderErrorSchema>

export { attemptDataSchema }
export type { RenderError, RenderErrorCategory }
