<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <LoadingIndicator v-if="asyncStatus === 'loading'" />
    <ErrorCard v-if="error" :error="error" />
    <BForm v-else-if="formDefinition">
        <OptionsSection header="General" name="general" :elements="formDefinition.general" />
        <OptionsSection
            v-for="section in formDefinition.sections"
            :elements="section.elements"
            :header="section.header"
            :key="section.name"
            :name="section.name"
        />
    </BForm>
    <ButtonGroup class="mb-4">
        <template v-if="hasEditableFields">
            <IconButton :disabled="isSaveDisabled" :icon-component="SubmitIcon" @click="submit" variant="primary">{{
                submitLabel
            }}</IconButton>
            <IconButton
                :disabled="isSaveDisabled"
                :icon-component="IMdiContentSaveMove"
                @click="saveAndReturn"
                variant="secondary"
                >{{ submitLabel }} and return</IconButton
            >
            <IconButton
                :disabled="isPreviewDisabled"
                :icon-component="IMdiEye"
                @click="saveAndPreview"
                variant="secondary"
                >{{ submitAndPreviewLabel }}</IconButton
            >
        </template>
        <IconButton v-else :icon-component="IMdiEye" @click="preview" variant="secondary">Preview</IconButton>
        <IconButton :disabled="isSaving" :icon-component="IMdiCancel" :to="{ name: 'index' }" variant="danger"
            >Cancel</IconButton
        >
    </ButtonGroup>
</template>

<script lang="ts" setup>
import IMdiCancel from '~icons/mdi/cancel'
import IMdiContentSave from '~icons/mdi/content-save'
import IMdiContentSaveMove from '~icons/mdi/content-save-move'
import IMdiContentSavePlus from '~icons/mdi/content-save-plus'
import IMdiEye from '~icons/mdi/eye'
import { computed, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'

import { useConfirmModal } from '@/composables/common'
import { provideFormDataState } from '@/composables/question/useFormDataState'
import useAppStateStore from '@/stores/useAppStateStore'

const { questionId } = defineProps<{ questionId: string }>()

const router = useRouter()
const store = useAppStateStore()
const {
    asyncStatus,
    error,
    formDefinition,
    hasEditableFields,
    isClean,
    isNew,
    isPreviewDisabled,
    isSaveDisabled,
    isSaving,
    reset,
    submit,
} = provideFormDataState(questionId)

const confirmModal = useConfirmModal({
    title: 'Unsaved Changes',
    body: 'You have unsaved changes. If you leave now, your changes will be lost.',
    okTitle: 'Discard Changes',
    cancelTitle: 'Keep Editing',
})

onBeforeRouteLeave(async () => {
    // Give user the opportunity to cancel page navigation in case they have unsaved changes
    if (!isClean.value) {
        if (await confirmModal()) {
            // Reset form data to clean state and continue...
            reset()
        } else {
            // ...or cancel navigation
            return false
        }
    }
})

const submitLabel = computed(() => (isNew.value ? 'Create' : 'Save'))
const submitAndPreviewLabel = computed(() => (isClean && !isNew.value ? 'Preview' : `${submitLabel.value} and preview`))
const SubmitIcon = computed(() => (isNew.value ? IMdiContentSavePlus : IMdiContentSave))

watch(
    isNew,
    (isNewValue) => {
        store.pageTitle = isNewValue ? 'Create Question' : 'Edit Question'
    },
    { immediate: true },
)

async function saveAndPreview() {
    if (isClean.value || (await submit())) {
        await router.push({ name: 'question', params: { questionId } })
    }
}

async function preview() {
    if (await submit()) {
        await router.push({ name: 'question', params: { questionId } })
    }
}

async function saveAndReturn() {
    if (await submit()) {
        await router.push({ name: 'index' })
    }
}
</script>
