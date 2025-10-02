<!--
    This file is part of the QuestionPy SDK. (https://questionpy.org)
    The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
    (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BCard :variant="cardVariant">
        <BCardText>
            <!-- TODO: Show Question -->
            <CollapsibleCard v-if="isDetailedServerError(error)" variant="danger">
                <template #button-title>{{ error.error }}</template>
                <p>The package could not parse the question state.</p>
                <code>
                    <pre>{{ error.details }}</pre>
                </code>
            </CollapsibleCard>
            <pre v-if="data">{{ data }}</pre>
        </BCardText>
        <ButtonGroup>
            <!-- TODO: Implement clone -->
            <IconButton :icon-component="IMdiContentCopy" variant="secondary" size="sm">Clone</IconButton>
            <!-- TODO: Implement export -->
            <IconButton :icon-component="IMdiExport" variant="secondary" size="sm">Export</IconButton>
            <IconButton @click="deleteQuestion" :icon-component="IMdiDelete" variant="danger" size="sm"
                >Delete</IconButton
            >
            <IconButton
                :to="{ name: 'question-edit', params: { questionId } }"
                :icon-component="IMdiPencil"
                variant="warning"
                size="sm"
                >Edit</IconButton
            >
            <IconButton
                v-if="!isCurrentPreviewActive"
                :to="questionLocation"
                :icon-component="IMdiEye"
                variant="primary"
                size="sm"
                >Preview</IconButton
            >
        </ButtonGroup>
    </BCard>
</template>

<script lang="ts" setup>
import IMdiContentCopy from '~icons/mdi/content-copy'
import IMdiDelete from '~icons/mdi/delete'
import IMdiExport from '~icons/mdi/export'
import IMdiEye from '~icons/mdi/eye'
import IMdiPencil from '~icons/mdi/pencil'
import { storeToRefs } from 'pinia'
import { computed } from 'vue'
import { useLink } from 'vue-router'

import { useDeleteQuestion } from '@/composables/question'
import useAppStateStore from '@/stores/useAppStateStore'
import { isDetailedServerError } from '@/types'
import type { DetailedServerError, OptionsFormData } from '@/types'

const { data, questionId } = defineProps<{
    questionId: string
    data?: OptionsFormData
    error?: DetailedServerError
}>()

const questionLocation = { name: 'question', params: { questionId } } as const

const { colorMode } = storeToRefs(useAppStateStore())
const deleteQuestion = useDeleteQuestion(questionId)
const { isActive: isCurrentPreviewActive } = useLink({ to: questionLocation })

const cardVariant = computed(() => (colorMode.value === 'dark' ? 'dark' : 'light'))
</script>
