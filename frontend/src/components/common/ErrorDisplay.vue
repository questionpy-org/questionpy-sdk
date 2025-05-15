<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div v-if="error instanceof FetchError" class="font-monospace">
        <p>{{ error.message }} ({{ error.status }}: {{ error.statusText }})</p>
        <code v-if="error.details">
            <pre>{{ error.details }}</pre>
        </code>
    </div>
    <div v-else-if="error instanceof z.ZodError">
        <BListGroup>
            <BListGroupItem v-for="(issue, index) in error.issues" :key="index" class="font-monospace">
                {{ fromZodIssue(issue) }}
            </BListGroupItem>
        </BListGroup>
    </div>
</template>

<script lang="ts" setup>
import { watch } from 'vue'
import { z } from 'zod'
import { fromZodIssue } from 'zod-validation-error'

import { FetchError } from '@/queries/fetch'

const props = defineProps<{ error: Error }>()

watch(
    () => props.error,
    (error) => {
        if (!(error instanceof FetchError || error instanceof z.ZodError)) {
            throw error
        }
    },
    { immediate: true },
)
</script>
