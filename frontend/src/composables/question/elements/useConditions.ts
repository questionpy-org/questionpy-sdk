/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { type Ref, ref, watchEffect } from 'vue'

import { useFormDataState } from '@/composables/question'
import { getElementName } from '@/composables/question/formDataUtils'
import { assertNever } from '@/types'
import type { CanHaveConditions, Condition, OptionsFormData } from '@/types'

/**
 * Evaluates whether a given condition is met based on form data and a base path.
 *
 * @param cond The condition to evaluate (see `questionpy.form` Python module for a detailed description).
 * @param basePath The base path used as a starting point for relative references.
 * @param formData The form data object to check against the condition.
 *
 * @returns Returns true if the condition is satisfied, false otherwise.
 */
function isConditionTrue(cond: Condition, basePath: string[], formData: OptionsFormData): boolean {
    const nameParts = cond.name.replace(/\]/g, '').split('[')

    // Resolve condition's target name
    const refPath = [...basePath]
    for (const part of nameParts) {
        if (part === '..') {
            refPath.pop()
        } else {
            refPath.push(part)
        }
    }
    const refValue = formData[getElementName(refPath)]

    if (refValue === undefined) {
        return false
    }

    switch (cond.kind) {
        case 'does_not_equal':
            return refValue !== cond.value

        case 'equals':
            return refValue === cond.value

        case 'in':
            return cond.value.includes(refValue as string | number | boolean)

        case 'is_checked':
            return refValue === true

        case 'is_not_checked':
            return refValue === false

        default:
            assertNever(cond)
    }
}

/**
 * A composable providing support for declarative conditions to options form elements.
 *
 * @param pathPrefix The parent's path of the form element.
 * @param element The form element definition object.
 *
 * @returns An object containing `isDisabledByCond` and `isHiddenByCond`.
 */
function useConditions(pathPrefix: string[], element: CanHaveConditions): UseConditionsReturn {
    const { formData } = useFormDataState()

    // State of conditions
    const isHiddenByCond = ref(false)
    const isDisabledByCond = ref(false)

    // Predicate that tests a single condition
    const predicate = (cond: Condition) => isConditionTrue(cond, pathPrefix, formData.value)

    // Update condition state based on `formData` updates
    watchEffect(() => {
        isHiddenByCond.value = element.hide_if.some(predicate)
        isDisabledByCond.value = element.disable_if.some(predicate)
    })

    return { isDisabledByCond, isHiddenByCond }
}

interface UseConditionsReturn {
    /** Indicates if disabled by a condition. */
    isDisabledByCond: Ref<boolean>
    /** Indicates if hidden by a condition. */
    isHiddenByCond: Ref<boolean>
}

export default useConditions
