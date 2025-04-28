<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <AttemptRenderErrors />
    <BContainer fluid>
        <BRow>
            <BCol class="px-0" cols="12" md="8" order-md="2">
                <QuestionPreview ref="questionPreview" />
            </BCol>
            <BCol class="px-0 mb-3" cols="12" md="4" order-md="1">
                <BRow align-v="center">
                    <BCol cols="6" md="12">
                        <h3 class="mb-md-5">
                            <BBadge variant="info">{{
                                displayScore ? `Score: ${displayScore}` : 'Not yet scored'
                            }}</BBadge>
                        </h3>
                    </BCol>
                    <BCol class="px-0" cols="6" md="12">
                        <IconButton :iconComponent="IMdiEdit" to="/question" variant="link">Edit question</IconButton>
                    </BCol>
                </BRow>
            </BCol>
        </BRow>
    </BContainer>
    <ButtonGroup>
        <IconButton :iconComponent="IMdiContentSave" @click="save" variant="primary">Save</IconButton>
        <IconButton :iconComponent="IMdiContentSaveMove" @click="saveAndSubmit" variant="secondary"
            >Save and submit</IconButton
        >
        <IconButton :disabled="restartDisabled" :iconComponent="IMdiRestart" @click="restart" variant="warning"
            >Restart</IconButton
        >
        <IconButton :disabled="rescoreDisabled" :iconComponent="IMdiScore" @click="score" variant="info"
            >Re-score</IconButton
        >
    </ButtonGroup>
    <DisplayOptions />
    <AttemptDetails />
</template>

<script setup lang="ts">
import IMdiContentSave from '~icons/mdi/content-save'
import IMdiContentSaveMove from '~icons/mdi/content-save-move'
import IMdiEdit from '~icons/mdi/edit'
import IMdiRestart from '~icons/mdi/restart'
import IMdiScore from '~icons/mdi/score'
import { storeToRefs } from 'pinia'
import { ref } from 'vue'

import useAttemptStore from '@/stores/useAttemptStore'

const attemptStore = useAttemptStore()
const { restart, save: saveAttempt, score } = attemptStore
const { displayScore, rescoreDisabled, restartDisabled } = storeToRefs(attemptStore)

const questionPreview = ref<{ getFormData: () => Promise<Record<string, unknown>> }>()

async function save() {
    if (questionPreview.value) {
        const formData = await questionPreview.value.getFormData()
        await saveAttempt(formData)
    }
}

async function saveAndSubmit() {
    if (questionPreview.value) {
        const formData = await questionPreview.value.getFormData()
        await saveAttempt(formData)
        await score()
    }
}
</script>
