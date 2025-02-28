/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

import type {
    formSectionSchema,
    optionsFormDataSchema,
    optionsFormDataValueSchema,
    serverValidationErrorsSchema,
} from '.'
import type { conditionSchema } from './conditions'
import type {
    canHaveConditionsSchema,
    canHaveHelpSchema,
    checkboxElementSchema,
    formElementSchema, // eslint-disable-line @typescript-eslint/no-unused-vars
    generatedIdElementSchema,
    groupElementSchema,
    hiddenElementSchema,
    radioGroupElementSchema,
    repetitionElementSchema,
    selectElementSchema,
    staticTextElementSchema,
    textAreaElementSchema,
    textInputElementSchema,
} from './elements'

type CanHaveConditions = z.infer<typeof canHaveConditionsSchema>
type CanHaveHelp = z.infer<typeof canHaveHelpSchema>

type Condition = z.infer<typeof conditionSchema>

/**
 * Represents an options form element.
 *
 * @remarks
 * Since this schema is recursive, its type is manually defined (see {@link formElementSchema}).
 */
type FormElement =
    | StaticTextElement
    | TextInputElement
    | TextAreaElement
    | CheckboxElement
    | RadioGroupElement
    | SelectElement
    | HiddenElement
    | GroupElement
    | RepetitionElement
    | GeneratedIdElement

/**
 * Utility type for replacing the `elements` field with another type.
 *
 * @remarks
 * The generic `E` is required to prevent TypeScript from prematurely resolving `FormElement[]`,
 * which would cause a circular reference error.
 *
 * See {@link formElementSchema} for details.
 */
type FixElementsType<T extends Record<string, unknown>, E> = Omit<T, 'elements'> & { elements: E }

type StaticTextElement = z.infer<typeof staticTextElementSchema>
type TextInputElement = z.infer<typeof textInputElementSchema>
type TextAreaElement = z.infer<typeof textAreaElementSchema>
type CheckboxElement = z.infer<typeof checkboxElementSchema>
type RadioGroupElement = z.infer<typeof radioGroupElementSchema>
type SelectElement = z.infer<typeof selectElementSchema>
type HiddenElement = z.infer<typeof hiddenElementSchema>
type GroupElement = FixElementsType<z.infer<typeof groupElementSchema>, FormElement[]>
type RepetitionElement = FixElementsType<z.infer<typeof repetitionElementSchema>, FormElement[]>
type GeneratedIdElement = z.infer<typeof generatedIdElementSchema>

type FormSection = FixElementsType<z.infer<typeof formSectionSchema>, FormElement[]>

interface Options {
    general: FormElement[]
    sections: FormSection[]
}

type OptionsFormDataValue = z.infer<typeof optionsFormDataValueSchema>
type OptionsFormData = z.infer<typeof optionsFormDataSchema>

/** A type that maps the element's `kind` field to the value type */
interface ElementValueMap {
    input: string
    textarea: string
    checkbox: boolean
    radio_group: string
    select: string | string[]
    hidden: string
    id: string
}

/** A utility to Look up value type by form element */
type ElementToValue<T extends FormElement> = T['kind'] extends keyof ElementValueMap
    ? ElementValueMap[T['kind']]
    : never

/** Server-side validation errors */
type ServerValidationErrors = z.infer<typeof serverValidationErrorsSchema>

export type {
    CanHaveConditions,
    CanHaveHelp,
    CheckboxElement,
    Condition,
    ElementToValue,
    FormElement,
    GeneratedIdElement,
    GroupElement,
    HiddenElement,
    Options,
    OptionsFormData,
    OptionsFormDataValue,
    RadioGroupElement,
    RepetitionElement,
    SelectElement,
    ServerValidationErrors,
    StaticTextElement,
    TextAreaElement,
    TextInputElement,
}
