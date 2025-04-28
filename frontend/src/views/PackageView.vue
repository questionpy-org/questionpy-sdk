<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <PackageCard />
    <h2>Saved questions</h2>
    <ButtonGroup>
        <IconButton :iconComponent="IMdiImport" variant="link" @click="importQuestion">Import question</IconButton>
        <IconButton :iconComponent="IMdiAdd" to="/question" variant="primary">New question</IconButton>
    </ButtonGroup>
</template>

<script lang="ts" setup>
import IMdiAdd from '~icons/mdi/add'
import IMdiImport from '~icons/mdi/import'

function importQuestion() {
    // TODO: import question
}
</script>
