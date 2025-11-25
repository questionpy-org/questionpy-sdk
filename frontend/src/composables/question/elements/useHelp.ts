/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type ComputedRef } from 'vue'

import type { CanHaveHelp, ElementPath } from '@/types'

import useId from './useId'
import usePath from './usePath'

/**
 * A composable providing help texts to options form elements.
 *
 * @param pathPrefix The parent's path of the form element.
 * @param element The form element definition object.
 *
 * @returns An object containing `helpId` and `helpText` for the form element.
 */
function useHelp(pathPrefix: ElementPath, element: CanHaveHelp): UseHelpReturn {
    const path = usePath(pathPrefix, element)
    const elementId = useId(path)
    const hasHelp = computed(() => (element.help ?? '').length > 0)

    return {
        helpId: computed(() => (hasHelp.value ? `${elementId.value}___help` : undefined)),
        helpText: computed(() => (hasHelp.value ? (element.help as string) : undefined)),
    }
}

interface UseHelpReturn {
    /** `id` attribute for the help element. */
    helpId: ComputedRef<string | undefined>
    /** Help text. */
    helpText: ComputedRef<string | undefined>
}

export default useHelp
