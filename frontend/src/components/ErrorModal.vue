<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BModal body-bg-variant="danger-subtle" header-variant="danger" no-footer v-model="show" @hide="clearError">
        <template #title>{{ error?.name }}</template>
        <ErrorDisplay v-if="error" :error="error" />
    </BModal>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed } from 'vue'

import useAppStateStore from '@/stores/useAppStateStore'

const appStateStore = useAppStateStore()
const { clearError } = appStateStore
const { currentError: error } = storeToRefs(appStateStore)

const show = computed(() => error.value !== null)
</script>
