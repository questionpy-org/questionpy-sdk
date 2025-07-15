/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import type {
    CheckboxElement,
    Condition,
    FormElement,
    GeneratedIdElement,
    GroupElement,
    HiddenElement,
    OptionsFormDefinition,
    RadioGroupElement,
    RepetitionElement,
    SelectElement,
    StaticTextElement,
    TextAreaElement,
    TextInputElement,
} from './OptionsFormDefinition.generated'
import type { OptionsFormData, OptionsStateResponse } from './OptionsStateResponse.generated'

/** Mapping of form element `kind` types to their corresponding value types. */
interface ElementValueMap {
    input: string
    textarea: string
    checkbox: boolean
    radio_group: string
    select: string | string[]
    hidden: string
    id: string
}

/** Utility to look up value type by form element. */
type ElementToValue<T extends FormElement> = T['kind'] extends keyof ElementValueMap
    ? ElementValueMap[T['kind']]
    : never

/** Mapping of input field names to their corresponding server-side validation error messages. */
type ServerValidationErrors = Record<string, string>

/** Form element that can be edited. */
type EditableElement =
    | RadioGroupElement
    | RepetitionElement
    | CheckboxElement
    | SelectElement
    | TextInputElement
    | TextAreaElement

/** Form element that has `elements` property. */
type HasElements = Extract<FormElement, { elements: FormElement[] }>

/** Form element that can have conditions. */
type CanHaveConditions = Extract<FormElement, { disable_if: Condition[]; hide_if: Condition[] }>

/** Form element that can have help. */
type CanHaveHelp = Extract<FormElement, { help: string | null }>

/** Possible primitive and list value types allowed in the options form. */
type OptionsFormValue = OptionsFormData[string]

export type {
    AttemptData,
    AttemptRenderData,
    RenderErrorCollection,
    ScoringCode,
    SectionErrorMap,
    TemplateKwargs,
} from './AttemptRenderData.generated'
export type { ClientQuestionDisplayOptions, DisplayRole } from './ClientQuestionDisplayOptions.generated'
export type { DetailedServerError, ErrorDetails } from './DetailedServerError.generated'
export type { ErrorSectionKey } from './ErrorSectionKey.generated'
export type { Manifest } from './Manifest.generated'
export { assertNever, hasElements, isDetailedServerError, isEditableElement, isObject } from './typeUtils'
export type {
    CanHaveConditions,
    CanHaveHelp,
    CheckboxElement,
    Condition,
    EditableElement,
    ElementToValue,
    FormElement,
    GeneratedIdElement,
    GroupElement,
    HasElements,
    HiddenElement,
    OptionsFormData,
    OptionsFormDefinition,
    OptionsFormValue,
    OptionsStateResponse,
    RadioGroupElement,
    RepetitionElement,
    SelectElement,
    ServerValidationErrors,
    StaticTextElement,
    TextAreaElement,
    TextInputElement,
}
