<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <LoadingIndicator :loading="isPending">
        <ErrorCard v-if="error" :error="error" />
        <ListView
            v-else
            :items="questions"
            text-empty="This package has no questions yet."
            title="Saved questions"
            deferred-item-model="question"
        >
            <template #prepend-list v-if="hasInvalidStates">
                <InvalidQuestionStateError class="mb-3" />
            </template>
            <template #item="{ item, id }">
                <QuestionCard :id="`question-${id}`" :question-id="id" v-bind="item as QuestionItem" />
            </template>
        </ListView>
    </LoadingIndicator>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { useQuestionStatesQuery } from '@/queries'
import { isDetailedServerError } from '@/types'
import type { DetailedServerError, OptionsFormData } from '@/types'

const { error, data, isPending } = useQuestionStatesQuery()

interface QuestionItem {
    data?: OptionsFormData
    error?: DetailedServerError
}

const questions = computed(() => {
    if (data.value === undefined) {
        return {}
    }
    const entries: [string, QuestionItem][] = Object.entries(data.value).map(([questionId, value]) => [
        questionId,
        isDetailedServerError(value) ? { error: value } : { data: value },
    ])
    return Object.fromEntries(entries)
})

const hasInvalidStates = computed(() => Object.values(questions.value).some((q) => q.error))
</script>
