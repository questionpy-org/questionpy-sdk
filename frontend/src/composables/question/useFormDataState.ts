/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, inject, provide, ref, toRaw, watch } from 'vue'
import type { ComputedRef, InjectionKey, Ref, ShallowRef } from 'vue'

import { useOptionsFormDataQuery, useOptionsFormDefinitionQuery, usePostOptionsFormDataMutation } from '@/queries'
import usePendingOperationsStore from '@/stores/usePendingOperationsStore'
import { isObject } from '@/types'
import type {
    ElementPath,
    OptionsFormData,
    OptionsFormDefinition,
    OptionsFormValue,
    ServerValidationErrors,
} from '@/types'

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
        data: formDefinition,
        error: formDefinitionError,
        isPending: formDefinitionIsPending,
        status: formDefinitionStatus,
    } = useOptionsFormDefinitionQuery(questionId)
    const {
        data: formDataRemote,
        error: formDataError,
        refresh: formDataRefresh,
        isPending: formDataIsPending,
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

    const { addOperation, removeOperation } = usePendingOperationsStore()

    // Build form data from server-side state
    watch(
        [() => formDefinitionStatus.value, () => formDataStatus.value],
        ([definitionStatus, dataStatus]) => {
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
        },
        {
            // If the queries already succeeded before this composable mounted, run once immediately
            immediate: true,
        },
    )

    const error = computed(() => formDefinitionError.value ?? formDataError.value ?? postDataError.value)
    const isPending = computed(() => formDefinitionIsPending.value || formDataIsPending.value)

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

    const isSaveDisabled = computed(
        () =>
            // Always allow initial creation
            !isNew.value &&
            // On existing: disable when nothing changed
            (isClean.value || isSaving.value),
    )
    const isPreviewDisabled = computed(() => isSaving.value || (!isNew.value && hasValidationErrors.value))

    // Form methods

    async function submit(): Promise<boolean> {
        const rawFormData = toRaw(formDataCurrent.value)

        const operation = addOperation('submit', { modelType: 'question' })
        try {
            formErrors.value = await postData(rawFormData)
        } catch (err) {
            if (err instanceof Error) {
                mutationState.value.error = err
            }
            throw err
        } finally {
            removeOperation(operation)
        }

        formDataClean.value = structuredClone(rawFormData)
        mutationState.value.error = null
        await formDataRefresh()

        return Object.keys(formErrors.value).length === 0
    }

    function reset(): void {
        formDataCurrent.value = structuredClone(toRaw(formDataClean.value))
    }

    function navigateToNestedProperty(path: ElementPath) {
        // Adjust path: the general section elements are at the root
        const adjustedPath = path[0] === 'general' ? path.slice(1) : path

        let current: unknown = formDataCurrent.value
        for (const key of adjustedPath) {
            if (isObject(current) && typeof key === 'string') {
                current = current[key]
                continue
            } else if (Array.isArray(current) && typeof key === 'number') {
                current = current[key]
                continue
            }
            return undefined
        }

        return current
    }

    function getValue<T extends OptionsFormValue>(path: ElementPath): T | undefined {
        return navigateToNestedProperty(path) as T
    }

    function setValue(path: ElementPath, value: OptionsFormValue): void {
        // Navigate to the parent of the target property
        const parentPath = path.slice(0, -1)
        const parent = navigateToNestedProperty(parentPath)

        // Set value
        const targetKey = path[path.length - 1]
        if (isObject(parent) && typeof targetKey === 'string') {
            parent[targetKey] = value
        } else if (Array.isArray(parent) && typeof targetKey === 'number') {
            parent[targetKey] = value
        } else {
            throw TypeError('Expected array or object in form data')
        }

        // Remove validation errors after edit
        resetFeedback(path)
    }

    function resetFeedback(path: ElementPath): void {
        const errorKey = getErrorKey(path)
        for (const key of Object.keys(formErrors.value)) {
            if (key.startsWith(errorKey)) {
                delete formErrors.value[key]
            }
        }
    }

    const formDataState = {
        formDefinition,
        formData: formDataCurrent,
        formErrors,
        isPending,
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
        resetFeedback,
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

    /**  Whether the form requests are still pending their first call. */
    isPending: ComputedRef<boolean>

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
     * @param path The element path representing the input field.
     * @returns The value found at the specified `path` in the `formData` object, or `undefined` otherwise.
     */
    getValue<T extends OptionsFormValue>(path: ElementPath): T | undefined

    /**
     * Sets a value on the form data object.
     *
     * @param path The element path representing the input field.
     * @param value The value to set at the specified name.
     */
    setValue(path: ElementPath, value: OptionsFormValue): void

    /**
     * Resets the validation feedback text of a form element and all its children.
     *
     * @param path The path representing the element.
     */
    resetFeedback(path: ElementPath): void
}

export type { UseFormDataStateReturn }
export { provideFormDataState }
export default useFormDataState
