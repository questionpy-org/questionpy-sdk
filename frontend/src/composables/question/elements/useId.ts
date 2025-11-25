/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, toValue } from 'vue'
import type { ComputedRef, MaybeRef } from 'vue'

import type { ElementPath } from '@/types'

/**
 * A composable providing the id attribute value for form elements.
 *
 * @param path The form element's path inside the options form definition.
 *
 * @returns The HTML `id` for the form element.
 */
function useId(path: MaybeRef<ElementPath>): ComputedRef<string> {
    return computed(() => `options_input.${toValue(path).join('.')}`)
}

export default useId
