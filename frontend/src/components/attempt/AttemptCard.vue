<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <component :is="cardComponent" v-bind="cardComponent === CollapsibleCard ? { expanded: true } : {}">
        <template #button-title>Current attempt</template>
        <BContainer class="p-0" fluid>
            <BRow class="mb-3">
                <BCol>Attempt status</BCol>
                <BCol class="fw-bold">{{ displayStatus }}</BCol>
            </BRow>
            <BRow class="mb-3">
                <BCol>Variant</BCol>
                <BCol class="fw-bold">{{ attemptData.variant }}</BCol>
            </BRow>
            <BRow class="mb-3">
                <BCol>Attempt state</BCol>
                <BCol>
                    <div class="bg-body-secondary border rounded-1 p-2">
                        <pre class="mb-0"><code>{{ attemptData.attempt_state }}</code></pre>
                    </div>
                </BCol>
            </BRow>
            <BRow class="mb-3">
                <BCol>Storage location</BCol>
                <BCol class="fw-bold"></BCol>
            </BRow>
            <template v-if="isScored">
                <BRow class="mb-3">
                    <BCol>Scoring code</BCol>
                    <BCol class="fw-bold">{{ attemptData.scoring_code }}</BCol>
                </BRow>
                <BRow class="mb-3">
                    <BCol>Score</BCol>
                    <BCol class="fw-bold">{{ displayScore }}</BCol>
                </BRow>
                <BRow class="mb-3">
                    <BCol>Scoring state</BCol>
                    <BCol>
                        <div class="bg-body-secondary border rounded-1 p-2" v-if="attemptData.scoring_state">
                            <pre class="mb-0"><code>{{ attemptData.scoring_state }}</code></pre>
                        </div>
                    </BCol>
                </BRow>
                <BRow class="mb-3">
                    <BCol>Scoring state files</BCol>
                    <BCol class="fw-bold"></BCol>
                </BRow>
            </template>
        </BContainer>
        <ButtonGroup>
            <!-- TODO: Implement clone -->
            <IconButton :icon-component="IMdiContentCopy" variant="secondary" size="sm">Clone</IconButton>
            <!-- TODO: Implement export -->
            <IconButton :icon-component="IMdiExport" variant="secondary" size="sm">Export</IconButton>
            <IconButton @click="deleteAttempt" :icon-component="IMdiDelete" variant="danger" size="sm"
                >Delete</IconButton
            >
            <IconButton
                v-if="!isCurrentPreviewActive"
                :to="attemptLocation"
                :icon-component="IMdiEye"
                variant="primary"
                size="sm"
                >Preview</IconButton
            >
        </ButtonGroup>
    </component>
</template>

<script setup lang="ts">
import IMdiContentCopy from '~icons/mdi/content-copy'
import IMdiDelete from '~icons/mdi/delete'
import IMdiExport from '~icons/mdi/export'
import IMdiEye from '~icons/mdi/eye'
import { BCard } from 'bootstrap-vue-next'
import { computed } from 'vue'
import { useLink } from 'vue-router'

import CollapsibleCard from '@/components/common/CollapsibleCard.vue'
import { useAttemptDisplay } from '@/composables/attempt'
import { useDeleteAttempt } from '@/composables/attempt'
import type { AttemptData } from '@/types'

const {
    attemptData,
    attemptId,
    collapsible = false,
    questionId,
} = defineProps<{
    attemptData: AttemptData
    attemptId: string
    collapsible?: boolean
    questionId: string
}>()

const attemptLocation = { name: 'question-attempt', params: { questionId, attemptId } } as const

const deleteAttempt = useDeleteAttempt(questionId, attemptId)
const { isActive: isCurrentPreviewActive } = useLink({ to: attemptLocation })
const { isScored, displayScore, displayStatus } = useAttemptDisplay(attemptData)

const cardComponent = computed(() => (collapsible ? CollapsibleCard : BCard))
</script>
