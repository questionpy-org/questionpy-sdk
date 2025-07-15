/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useFormDataState } from '@/composables/question'
import type { FormElement } from '@/types'

import { createFormDataValues, getElementName, getErrorKey } from './formDataUtils'

/**
 * Provides management for form repetitions.
 *
 * @param path The path representing the repetition element.
 * @returns Repetition management methods.
 */
function useRepetitions(path: string[]) {
    const { formData, formErrors } = useFormDataState()

    /**
     * Gets number of repetitions for a repetition element.
     *
     * @returns The number of repetitions.
     */
    function getRepetitionCount(): number {
        // There's no explicit value in the data model, so we need to derive it from the form data.
        const re = new RegExp(`^${RegExp.escape(getElementName(path))}\\[(\\d+)\\]`)
        let highest = 0
        for (const elName of Object.keys(formData.value)) {
            const match = re.exec(elName)
            if (match) {
                highest = Math.max(highest, Number(match[1]))
            }
        }
        return highest
    }

    /**
     * Adds another repetition to a repetition element.
     *
     * @param elements The repetition element's child elements.
     */
    function addRepetition(elements: FormElement[]): void {
        const count = getRepetitionCount() + 1
        createFormDataValues(formData.value, elements, [...path, count.toString()])
    }

    /**
     * Removes a repetition from a repetition element.
     *
     * @param path The path representing the repetition element.
     * @param num The repetition number to be removed.
     */
    function removeRepetition(num: number): void {
        const count = getRepetitionCount()
        const repName = getElementName(path)

        // Delete repetition values...
        let repNameWithNum = `${repName}[${num}]`
        for (const name of Object.keys(formData.value)) {
            if (name.startsWith(repNameWithNum)) {
                delete formData.value[name]
            }
        }

        let errKey = getErrorKey([...path, String(num)])
        for (const key of Object.keys(formErrors.value)) {
            if (key.startsWith(errKey)) {
                delete formErrors.value[key]
            }
        }

        // ...and shift all subsequent by one.
        for (let i = num + 1; i <= count; ++i) {
            repNameWithNum = `${repName}[${i}]`
            for (const [name, value] of Object.entries(formData.value)) {
                if (name.startsWith(repNameWithNum)) {
                    formData.value[name.replace(repNameWithNum, `${repName}[${i - 1}]`)] = value
                    delete formData.value[name]
                }
            }

            errKey = getErrorKey([...path, String(i)])
            for (const [key, value] of Object.entries(formErrors.value)) {
                if (key.startsWith(errKey)) {
                    formErrors.value[key.replace(errKey, getErrorKey([...path, String(i - 1)]))] = value
                    delete formErrors.value[key]
                }
            }
        }
    }

    return { addRepetition, getRepetitionCount, removeRepetition }
}

export default useRepetitions
