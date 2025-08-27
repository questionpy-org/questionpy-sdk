<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BAlert :model-value="true" variant="warning">
        The package could not parse one or more question states. If you renamed or added required fields, delete the
        existing states and create a new question. Otherwise, this may be a bug in the package.
    </BAlert>
    <ButtonGroup>
        <IconButton @click="deleteQuestionStates" :icon-component="IMdiDelete" variant="danger" size="sm"
            >Delete question states</IconButton
        ></ButtonGroup
    >
</template>

<script lang="ts" setup>
import IMdiDelete from '~icons/mdi/delete'

import { useDeleteAllQuestions } from '@/composables/question'

const deleteQuestionStates = useDeleteAllQuestions()
</script>
