<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <LoadingIndicator :loading="isPending">
        <ErrorCard v-if="error" :error="error" />
        <CollapsibleCard v-else expanded>
            <template #button-title>
                <div class="d-flex gap-2 align-items-center">
                    <IMdiFormatListBulleted class="flex-shrink-0 me-2" />
                    <div class="text-truncate">Saved questions ({{ questionCount }})</div>
                </div>
            </template>
            <InvalidQuestionStateError v-if="hasInvalidStates" class="mb-3" />
            <div class="vstack gap-3">
                <div
                    v-for="[questionId, question] in Object.entries(questions)"
                    :class="['question-card-wrapper', { highlight: highlightedIds.has(questionId) }]"
                    :key="questionId"
                    :ref="registerElementRef(questionId)"
                >
                    <QuestionCard
                        :id="`question-${questionId}`"
                        :questionId="questionId"
                        :data="question.data"
                        :error="question.error"
                    />
                </div>
            </div>
            <BAlert v-if="questionCount === 0" :model-value="true" class="mb-0" variant="info"
                >This package has no questions yet.</BAlert
            >
        </CollapsibleCard>
    </LoadingIndicator>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { useDeferredItem, useHintItem } from '@/composables/common'
import { useQuestionStatesQuery } from '@/queries'
import { isDetailedServerError } from '@/types'
import type { DetailedServerError, OptionsFormData } from '@/types'

const { error, data, isPending } = useQuestionStatesQuery()

const questions = computed<Record<string, { data?: OptionsFormData; error?: DetailedServerError }>>(() => {
    if (data.value === undefined) {
        return {}
    }
    const entries = Object.entries(data.value).map(([questionId, value]) => [
        questionId,
        isDetailedServerError(value) ? { data: undefined, error: value } : { data: value, error: undefined },
    ])
    return Object.fromEntries(entries)
})

const questionCount = computed(() => Object.keys(questions.value).length)
const hasInvalidStates = computed(() => Object.values(questions.value).some((q) => q.error))

const { highlightedIds, hintItem, registerElementRef } = useHintItem()
useDeferredItem('question', questions, hintItem)
</script>

<style lang="scss" scoped>
.question-card-wrapper {
    border-radius: var(--bs-border-radius);

    &.highlight {
        @include highlight-pulse;
    }
}
</style>
