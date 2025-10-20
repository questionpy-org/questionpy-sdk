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
            :class="['attempt-card', { highlight: highlightedIds.has(attemptId) }]"
            :id="`attempt-${questionId}-${attemptId}`"
            :key="attemptId"
            :question-id="questionId"
            :attempt-id="attemptId"
            :attempt-data="attemptData"
            @cloned="handleAttemptCloned"
        />
        <BAlert v-if="attemptCount === 0" :model-value="true" class="mb-0" variant="info"
            >This question has no attempts yet.</BAlert
        >
    </CollapsibleCard>
</template>

<script lang="ts" setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'

import { useAttemptListQuery } from '@/queries'

const { questionId } = defineProps<{ questionId: string }>()

const { asyncStatus, error, data: listData } = useAttemptListQuery(questionId)

const attempts = computed(() => listData.value ?? {})
const attemptCount = computed(() => Object.keys(attempts.value).length)

const pendingClones = ref<Set<string>>(new Set())
const highlightedIds = ref<Set<string>>(new Set())

onMounted(() => {
    // Handle clones coming in via route navigation
    const hightlightId = history.state?.highlightAttemptId
    if (typeof hightlightId === 'string') {
        pendingClones.value.add(hightlightId)
    }
})

const handleAttemptCloned = (newAttemptId: string) => {
    pendingClones.value.add(newAttemptId)
}

// Watch for pending clones to appear
watch(attempts, async (newAttempts, oldAttempts) => {
    for (const attemptId of pendingClones.value) {
        if (newAttempts[attemptId] && !oldAttempts?.[attemptId]) {
            pendingClones.value.delete(attemptId)
            await nextTick()
            const el = document.getElementById(`attempt-${questionId}-${attemptId}`)
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' })
                setTimeout(() => {
                    highlightedIds.value.add(attemptId)
                    el.addEventListener(
                        'animationend',
                        () => {
                            highlightedIds.value.delete(attemptId)
                        },
                        { once: true },
                    )
                }, 600)
            }
        }
    }
})
</script>

<style lang="scss" scoped>
.attempt-card {
    margin-bottom: $spacer;

    &:last-of-type {
        margin-bottom: 0;
    }

    &.highlight {
        animation: highlight-pulse 1500ms ease-in-out;
    }
}
</style>
