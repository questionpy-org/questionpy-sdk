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
        <BCardText>
            <ErrorDisplay :error="error" />
        </BCardText>
        <BButton v-if="reset" @click="reset">Reset error</BButton>
    </BCard>
</template>

<script lang="ts" setup>
defineProps<{
    error: Error
    reset?: () => void
}>()
</script>
