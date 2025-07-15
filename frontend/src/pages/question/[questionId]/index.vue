<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <IconButton :to="{ name: 'index' }" :icon-component="IMdiArrowLeft" class="ps-0 mb-2" variant="link"
        >Back to Package Preview</IconButton
    >
    <QuestionCard class="mb-3" :question-id="params.questionId" :form-data="formData?.data ?? {}" />
    <ButtonGroup class="mb-4">
        <IconButton :icon-component="IMdiImport" variant="link" @click="importAttempt">Import attempt</IconButton>
        <IconButton :icon-component="IMdiAdd" @click="createAttempt" variant="primary">New attempt</IconButton>
    </ButtonGroup>
    <AttemptList :question-id="params.questionId" />
</template>

<script setup lang="ts">
import IMdiAdd from '~icons/mdi/add'
import IMdiArrowLeft from '~icons/mdi/arrow-left'
import IMdiImport from '~icons/mdi/import'
import { watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useCreateAttempt } from '@/composables/attempt'
import { useOptionsFormDataQuery } from '@/queries'

const route = useRouter()
const { params } = useRoute('question')
const { data: formData } = useOptionsFormDataQuery(params.questionId)
const createAttempt = useCreateAttempt(params.questionId)

// If question doesn't exist, show index instead
watch(
    formData,
    (value) => {
        if (value?.is_new) {
            route.replace({ name: 'index' })
        }
    },
    { immediate: true },
)

function importAttempt() {
    // TODO: import question
}
</script>

<route lang="json">
{
    "name": "question",
    "meta": { "title": "Question Preview" }
}
</route>
