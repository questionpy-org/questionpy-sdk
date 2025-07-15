<!--
    This file is part of the QuestionPy SDK. (https://questionpy.org)
    The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
    (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BCard :variant="cardVariant">
        <BCardText>
            <!-- TODO: Show Question -->
            <pre>{{ formData }}</pre>
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

import useDeleteQuestion from '@/composables/question/useDeleteQuestion'
import useAppStateStore from '@/stores/useAppStateStore'
import type { OptionsFormData } from '@/types'

const { questionId } = defineProps<{
    questionId: string
    formData: OptionsFormData
}>()

const questionLocation = { name: 'question', params: { questionId } } as const

const { colorMode } = storeToRefs(useAppStateStore())
const deleteQuestion = useDeleteQuestion(questionId)
const { isActive: isCurrentPreviewActive } = useLink({ to: questionLocation })

const cardVariant = computed(() => (colorMode.value === 'dark' ? 'dark' : 'light'))
</script>
