/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { storeToRefs } from 'pinia'
import { computed, toValue } from 'vue'
import type { ComputedRef, MaybeRefOrGetter } from 'vue'

import { useFormDataState } from '@/composables/question'
import usePendingOperationsStore from '@/stores/usePendingOperationsStore'

/**
 * A composable providing a disabled state to options form elements.
 *
 * The element is considered disabled if the underlying store is currently busy or the parameter `disabled` is true.
 *
 * @param disabled The general disabled state of the form element.
 * @returns `true` if form element should be disabled, otherwise `false`.
 */
function useIsDisabled(disabled: MaybeRefOrGetter<boolean> = false): ComputedRef<boolean> {
    const { isSaving } = useFormDataState()
    const { hasPendingOperations } = storeToRefs(usePendingOperationsStore())
    return computed(() => hasPendingOperations.value || isSaving.value || toValue(disabled))
}

export default useIsDisabled
