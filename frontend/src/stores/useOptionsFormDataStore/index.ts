/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import { computed, ref, toRaw, watch } from 'vue'

import { useAttemptData } from '@/queries/attempt'
import { useOptionsFormData, useOptionsFormDefinition, usePostOptionsFormData } from '@/queries/options'
import type { FormElement, OptionsFormData, OptionsFormDataValue, ServerValidationErrors } from '@/schema/options/types'

import {
    areFormDataObjIdentical,
    createFormDataValues,
    getElementName,
    getErrorKey,
    getFormData,
    hasEditableElements,
} from './formDataUtils'

/** Provides options form definition and manages form data. */
const useOptionsFormDataStore = defineStore('optionsFormData', () => {
    const { asyncStatus: definitionAsyncStatus, state: definitionState } = useOptionsFormDefinition()
    const { asyncStatus: dataAsyncStatus, state: dataState, refresh: dataRefresh } = useOptionsFormData()
    const { asyncStatus: postDataAsyncStatus, mutateAsync: postData, state: mutationState } = usePostOptionsFormData()
    const { state: attemptDataState } = useAttemptData()

    const formData = ref<OptionsFormData>({})
    const formDataClean = ref<OptionsFormData>({})
    const formErrors = ref<ServerValidationErrors>({})

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

    /**
     * Gets number of repetitions for a repetition element.
     *
     * @param path The path representing the repetition element.
     * @returns The number of repetitions.
     */
    function getRepetitionCount(path: string[]): number {
        // There's no explicit value in the data model, so we need to derive it from the form data.
        const re = new RegExp(`^${RegExp.escape(getElementName(path))}\\[(\\d+)\\]`)
        let highest = 0
        for (const elName of Object.keys(formData.value)) {
            const match = re.exec(elName)
            if (match) {
                highest = Math.max(highest, Number(match[1]))
            }
        }
        return highest
    }

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

    return {
        asyncStatus: computed(() =>
            definitionAsyncStatus.value === 'idle' && dataAsyncStatus.value === 'idle' ? 'idle' : 'loading',
        ),
        error: computed(() => definitionState.value.error ?? dataState.value.error ?? mutationState.value.error),

        hasEditableFields,
        isClean,
        isPreviewDisabled,
        isSaveDisabled,
        isSaving,

        formDefinition: computed(() => definitionState.value.data),
        formData,
        formErrors,

        /**
         * Submits the form data.
         *
         * @returns `false` if form has validation errors, otherwise `true`.
         */
        async submit(): Promise<boolean> {
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
        },

        /** Resets the form data. */
        reset(): void {
            formData.value = structuredClone(toRaw(formDataClean.value))
        },

        /**
         * Retrieves a value from the form data object.
         *
         * @param name The name representing the input field, e.g. `general[first_name]`.
         * @returns The value found at the specified name in the `formData` object, or `undefined` otherwise.
         */
        getValue<T extends OptionsFormDataValue>(name: string): T | undefined {
            if (name in formData.value) {
                return formData.value[name] as T
            }
        },

        /**
         * Sets a value on the form data object.
         *
         * @param name The name representing the input field, e.g. `general[first_name]`.
         * @param value The value to set at the specified name.
         */
        setValue(name: string, value: OptionsFormDataValue): void {
            formData.value[name] = value
        },

        /**
         * Retrieves the validation feedback text of a form element.
         *
         * @param path The path representing the element.
         * @returns The validation feedback text or `undefined`.
         */
        getFeedback(path: string[]): string | undefined {
            return formErrors.value[getErrorKey(path)]
        },

        /**
         * Adds another repetition to a repetition element.
         *
         * @param path The path representing the repetition element.
         * @param elements The repetition element's child elements.
         */
        addRepetition(path: string[], elements: FormElement[]): void {
            const count = getRepetitionCount(path) + 1
            createFormDataValues(formData.value, elements, [...path, count.toString()])
        },

        /**
         * Removes a repetition from a repetition element.
         *
         * @param path The path representing the repetition element.
         * @param num The repetition number to be removed.
         */
        removeRepetition(path: string[], num: number): void {
            const count = getRepetitionCount(path)
            const repName = getElementName(path)

            // Delete repetition values...
            let repNameWithNum = `${repName}[${num}]`
            for (const name of Object.keys(formData.value)) {
                if (name.startsWith(repNameWithNum)) {
                    delete formData.value[name]
                }
            }

            let errKey = getErrorKey([...path, String(num)])
            for (const key of Object.keys(formErrors.value)) {
                if (key.startsWith(errKey)) {
                    delete formErrors.value[key]
                }
            }

            // ...and shift all subsequent by one.
            for (let i = num + 1; i <= count; ++i) {
                repNameWithNum = `${repName}[${i}]`
                for (const [name, value] of Object.entries(formData.value)) {
                    if (name.startsWith(repNameWithNum)) {
                        formData.value[name.replace(repNameWithNum, `${repName}[${i - 1}]`)] = value
                        delete formData.value[name]
                    }
                }

                errKey = getErrorKey([...path, String(i)])
                for (const [key, value] of Object.entries(formErrors.value)) {
                    if (key.startsWith(errKey)) {
                        formErrors.value[key.replace(errKey, getErrorKey([...path, String(i - 1)]))] = value
                        delete formErrors.value[key]
                    }
                }
            }
        },

        getRepetitionCount,
    }
})

export default useOptionsFormDataStore
