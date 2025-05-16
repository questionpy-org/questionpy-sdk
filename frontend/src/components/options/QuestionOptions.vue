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
    <ButtonGroup>
        <template v-if="hasEditableFields">
            <IconButton
                :disabled="isPreviewDisabled"
                :iconComponent="IMdiEye"
                @click="saveAndPreview"
                variant="secondary"
                >{{ isClean ? 'Preview' : 'Save and preview' }}</IconButton
            >
            <IconButton :disabled="isSaveDisabled" :iconComponent="IMdiContentSave" @click="submit" variant="primary"
                >Save</IconButton
            >
            <IconButton
                :disabled="isSaveDisabled"
                :iconComponent="IMdiContentSaveMove"
                @click="saveAndReturn"
                variant="secondary"
                >Save and return</IconButton
            >
        </template>
        <IconButton v-else :iconComponent="IMdiEye" @click="preview" variant="secondary">Preview</IconButton>
        <IconButton :disabled="isSaving" :iconComponent="IMdiCancel" to="/" variant="danger">Cancel</IconButton>
    </ButtonGroup>
</template>

<script lang="ts" setup>
import IMdiCancel from '~icons/mdi/cancel'
import IMdiContentSave from '~icons/mdi/content-save'
import IMdiContentSaveMove from '~icons/mdi/content-save-move'
import IMdiEye from '~icons/mdi/eye'
import { useModalController } from 'bootstrap-vue-next'
import { storeToRefs } from 'pinia'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import type { ModalOrchestratorShowParam } from 'bootstrap-vue-next'

import useOptionsFormDataStore from '@/stores/useOptionsFormDataStore'

const router = useRouter()
const { confirm: confirmModal } = useModalController()
const store = useOptionsFormDataStore()
const { reset, submit } = store
const { asyncStatus, error, formDefinition, hasEditableFields, isClean, isPreviewDisabled, isSaveDisabled, isSaving } =
    storeToRefs(store)

const modalOptions = {
    props: {
        centered: true,
        noHeaderClose: true,
        title: 'Unsaved Changes',
        body: 'You have unsaved changes. If you leave now, your changes will be lost.',
        okTitle: 'Discard Changes',
        okVariant: 'danger',
        cancelTitle: 'Keep Editing',
        cancelVariant: 'primary',
    },
} satisfies ModalOrchestratorShowParam

onBeforeRouteLeave(async () => {
    // Give user the opportunity to cancel page navigation in case they have unsaved changes
    if (!isClean.value) {
        if (await confirmModal?.(modalOptions)) {
            // Reset form data to clean state and continue...
            reset()
        } else {
            // ...or cancel navigation
            return false
        }
    }
})

async function saveAndPreview() {
    if (isClean.value || (await submit())) {
        await router.push('/attempt')
    }
}

async function preview() {
    if (await submit()) {
        await router.push('/attempt')
    }
}

async function saveAndReturn() {
    if (await submit()) {
        await router.push('/')
    }
}
</script>
