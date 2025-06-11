<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BListGroup>
        <BListGroupItem v-for="(detail, idx) in details" :key="idx" class="flex-column align-items-start">
            <div class="d-flex w-100 justify-content-between">
                <div class="mb-1">
                    Type: <samp>{{ detail.type }}</samp>
                </div>
                <small v-if="detail.url">
                    <BLink :href="detail.url" target="_blank" rel="noopener" variant="secondary">Documentation</BLink>
                </small>
            </div>
            <div class="d-flex w-100 justify-content-between">
                <div class="mb-1">
                    {{ detail.msg }}: <code>{{ detail.input }}</code>
                </div>
                <small>
                    <samp>{{ detail.loc.join(', ') }}</samp>
                </small>
            </div>
        </BListGroupItem>
    </BListGroup>
</template>

<script lang="ts" setup>
import type { ErrorDetails } from '@/types'

defineProps<{ details: ErrorDetails[] }>()
</script>
