<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <PackageCard class="mb-4" />
    <ButtonGroup class="mb-4">
        <IconButton :icon-component="IMdiImport" variant="link" @click="importQuestion">Import question</IconButton>
        <IconButton :icon-component="IMdiAdd" @click="createQuestion" variant="primary">New question</IconButton>
    </ButtonGroup>
    <QuestionList />
</template>

<script lang="ts" setup>
import IMdiAdd from '~icons/mdi/add'
import IMdiImport from '~icons/mdi/import'

import useCreateQuestion from '@/composables/question/useCreateQuestion'

const createQuestion = useCreateQuestion()

function importQuestion() {
    // TODO: import question
}
</script>

<route lang="json">
{
    "name": "index",
    "meta": { "title": "Package preview" }
}
</route>
