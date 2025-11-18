<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <slot v-if="error" name="error" v-bind="{ error: error, reset }">
        <ErrorCard :error="error" :reset="reset" />
    </slot>
    <slot v-else name="default" />
</template>

<script setup lang="ts">
import { onErrorCaptured, ref } from 'vue'

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
</script>
