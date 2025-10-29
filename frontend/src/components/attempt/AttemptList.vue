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
            :items="attempts"
            text-empty="This question has no attempts yet."
            title="Saved attempts"
            deferred-item-model="attempt"
        >
            <template #item="{ item, id }">
                <AttemptCard
                    :id="`attempt-${questionId}-${id}`"
                    :question-id="questionId"
                    :attempt-id="id"
                    :attempt-data="item as AttemptData"
                />
            </template>
        </ListView>
    </LoadingIndicator>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import AttemptCard from '@/components/attempt/AttemptCard.vue'
import { useAttemptListQuery } from '@/queries'
import type { AttemptData } from '@/types'

const { questionId } = defineProps<{ questionId: string }>()

const { error, data: listData, isPending } = useAttemptListQuery(questionId)
const attempts = computed(() => listData.value ?? {})
</script>
