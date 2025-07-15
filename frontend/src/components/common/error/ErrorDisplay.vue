<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <h5>{{ fetchError.message }} ({{ fetchError.status }}: {{ fetchError.statusText }})</h5>
    <code v-if="typeof fetchError.details === 'string'">
        <pre>{{ fetchError.details }}</pre>
    </code>
    <ValidationErrorDetails v-if="Array.isArray(fetchError.details)" :details="fetchError.details" />
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { FetchError } from '@/queries'

const props = defineProps<{ error: Error }>()

const fetchError = computed(() => {
    // The component only deals with FetchError
    if (!(props.error instanceof FetchError)) {
        throw props.error
    }
    return props.error
})
</script>
