/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

import { conditionSchema } from './conditions'

const positiveIntSchema = z.number().int().min(0)

const baseElementSchema = z
    .object({
        kind: z.string(),
        name: z.string(),
    })
    .strict()

const labelledSchema = z.object({
    label: z.string(),
})

const canHaveConditionsSchema = z.object({
    disable_if: conditionSchema.array(),
    hide_if: conditionSchema.array(),
})

const canHaveHelpSchema = z.object({
    help: z.string().nullable(),
})

const staticTextElementSchema = baseElementSchema
    .merge(labelledSchema)
    .merge(canHaveConditionsSchema)
    .merge(canHaveHelpSchema)
    .extend({
        kind: z.literal('static_text'),
        text: z.string(),
    })

const textInputElementSchema = baseElementSchema
    .merge(labelledSchema)
    .merge(canHaveConditionsSchema)
    .merge(canHaveHelpSchema)
    .extend({
        kind: z.literal('input'),
        required: z.boolean(),
        default: z.string().nullable(),
        placeholder: z.string().nullable(),
    })

const textAreaElementSchema = baseElementSchema
    .merge(labelledSchema)
    .merge(canHaveConditionsSchema)
    .merge(canHaveHelpSchema)
    .extend({
        kind: z.literal('textarea'),
        required: z.boolean(),
        default: z.string().nullable(),
        placeholder: z.string().nullable(),
    })

const checkboxElementSchema = baseElementSchema
    .merge(canHaveConditionsSchema)
    .merge(canHaveHelpSchema)
    .extend({
        kind: z.literal('checkbox'),
        left_label: z.string().nullable(),
        right_label: z.string().nullable(),
        required: z.boolean(),
        selected: z.boolean(),
    })

const optionSchema = z
    .object({
        label: z.string(),
        value: z.string(),
        selected: z.boolean(),
    })
    .strict()

const radioGroupElementSchema = baseElementSchema
    .merge(labelledSchema)
    .merge(canHaveConditionsSchema)
    .merge(canHaveHelpSchema)
    .extend({
        kind: z.literal('radio_group'),
        options: optionSchema.array(),
        required: z.boolean(),
    })

const selectElementSchema = baseElementSchema
    .merge(labelledSchema)
    .merge(canHaveConditionsSchema)
    .merge(canHaveHelpSchema)
    .extend({
        kind: z.literal('select'),
        multiple: z.boolean(),
        options: optionSchema.array(),
        required: z.boolean(),
    })

const hiddenElementSchema = baseElementSchema.merge(canHaveConditionsSchema).extend({
    kind: z.literal('hidden'),
    value: z.string(),
})

const generatedIdElementSchema = baseElementSchema.extend({
    kind: z.literal('id'),
})

/**
 * Schema for an options form element.
 *
 * @remarks
 *
 * Due to the {@link https://zod.dev/?id=recursive-types|recursive} nature of `formElementSchema`, we must use
 * `z.lazy` and manually specify its type. The ideal type would be:
 *
 * ```ts
 * type FormElementSchemaZodType = z.ZodDiscriminatedUnion<
 *     'kind',
 *     [
 *         z.ZodType<StaticTextElement>,
 *         z.ZodType<TextInputElement>,
 *         // ...
 *     ]
 * >
 * ```
 *
 * However, this is {@link https://github.com/colinhacks/zod/issues/3898|currently not possible in Zod} but will be
 * fixed in version 4. As a workaround, we:
 * 1. Use `ZodType` (which defaults to `any`) to satisfy TypeScript.
 * 2. Define `FormElement` manually.
 * 3. Correct downstream types using a custom `FixElementsType` utility.
 */
const formElementSchema: z.ZodType = z.lazy(() =>
    z.discriminatedUnion('kind', [
        staticTextElementSchema,
        textInputElementSchema,
        textAreaElementSchema,
        checkboxElementSchema,
        radioGroupElementSchema,
        selectElementSchema,
        hiddenElementSchema,
        groupElementSchema,
        repetitionElementSchema,
        generatedIdElementSchema,
    ]),
)

const groupElementSchema = baseElementSchema
    .merge(labelledSchema)
    .merge(canHaveConditionsSchema)
    .merge(canHaveHelpSchema)
    .extend({
        kind: z.literal('group'),
        elements: z.array(formElementSchema),
    })

const repetitionElementSchema = baseElementSchema.extend({
    kind: z.literal('repetition'),
    initial_repetitions: positiveIntSchema,
    minimum_repetitions: positiveIntSchema,
    increment: positiveIntSchema,
    button_label: z.string().nullable(),
    elements: z.array(formElementSchema),
})

export type { canHaveConditionsSchema, canHaveHelpSchema }
export {
    checkboxElementSchema,
    formElementSchema,
    generatedIdElementSchema,
    groupElementSchema,
    hiddenElementSchema,
    radioGroupElementSchema,
    repetitionElementSchema,
    selectElementSchema,
    staticTextElementSchema,
    textAreaElementSchema,
    textInputElementSchema,
}
