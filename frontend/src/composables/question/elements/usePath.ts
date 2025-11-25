/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type ComputedRef } from 'vue'

import type { ElementPath, FormElement } from '@/types'

/**
 * A composable providing the child path value for form elements constructed from the parent's path.
 *
 * @param pathPrefix The parent's path of the form element.
 * @param element The form element definition object.
 *
 * @returns Element path inside options form definition.
 */
function usePath(pathPrefix: ElementPath, element: FormElement): ComputedRef<ElementPath> {
    return computed(() => [...pathPrefix, element.name])
}

export default usePath
