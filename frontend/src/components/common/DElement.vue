<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <dt class="col-sm-3 text-nowrap">{{ term }}</dt>
    <dd class="col-sm-9"><slot /></dd>
</template>

<script lang="ts" setup>
defineProps<{
    term: string
}>()
</script>
