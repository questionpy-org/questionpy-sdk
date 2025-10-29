<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BackLink :to="{ name: 'question', params: { questionId: params.questionId } }">Back to Question Preview</BackLink>
    <AttemptPreview :questionId="params.questionId" :attemptId="params.attemptId" />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const { params } = useRoute('question-attempt')
</script>

<route lang="json">
{
    "name": "question-attempt",
    "meta": { "title": "Attempt Preview" }
}
</route>
