<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <slot :name="slotName" v-bind="slotProps"></slot>
</template>

<script setup lang="ts">
import { computed, onErrorCaptured, ref } from 'vue'

const error = ref<Error | null>(null)

onErrorCaptured((err) => {
    error.value = err
    console.error(err)

    // Pevent error from bubbling up
    return false
})

function reset() {
    error.value = null
}

const slotProps = computed(() => (error.value ? { error: error.value, reset } : ({} as Record<string, never>)))
const slotName = computed(() => (error.value ? 'error' : 'default'))
</script>
