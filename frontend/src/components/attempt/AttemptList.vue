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
        <AttemptCard
            v-for="[attemptId, attemptData] in Object.entries(attempts)"
            class="attempt-card"
            :id="`attempt-${questionId}-${attemptId}`"
            :key="attemptId"
            :question-id="questionId"
            :attempt-id="attemptId"
            :attempt-data="attemptData"
        />
        <BAlert v-if="attemptCount === 0" :model-value="true" class="mb-0" variant="info"
            >This question has no attempts yet.</BAlert
        >
    </CollapsibleCard>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { useAttemptListQuery } from '@/queries'

const { questionId } = defineProps<{ questionId: string }>()

const { asyncStatus, error, data: listData } = useAttemptListQuery(questionId)

const attempts = computed(() => listData.value ?? {})
const attemptCount = computed(() => Object.keys(attempts.value).length)
</script>

<style lang="scss" scoped>
.attempt-card {
    margin-bottom: $spacer;

    &:last-of-type {
        margin-bottom: 0;
    }
}
</style>
