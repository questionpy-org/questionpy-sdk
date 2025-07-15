/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type ComputedRef } from 'vue'

import { getElementName } from '@/composables/question/formDataUtils'
import type { FormElement } from '@/types'

/**
 * A composable providing common values to options form elements.
 *
 * @param pathPrefix The parent's path of the form element.
 * @param element The form element definition object.
 *
 * @returns An object containing `id`, `name` and `path` for the form element.
 */
function useCommon(pathPrefix: string[], element: FormElement): UseCommonReturn {
    const path = computed(() => [...pathPrefix, element.name])
    const name = computed(() => getElementName(path.value))
    const id = computed(() => `options_${name.value}`)

    return { id, name, path }
}

interface UseCommonReturn {
    /** `id` attribute. */
    id: ComputedRef<string>
    /** `name` attribute. */
    name: ComputedRef<string>
    /** Element path inside options form definition. */
    path: ComputedRef<string[]>
}

export default useCommon
