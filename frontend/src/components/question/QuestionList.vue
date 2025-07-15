<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <LoadingIndicator v-if="asyncStatus === 'loading'" />
    <ErrorCard v-if="error" :error="error" />
    <CollapsibleCard v-else expanded>
        <template #button-title>Saved questions ({{ questionCount }})</template>
        <QuestionCard
            v-for="[questionId, formData] in Object.entries(questions)"
            class="question-card"
            :id="`question-${questionId}`"
            :key="questionId"
            :questionId="questionId"
            :formData="formData"
        />
        <BAlert v-if="questionCount === 0" :model-value="true" class="mb-0" variant="info"
            >This package has no questions yet.</BAlert
        >
    </CollapsibleCard>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { useQuestionStatesQuery } from '@/queries'

const { asyncStatus, error, data } = useQuestionStatesQuery()

const questions = computed(() => data.value ?? {})
const questionCount = computed(() => Object.keys(questions.value).length)
</script>

<style lang="scss" scoped>
.question-card {
    margin-bottom: $spacer;

    &:last-of-type {
        margin-bottom: 0;
    }
}
</style>
