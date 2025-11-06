/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import type { ValidationState } from 'bootstrap-vue-next'

import type {
    CheckboxElement,
    Condition,
    FileUploadElement,
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
import type {
    OptionsFile,
    OptionsFormData,
    OptionsFormModelValue,
    OptionsFormValue,
    OptionsStateResponse,
} from './OptionsStateResponse.generated'

/** Mapping of form element `kind` types to their corresponding value types. */
interface ElementValueMap {
    input: string
    textarea: string
    checkbox: boolean
    radio_group: string
    repetition: OptionsFormModelValue[]
    select: string | string[]
    hidden: string
    id: string
    file_upload: OptionsFile[]
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
    | FileUploadElement

/** Form element that has `elements` property. */
type HasElements = Extract<FormElement, { elements: FormElement[] }>

/** Form element that can have conditions. */
type CanHaveConditions = Extract<FormElement, { disable_if: Condition[]; hide_if: Condition[] }>

/** Form element that can have help. */
type CanHaveHelp = Extract<FormElement, { help: string | null }>

/**
 * An array of strings/integers representing the hierarchical path of a `FormElement`.
 *
 * @example
 * [general', 'my_repetition', 0, 'name', 'first_name']
 */
type ElementPath = (string | number)[]

/** Validation state and text of an options form input. */
interface ValidationInfo {
    /**
     * Validation state.
     *
     * See {@link https://bootstrap-vue-next.github.io/bootstrap-vue-next/docs/components/form-group.html#validation-state-feedback|BootstrapVueNext docs}
     */
    state: ValidationState
    /** Validation feedback text. */
    text: string | undefined
}

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
    ElementPath,
    ElementToValue,
    FileUploadElement,
    FormElement,
    GeneratedIdElement,
    GroupElement,
    HasElements,
    HiddenElement,
    OptionsFile,
    OptionsFormData,
    OptionsFormDefinition,
    OptionsFormModelValue,
    OptionsFormValue,
    OptionsStateResponse,
    RadioGroupElement,
    RepetitionElement,
    SelectElement,
    ServerValidationErrors,
    StaticTextElement,
    TextAreaElement,
    TextInputElement,
    ValidationInfo,
}
