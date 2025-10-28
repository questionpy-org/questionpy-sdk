<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <LoadingIndicator v-if="asyncStatus === 'loading'" />
    <ErrorCard v-if="error" :error="error" />
    <template v-else>
        <AttemptRenderErrors v-if="renderErrors" :render-errors="renderErrors" />
        <BContainer fluid>
            <BRow>
                <BCol class="px-0" cols="12" md="8" order-md="2">
                    <AttemptIframe v-if="iframeSrcDoc" :src-doc="iframeSrcDoc" ref="attemptIframeRef" />
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
                            <IconButton
                                :icon-component="IMdiEdit"
                                :to="{ name: 'question-edit', params: { questionId } }"
                                variant="link"
                                >Edit question</IconButton
                            >
                        </BCol>
                    </BRow>
                </BCol>
            </BRow>
        </BContainer>
        <ButtonGroup class="mb-4">
            <IconButton :icon-component="IMdiContentSave" @click="save" variant="primary">Save</IconButton>
            <IconButton :icon-component="IMdiContentSaveMove" @click="saveAndSubmit" variant="secondary"
                >Save and submit</IconButton
            >
            <IconButton :disabled="isRestartDisabled" :icon-component="IMdiRestart" @click="restart" variant="warning"
                >Restart</IconButton
            >
            <IconButton :disabled="isRescoreDisabled" :icon-component="IMdiScore" @click="score" variant="info"
                >Re-score</IconButton
            >
        </ButtonGroup>
        <DisplayOptions class="mb-4" />
        <AttemptCard
            v-if="attemptData"
            :attempt-data="attemptData"
            :question-id="questionId"
            :attempt-id="attemptId"
            collapsible
            variant="info"
        />
    </template>
</template>

<script setup lang="ts">
import IMdiContentSave from '~icons/mdi/content-save'
import IMdiContentSaveMove from '~icons/mdi/content-save-move'
import IMdiEdit from '~icons/mdi/edit'
import IMdiRestart from '~icons/mdi/restart'
import IMdiScore from '~icons/mdi/score'
import { ref } from 'vue'

import { useAttemptDisplay } from '@/composables/attempt'
import useAttempt from '@/composables/attempt/useAttempt'
import type AttemptIframe from '@/components/attempt/AttemptIframe.vue'

type AttemptIframeInstanceType = InstanceType<typeof AttemptIframe>

const { questionId, attemptId } = defineProps<{
    questionId: string
    attemptId: string
}>()

const {
    asyncStatus,
    attemptData,
    error,
    iframeSrcDoc,
    renderErrors,
    score,
    isRescoreDisabled,
    isRestartDisabled,
    restart,
    save: saveAttempt,
} = useAttempt(questionId, attemptId)
const { displayScore } = useAttemptDisplay(attemptData)
const attemptIframeRef = ref<AttemptIframeInstanceType>()

async function save() {
    if (attemptIframeRef.value) {
        const formData = await attemptIframeRef.value.getFormData()
        await saveAttempt(formData)
    }
}

async function saveAndSubmit() {
    if (attemptIframeRef.value) {
        const formData = await attemptIframeRef.value.getFormData()
        await saveAttempt(formData)
        await score()
    }
}
</script>
