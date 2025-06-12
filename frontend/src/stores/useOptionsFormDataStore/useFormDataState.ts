/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, ref, toRaw, watch } from 'vue'

import { useAttemptDataQuery } from '@/queries/attempt'
import { useOptionsFormDataQuery, useOptionsFormDefinitionQuery, usePostOptionsFormDataQuery } from '@/queries/options'
import type { OptionsFormData, OptionsFormValue, ServerValidationErrors } from '@/types'

import { areFormDataObjIdentical, getErrorKey, getFormData, hasEditableElements } from './formDataUtils'
import useRepetitions from './useRepetitions'

function useFormDataState() {
    const { state: definitionState } = useOptionsFormDefinitionQuery()
    const { state: dataState, refresh: dataRefresh } = useOptionsFormDataQuery()
    const {
        asyncStatus: postDataAsyncStatus,
        mutateAsync: postData,
        state: mutationState,
    } = usePostOptionsFormDataQuery()
    const { state: attemptDataState } = useAttemptDataQuery()

    // Form data
    const formData = ref<OptionsFormData>({})
    const formDataClean = ref<OptionsFormData>({})

    // Form validation errors
    const formErrors = ref<ServerValidationErrors>({})

    // Build form data from server-side state
    watch([() => definitionState.value.status, () => dataState.value.status], ([definitionStatus, dataStatus]) => {
        if (
            definitionStatus === 'success' &&
            dataStatus === 'success' &&
            definitionState.value.data &&
            dataState.value.data
        ) {
            // Restore form data and populate with default values
            formData.value = getFormData(definitionState.value.data, dataState.value.data)
            // Remember clean form state
            formDataClean.value = structuredClone(toRaw(formData.value))
        }
    })

    // Form logic

    const hasAttemptState = computed(() => attemptDataState.value.data !== undefined)
    const hasEditableFields = computed(
        () =>
            hasEditableElements(definitionState.value.data?.general ?? []) ||
            (definitionState.value.data?.sections ?? []).some((section) => hasEditableElements(section.elements)),
    )

    const isClean = computed(() => areFormDataObjIdentical(formData.value, formDataClean.value))
    const isSaving = computed(() => postDataAsyncStatus.value !== 'idle')

    const isSaveDisabled = computed(() => isClean.value || isSaving.value)
    const isPreviewDisabled = computed(
        () => isSaving.value || (!hasAttemptState.value && isClean.value) || Object.keys(formErrors.value).length > 0,
    )

    /**
     * Submits the form data.
     *
     * @returns `false` if form has validation errors, otherwise `true`.
     */
    async function submit(): Promise<boolean> {
        const rawFormData = toRaw(formData.value)
        try {
            formErrors.value = await postData(rawFormData)
        } catch (err) {
            if (err instanceof Error) {
                mutationState.value.error = err
            }
            throw err
        }
        formDataClean.value = structuredClone(rawFormData)
        mutationState.value.error = null
        await dataRefresh()
        return Object.keys(formErrors.value).length === 0
    }

    /** Resets the form data. */
    function reset(): void {
        formData.value = structuredClone(toRaw(formDataClean.value))
    }

    /**
     * Retrieves a value from the form data object.
     *
     * @param name The name representing the input field, e.g. `general[first_name]`.
     * @returns The value found at the specified name in the `formData` object, or `undefined` otherwise.
     */
    function getValue<T extends OptionsFormValue>(name: string): T | undefined {
        if (name in formData.value) {
            return formData.value[name] as T
        }
    }

    /**
     * Sets a value on the form data object.
     *
     * @param name The name representing the input field, e.g. `general[first_name]`.
     * @param value The value to set at the specified name.
     */
    function setValue(name: string, value: OptionsFormValue): void {
        formData.value[name] = value
    }

    /**
     * Retrieves the validation feedback text of a form element.
     *
     * @param path The path representing the element.
     * @returns The validation feedback text or `undefined`.
     */
    function getFeedback(path: string[]): string | undefined {
        return formErrors.value[getErrorKey(path)]
    }

    return {
        formData,
        formErrors,

        hasEditableFields,
        isClean,
        isPreviewDisabled,
        isSaveDisabled,
        isSaving,

        submit,
        reset,
        getValue,
        setValue,
        getFeedback,

        ...useRepetitions(formData, formErrors),
    }
}

export default useFormDataState
