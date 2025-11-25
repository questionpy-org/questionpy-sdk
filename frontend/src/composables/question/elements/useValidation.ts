/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, toValue } from 'vue'
import type { ComputedRef, MaybeRef } from 'vue'

import { useFormDataState } from '@/composables/question'
import { getErrorKey } from '@/composables/question/formDataUtils'
import type { ElementPath, ValidationInfo } from '@/types'

/**
 * A composable providing validation feedback text and state for options form elements.
 *
 * @param path The element's path.
 *
 * @returns An object containing the validation state and text for the form element.
 */
function useValidation(path: MaybeRef<ElementPath>): ComputedRef<ValidationInfo> {
    const { formErrors } = useFormDataState()

    return computed(() => {
        const text = formErrors.value[getErrorKey(toValue(path))]
        const state = text ? false : null
        return { state, text }
    })
}

export default useValidation
