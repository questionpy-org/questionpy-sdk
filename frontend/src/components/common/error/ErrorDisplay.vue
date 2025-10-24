<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <template v-if="fetchError">
        <h5>{{ fetchError.message }} ({{ fetchError.status }}: {{ fetchError.statusText }})</h5>
        <h6>Stacktrace</h6>
        <code v-if="typeof fetchError.details === 'string'">
            <pre>{{ fetchError.details }}</pre>
        </code>
        <ValidationErrorDetails v-if="Array.isArray(fetchError.details)" :details="fetchError.details" />
    </template>
    <template v-else>
        <h5>{{ error.message }}</h5>
        <code v-if="error.stack">
            <pre class="mb-0">{{ error.stack }}</pre>
        </code>
    </template>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { FetchError } from '@/queries'

const props = defineProps<{ error: Error }>()

const fetchError = computed(() => (props.error instanceof FetchError ? props.error : null))
</script>
