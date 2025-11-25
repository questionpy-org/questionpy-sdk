/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { ref, watch } from 'vue'
import type { Ref } from 'vue'

import { useFormDataState } from '@/composables/question'
import { assertNever } from '@/types'
import type { UseFormDataStateReturn } from '@/composables/question/useFormDataState'
import type { CanHaveConditions, Condition, ElementPath } from '@/types'

/**
 * Evaluates whether a given condition is met based on form data and a base path.
 *
 * @param cond The condition to evaluate (see `questionpy.form` Python module for a detailed description).
 * @param basePath The base path used as a starting point for relative references.
 * @param getValue The form data value getter.
 *
 * @returns Returns true if the condition is satisfied, false otherwise.
 */
function isConditionTrue(
    cond: Condition,
    basePath: ElementPath,
    getValue: UseFormDataStateReturn['getValue'],
): boolean {
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

    const refValue = getValue(refPath)

    if (refValue === undefined) {
        throw new Error(`Invalid condition detected: ${cond.name}`)
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
function useConditions<T extends CanHaveConditions>(pathPrefix: ElementPath, element: T): UseConditionsReturn {
    const { formData, getValue } = useFormDataState()

    // State of conditions
    const isHiddenByCond = ref(false)
    const isDisabledByCond = ref(false)

    const isRepetition = typeof pathPrefix[pathPrefix.length - 1] === 'number'

    // For elements inside repetitions, the reference is relative to the repetition when accessing parent element
    //  -> remove last number part
    const basePath = (cond: Condition) =>
        cond.name.startsWith('..') && isRepetition ? pathPrefix.slice(0, -1) : pathPrefix

    // Predicate that tests a single condition
    const predicate = (cond: Condition) => isConditionTrue(cond, basePath(cond), getValue)

    // Update condition state based on `formData` updates
    watch(
        formData.value,
        () => {
            isHiddenByCond.value = element.hide_if.some(predicate)
            isDisabledByCond.value = element.disable_if.some(predicate)
        },
        { immediate: true },
    )

    return { isDisabledByCond, isHiddenByCond }
}

interface UseConditionsReturn {
    /** Indicates if disabled by a condition. */
    isDisabledByCond: Ref<boolean>
    /** Indicates if hidden by a condition. */
    isHiddenByCond: Ref<boolean>
}

export default useConditions
