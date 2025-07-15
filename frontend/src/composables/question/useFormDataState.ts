/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, inject, provide, ref, toRaw, watch } from 'vue'
import type { AsyncStatus } from '@pinia/colada'
import type { ComputedRef, InjectionKey, Ref, ShallowRef } from 'vue'

import { useOptionsFormDataQuery, useOptionsFormDefinitionQuery, usePostOptionsFormDataMutation } from '@/queries'
import type { OptionsFormData, OptionsFormDefinition, OptionsFormValue, ServerValidationErrors } from '@/types'

import { areFormDataObjIdentical, getErrorKey, getFormData, hasEditableElements } from './formDataUtils'

const QUESTION_FORM_DATA_KEY = Symbol('question-form-data') as InjectionKey<UseFormDataStateReturn>

/**
 * Composable that provides stateful form data to all child components.
 *
 * @param questionId ID of the question.
 * @returns An object containing form state and mutation methods.
 */
function provideFormDataState(questionId: string): UseFormDataStateReturn {
    const {
        asyncStatus: formDefinitionAsyncStatus,
        data: formDefinition,
        error: formDefinitionError,
        status: formDefinitionStatus,
    } = useOptionsFormDefinitionQuery(questionId)
    const {
        asyncStatus: formDataAsyncStatus,
        data: formDataRemote,
        error: formDataError,
        refresh: formDataRefresh,
        status: formDataStatus,
    } = useOptionsFormDataQuery(questionId)
    const {
        asyncStatus: postDataAsyncStatus,
        error: postDataError,
        mutateAsync: postData,
        state: mutationState,
    } = usePostOptionsFormDataMutation(questionId)

    // Form data
    const formDataCurrent = ref<OptionsFormData>({})
    const formDataClean = ref<OptionsFormData>({})

    // Form validation errors
    const formErrors = ref<ServerValidationErrors>({})

    // Build form data from server-side state
    watch([() => formDefinitionStatus.value, () => formDataStatus.value], ([definitionStatus, dataStatus]) => {
        if (
            definitionStatus === 'success' &&
            dataStatus === 'success' &&
            formDefinition.value &&
            formDataRemote.value
        ) {
            // Restore form data and populate with default values
            formDataCurrent.value = getFormData(formDefinition.value, formDataRemote.value.data)
            // Remember clean form state
            formDataClean.value = structuredClone(toRaw(formDataCurrent.value))
        }
    })

    const asyncStatus = computed(() =>
        [formDefinitionAsyncStatus, formDataAsyncStatus, postDataAsyncStatus].some(
            (status) => status.value === 'loading',
        )
            ? 'loading'
            : 'idle',
    )
    const error = computed(() => formDefinitionError.value ?? formDataError.value ?? postDataError.value)

    // Form logic

    const hasEditableFields = computed(
        () =>
            hasEditableElements(formDefinition.value?.general ?? []) ||
            (formDefinition.value?.sections ?? []).some((section) => hasEditableElements(section.elements)),
    )
    const hasValidationErrors = computed(() => Object.keys(formErrors.value).length > 0)

    const isNew = computed(() => formDataRemote.value?.is_new ?? false)
    const isClean = computed(() => areFormDataObjIdentical(formDataCurrent.value, formDataClean.value))
    const isSaving = computed(() => postDataAsyncStatus.value !== 'idle')

    const isSaveDisabled = computed(() => isClean.value || isSaving.value)
    const isPreviewDisabled = computed(
        () => (isNew.value && isClean.value) || isSaving.value || hasValidationErrors.value,
    )

    // Form methods

    async function submit(): Promise<boolean> {
        const rawFormData = toRaw(formDataCurrent.value)
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
        await formDataRefresh()
        return Object.keys(formErrors.value).length === 0
    }

    function reset(): void {
        formDataCurrent.value = structuredClone(toRaw(formDataClean.value))
    }

    function getValue<T extends OptionsFormValue>(name: string): T | undefined {
        if (name in formDataCurrent.value) {
            return formDataCurrent.value[name] as T
        }
    }

    function setValue(name: string, value: OptionsFormValue): void {
        formDataCurrent.value[name] = value
    }

    function getFeedback(path: string[]): string | undefined {
        return formErrors.value[getErrorKey(path)]
    }

    const formDataState = {
        formDefinition,
        formData: formDataCurrent,
        formErrors,
        asyncStatus,
        error,

        hasEditableFields,
        isNew,
        isClean,
        isPreviewDisabled,
        isSaveDisabled,
        isSaving,

        submit,
        reset,
        getValue,
        setValue,
        getFeedback,
    }

    // Provide form data to child components
    provide(QUESTION_FORM_DATA_KEY, formDataState)

    return formDataState
}

/**
 * Composable for accessing and managing stateful form data related to a question's options.
 *
 * Designed to be used within child components of an options form.
 * Requires a parent component to provide the form data via injection.
 *
 * @returns An object containing form state and mutation methods.
 */
function useFormDataState(): UseFormDataStateReturn {
    // Reuse existing instance provided higher in the component tree
    const existing = inject(QUESTION_FORM_DATA_KEY, null)
    if (!existing) {
        throw Error('No form data state was provided by a parent component.')
    }
    return existing
}

/** Encapsulates reactive form state and mutation methods for an options form. */
interface UseFormDataStateReturn {
    /** Reactive reference to the form definition. */
    formDefinition: ShallowRef<OptionsFormDefinition | undefined>

    /** Reactive reference to the current form data. */
    formData: Ref<OptionsFormData>

    /** Reactive reference to current form validation errors. */
    formErrors: Ref<ServerValidationErrors>

    /** Computed combined async loading status. */
    asyncStatus: ComputedRef<AsyncStatus>

    /** Computed reference to the latest error from underlying queries. */
    error: ComputedRef<Error | null>

    /** Whether the form includes user-editable fields. */
    hasEditableFields: ComputedRef<boolean>

    /** Whether the form has not been modified since the last save. */
    isClean: ComputedRef<boolean>

    /** Whether the preview action is currently disabled. */
    isPreviewDisabled: ComputedRef<boolean>

    /** Whether the save action should currently be disabled. */
    isSaveDisabled: ComputedRef<boolean>

    /** Whether the form is currently in the process of saving. */
    isSaving: ComputedRef<boolean>

    /** Whether the question is newly created and has not been persisted yet. */
    isNew: ComputedRef<boolean>

    /**
     * Submits the form data.
     *
     * @returns `false` if form has validation errors, otherwise `true`.
     */
    submit(): Promise<boolean>

    /** Resets the form data. */
    reset(): void

    /**
     * Retrieves a value from the form data object.
     *
     * @param name The name representing the input field, e.g. `general[first_name]`.
     * @returns The value found at the specified name in the `formData` object, or `undefined` otherwise.
     */
    getValue<T extends OptionsFormValue>(name: string): T | undefined

    /**
     * Sets a value on the form data object.
     *
     * @param name The name representing the input field, e.g. `general[first_name]`.
     * @param value The value to set at the specified name.
     */
    setValue(name: string, value: OptionsFormValue): void

    /**
     * Retrieves the validation feedback text of a form element.
     *
     * @param path The path representing the element.
     * @returns The validation feedback text or `undefined`.
     */
    getFeedback(path: string[]): string | undefined
}

export { provideFormDataState }
export default useFormDataState
