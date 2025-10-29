<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <IconButton :icon-component="IMdiArrowLeft" :to="to" class="link ps-0" variant="link"><slot /></IconButton>
</template>

<script setup lang="ts">
import IMdiArrowLeft from '~icons/mdi/arrow-left'
import type { RouteLocationRaw } from 'vue-router'

defineProps<{
    to: RouteLocationRaw
}>()
</script>

<style lang="scss" scoped>
.link {
    margin-bottom: -$spacer;
}
</style>
