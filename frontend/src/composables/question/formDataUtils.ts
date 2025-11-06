/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { v4 as uuidv4 } from 'uuid'

import { assertNever, hasElements, isEditableElement, isObject } from '@/types'
import type {
    ElementPath,
    FormElement,
    OptionsFile,
    OptionsFormData,
    OptionsFormDefinition,
    OptionsFormModelValue,
    OptionsFormValue,
} from '@/types'

/**
 * Constructs the error key from an array of path segments.
 *
 * @param path An array of strings representing the path segments.
 * @returns The constructed error key.
 *
 * @example
 * getErrorKey(['general', 'a', 1, 'c']);
 * // Output: "a.1.c"
 */
function getErrorKey(path: ElementPath): string {
    return (
        path
            // Remove 'general' prefix
            .slice(path[0] === 'general' ? 1 : 0)
            .map((part) => (typeof part === 'number' ? String(part) : part))
            .join('.')
    )
}

/**
 * Populates a form data object with default values from a list of form elements.
 *
 * @param elems An array of form elements that is processed recursively.
 * @param data The form data object to be updated with default values (default: empty object).
 * @return The updated form data.
 */
function createFormDataValues(elems: FormElement[], data: OptionsFormModelValue = {}): OptionsFormData {
    for (const elem of elems) {
        // Skip if already populated
        if (data[elem.name] !== undefined) {
            continue
        }

        switch (elem.kind) {
            case 'checkbox':
                data[elem.name] = elem.selected
                break

            case 'select': {
                if (elem.multiple) {
                    data[elem.name] = elem.options.filter((opt) => opt.selected).map((opt) => opt.value)
                } else {
                    data[elem.name] = elem.options.find((opt) => opt.selected)?.value ?? elem.options[0]?.value ?? ''
                }
                break
            }

            case 'input':
            case 'textarea':
                data[elem.name] = elem.default ?? ''
                break

            case 'radio_group':
                data[elem.name] = elem.options.find((opt) => opt.selected)?.value ?? ''
                break

            case 'hidden':
                data[elem.name] = elem.value
                break

            case 'id':
                data[elem.name] = uuidv4()
                break

            case 'group': {
                data[elem.name] = createFormDataValues(elem.elements)
                break
            }

            case 'repetition': {
                const count = Math.max(elem.initial_repetitions, elem.minimum_repetitions)
                const repetitionData: OptionsFormData[] = []

                for (let i = 0; i < count; ++i) {
                    repetitionData.push(createFormDataValues(elem.elements))
                }

                data[elem.name] = repetitionData
                break
            }

            case 'static_text':
                // no form data
                break

            case 'file_upload':
                data[elem.name] = []
                break

            case 'wysiwyg_editor':
                // TODO: Implement.
                throw new Error('Form element not yet implemented: ' + elem.kind)

            default:
                assertNever(elem)
        }
    }

    return data
}

/**
 * Extracts default form data from an options form definition.
 *
 * @param options The options form definition.
 * @param initialFormData Prepopulated form data.
 * @returns The default form data.
 */
function getFormData(options: OptionsFormDefinition, initialFormData: OptionsFormData): OptionsFormData {
    // General section elements at the root level
    const data = createFormDataValues(options.general, { ...initialFormData })

    // Other sections
    for (const section of options.sections) {
        const sectionElems = (data[section.name] ?? {}) as OptionsFormModelValue
        data[section.name] = createFormDataValues(section.elements, sectionElems)
    }

    return data
}

type FormValue = OptionsFormValue | OptionsFile | null

function areFormValuesIdentical(v1?: FormValue, v2?: FormValue): boolean {
    // Primitive values, null and undefined
    if (v1 === v2) {
        return true
    }

    // Arrays
    if (Array.isArray(v1) && Array.isArray(v2)) {
        if (v1.length !== v2.length) {
            return false
        }
        return v1.every((item, index) => areFormValuesIdentical(item, v2[index]))
    }

    // Objects
    if (isObject(v1) && isObject(v2)) {
        const keys1 = Object.keys(v1)
        const keys2 = Object.keys(v2)

        if (keys1.length !== keys2.length) {
            return false
        }

        return keys1.every(
            // RichTextEditor includes `[k: string]: unknown` which we don't use though
            (key) => keys2.includes(key) && areFormValuesIdentical(v1[key] as FormValue, v2[key] as FormValue),
        )
    }

    // Mismatched types
    return false
}

/**
 * Performs deep equality check between two `OptionsFormData` objects.
 *
 * Recursively compares all properties, including nested objects and arrays. Array/object comparison requires identical
 * length, order, and content.
 *
 * @param d1 First form data object to compare
 * @param d2 Second form data object to compare
 * @returns `true` if objects are deeply equal, `false` otherwise
 */
function areFormDataObjIdentical(d1: OptionsFormData, d2: OptionsFormData): boolean {
    return areFormValuesIdentical(d1, d2)
}

/**
 * Determines if a form element array contains any editable elements.
 *
 * Recursively traverses form elements to check for at least one editable field.
 *
 * @param elements The array of form elements to check.
 * @returns `true` if any editable element exists, `false` otherwise.
 */
function hasEditableElements(elements: FormElement[]): boolean {
    for (const elem of elements) {
        if (isEditableElement(elem) || (hasElements(elem) && hasEditableElements(elem.elements))) {
            return true
        }
    }
    return false
}

export { areFormDataObjIdentical, createFormDataValues, getErrorKey, getFormData, hasEditableElements }
