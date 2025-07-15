/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type WritableComputedRef } from 'vue'

import { useFormDataState } from '@/composables/question'
import type { ElementToValue, FormElement } from '@/types'

import useCommon from './useCommon'

/**
 * A composable providing a two-way data binding model to options form elements.
 *
 * The model is backed by the {@link useFormDataState} composable.
 *
 * @param pathPrefix The parent's path of the form element.
 * @param element The form element definition object.
 *
 * @returns A data model that can be used with options form elements.
 */
function useModel<T extends FormElement>(
    pathPrefix: string[],
    element: T,
): WritableComputedRef<ElementToValue<T> | undefined, ElementToValue<T>> {
    const { name } = useCommon(pathPrefix, element)
    const { getValue, setValue } = useFormDataState()

    return computed({
        get: () => getValue<ElementToValue<T>>(name.value),
        set: (value: ElementToValue<T>) => {
            setValue(name.value, value)
        },
    })
}

export default useModel
