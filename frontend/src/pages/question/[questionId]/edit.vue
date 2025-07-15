<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <QuestionOptions :questionId="params.questionId" />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const { params } = useRoute('question-edit')
</script>

<route lang="json">
{
    "name": "question-edit",
    "meta": { "title": "Edit Question" }
}
</route>
