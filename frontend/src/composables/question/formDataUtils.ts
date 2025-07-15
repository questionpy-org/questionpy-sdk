/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { v4 as uuidv4 } from 'uuid'

import { assertNever, hasElements, isEditableElement } from '@/types'
import type { FormElement, OptionsFormData, OptionsFormDefinition } from '@/types'

/**
 * Constructs an element name string from an array of path segments.
 *
 * @param path An array of strings representing the path segments.
 * @returns The constructed element name string.
 *
 * **Example:**
 *
 * ```typescript
 * getElementName(['a', 'b', 'c']);
 * // Output: "a[b][c]"
 * ```
 */
function getElementName(path: string[]): string {
    return `${path.join('][').replace(']', '')}]`
}

/**
 * Constructs the error key from an array of path segments.
 *
 * @param path An array of strings representing the path segments.
 * @returns The constructed error key.
 *
 * **Example:**
 *
 * ```typescript
 * getErrorKey(['general', 'a', '2', 'c']);
 * // Output: "a.1.c"
 * ```
 */
function getErrorKey(path: string[]): string {
    return (
        path
            // Remove 'general' prefix
            .slice(path[0] === 'general' ? 1 : 0)
            // Backend validation uses 0-based index
            .map((part) => (part.match(/\d+/) ? String(Number(part) - 1) : part))
            .join('.')
    )
}

/**
 * Populates a form data object with default values from a list of form elements.
 *
 * Each element's value is assigned to the `data` object using a key derived from the `pathPrefix`.
 *
 * @param data The form data object to be updated with default values.
 * @param elems An array of form elements that is processed recursively.
 * @param pathPrefix An array of strings representing the hierarchical path used to generate keys for the `data` object.
 */
function createFormDataValues(data: OptionsFormData, elems: FormElement[], pathPrefix: string[]): void {
    for (const elem of elems) {
        const path = [...pathPrefix, elem.name]
        const name = getElementName(path)

        // Skip fields that are already populated
        if (Object.keys(data).some((key) => key.startsWith(name))) {
            continue
        }

        switch (elem.kind) {
            case 'checkbox':
                data[name] = elem.selected
                break

            case 'select': {
                if (elem.multiple) {
                    data[name] = []
                    for (const { selected, value } of elem.options) {
                        if (selected) {
                            data[name].push(value)
                        }
                    }
                } else {
                    data[name] = elem.options.find((opt) => opt.selected)?.value ?? elem.options.at(0)?.value ?? ''
                }
                break
            }

            case 'input':
            case 'textarea':
                data[name] = elem.default ?? ''
                break

            case 'radio_group':
                data[name] = elem.options.find((opt) => opt.selected)?.value ?? ''
                break

            case 'hidden':
                data[name] = elem.value
                break

            case 'id':
                data[name] = uuidv4()
                break

            case 'group':
                createFormDataValues(data, elem.elements, path)
                break

            case 'repetition': {
                const count = Math.max(elem.initial_repetitions, elem.minimum_repetitions)
                for (let i = 1; i <= count; ++i) {
                    createFormDataValues(data, elem.elements, [...path, i.toString()])
                }
                break
            }

            case 'static_text':
                // no form data
                break

            default:
                assertNever(elem)
        }
    }
}

/**
 * Extracts default form data from an options form definition.
 *
 * @param options The options form definition.
 * @param initialFormData Prepopulated form data.
 * @returns The default form data.
 */
function getFormData(options: OptionsFormDefinition, initialFormData: OptionsFormData): OptionsFormData {
    const data: OptionsFormData = { ...initialFormData }

    createFormDataValues(data, options.general, ['general'])
    for (const section of options.sections) {
        createFormDataValues(data, section.elements, [section.name])
    }

    return data
}

/**
 * Checks if two objects are identical.
 *
 * Compares two objects of type `Record<string, string | boolean | string[]>` to determine if they have the same keys
 * and corresponding values. For values that are arrays, the order and content are compared.
 *
 * @param d1 The first object to compare.
 * @param d2 The second object to compare.
 * @returns `true` if both objects are identical, `false` otherwise.
 */
function areFormDataObjIdentical(d1: OptionsFormData, d2: OptionsFormData): boolean {
    const keys1 = Object.keys(d1)
    const keys2 = Object.keys(d2)

    if (keys1.length !== keys2.length) {
        return false
    }

    for (const key of keys1) {
        if (!d2.hasOwnProperty(key)) {
            return false
        }

        const val1 = d1[key]
        const val2 = d2[key]

        if (Array.isArray(val1) && Array.isArray(val2)) {
            if (val1.length !== val2.length) {
                return false
            }
            for (let i = 0; i < val1.length; i++) {
                if (val1[i] !== val2[i]) {
                    return false
                }
            }
        } else if (val1 !== val2) {
            return false
        }
    }

    return true
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

export { areFormDataObjIdentical, createFormDataValues, getElementName, getErrorKey, getFormData, hasEditableElements }
