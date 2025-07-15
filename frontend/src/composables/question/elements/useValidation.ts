/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type ComputedRef } from 'vue'

import { useFormDataState } from '@/composables/question'
import type { FormElement } from '@/types'

import useCommon from './useCommon'

/**
 * A composable providing validation feedback text and state for options form elements.
 *
 * @param pathPrefix The parent's path of the form element.
 * @param element The form element definition object.
 *
 * @returns An object containing `validationId`, `validationState` and `validationText` for the form element.
 */
function useValidation(pathPrefix: string[], element: FormElement): UseValidationReturn {
    const { id: elementId, path } = useCommon(pathPrefix, element)
    const { getFeedback } = useFormDataState()

    const text = computed(() => getFeedback(path.value))

    return {
        validationId: computed(() => (text.value ? `${elementId.value}___feedback` : undefined)),
        validationState: computed(() => (text.value ? false : null)),
        validationText: text,
    }
}

interface UseValidationReturn {
    /** `id` attribute for the validation element. */
    validationId: ComputedRef<string | undefined>
    /**
     * Validation state.
     *
     * See {@link https://bootstrap-vue-next.github.io/bootstrap-vue-next/docs/components/form-group.html#validation-state-feedback|BootstrapVueNext docs}
     */
    validationState: ComputedRef<false | null>
    /** Validation feedback text. */
    validationText: ComputedRef<string | undefined>
}

export default useValidation
