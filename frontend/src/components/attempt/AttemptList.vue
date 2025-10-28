<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <LoadingIndicator v-if="asyncStatus === 'loading'" />
    <ErrorCard v-if="error" :error="error" />
    <CollapsibleCard v-else expanded>
        <template #button-title>Saved attempts ({{ attemptCount }})</template>
        <div
            v-for="[attemptId, attemptData] in Object.entries(attempts)"
            :class="['attempt-card-wrapper', { highlight: highlightedIds.has(attemptId) }]"
            :key="attemptId"
            :ref="registerElementRef(attemptId)"
        >
            <AttemptCard
                :id="`attempt-${questionId}-${attemptId}`"
                :question-id="questionId"
                :attempt-id="attemptId"
                :attempt-data="attemptData"
            />
        </div>
        <BAlert v-if="attemptCount === 0" :model-value="true" class="mb-0" variant="info"
            >This question has no attempts yet.</BAlert
        >
    </CollapsibleCard>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { useDeferredItem, useHintItem } from '@/composables/common'
import { useAttemptListQuery } from '@/queries'

const { questionId } = defineProps<{ questionId: string }>()

const { asyncStatus, error, data: listData } = useAttemptListQuery(questionId)

const attempts = computed(() => listData.value ?? {})
const attemptCount = computed(() => Object.keys(attempts.value).length)

const { highlightedIds, hintItem, registerElementRef } = useHintItem()
useDeferredItem('attempt', attempts, hintItem)
</script>

<style lang="scss" scoped>
.attempt-card-wrapper {
    border-radius: var(--bs-border-radius);
    margin-bottom: $spacer;

    &:last-of-type {
        margin-bottom: 0;
    }

    &.highlight {
        @include highlight-pulse;
    }
}
</style>
