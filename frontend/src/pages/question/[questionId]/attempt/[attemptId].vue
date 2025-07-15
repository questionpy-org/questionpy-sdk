<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <IconButton
        :to="{ name: 'question', params: { questionId: params.questionId } }"
        :icon-component="IMdiArrowLeft"
        class="ps-0 mb-2"
        variant="link"
        >Back to Question Preview</IconButton
    >
    <AttemptPreview :questionId="params.questionId" :attemptId="params.attemptId" />
</template>

<script setup lang="ts">
import IMdiArrowLeft from '~icons/mdi/arrow-left'
import { useRoute } from 'vue-router'

const { params } = useRoute('question-attempt')
</script>

<route lang="json">
{
    "name": "question-attempt",
    "meta": { "title": "Attempt Preview" }
}
</route>
