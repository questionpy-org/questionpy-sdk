<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BCard
        :header="error.name"
        border-variant="danger"
        header-border-variant="danger"
        header-text-variant="danger"
        class="mb-4"
    >
        <BCardText v-if="error instanceof FetchError" class="font-monospace">
            {{ error.message }} ({{ error.status }}: {{ error.statusText }})
        </BCardText>
        <BCardText v-else-if="error instanceof z.ZodError">
            <BListGroup>
                <BListGroupItem v-for="(issue, index) in error.issues" :key="index" class="font-monospace">
                    {{ fromZodIssue(issue) }}
                </BListGroupItem>
            </BListGroup>
        </BCardText>
        <BCardText v-else class="font-monospace">
            {{ error.message }}
        </BCardText>
    </BCard>
</template>

<script lang="ts" setup>
import { z } from 'zod'
import { fromZodIssue } from 'zod-validation-error'

import { FetchError } from '@/queries/fetch'

defineProps<{ error: Error }>()
</script>
