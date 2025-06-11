<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <span>
        <template v-for="(part, index) in parts" :key="index">
            <template v-if="part.type === 'text'">
                {{ part.content }}
            </template>
            <code v-else>{{ part.content }}</code>
        </template>
    </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { TemplateKwargs } from '@/types/AttemptRenderData.generated'

interface Part {
    type: 'text' | 'value'
    content: string
}

const { template, values } = defineProps<{
    template: string
    values: TemplateKwargs
}>()

function formatArray(arrValue: string[]): Part[] {
    const parts: Part[] = []

    if (!arrValue.length) {
        return parts
    }

    const [lastValue, ...restValues] = [...arrValue].reverse()
    restValues.reverse()

    for (let i = 0; i < restValues.length; ++i) {
        parts.push({ type: 'value', content: restValues[i] })
        parts.push({ type: 'text', content: i < restValues.length - 1 ? ', ' : ' and ' })
    }

    parts.push({ type: 'value', content: lastValue })

    return parts
}

const parts = computed(() => {
    const parts: Part[] = []
    let lastIndex = 0

    template.replace(/{(\w+)}/g, (match, key, offset) => {
        if (offset > lastIndex) {
            parts.push({ type: 'text', content: template.slice(lastIndex, offset) })
        }

        const value = values[key]

        if (value === undefined) {
            throw new Error(`Expected value for placeholder '${key}'`)
        }

        if (Array.isArray(value)) {
            parts.push(...formatArray(value))
        } else {
            parts.push({ type: 'value', content: value })
        }

        lastIndex = offset + match.length
        return match
    })

    if (lastIndex < template.length) {
        parts.push({ type: 'text', content: template.slice(lastIndex) })
    }

    return parts
})
</script>
