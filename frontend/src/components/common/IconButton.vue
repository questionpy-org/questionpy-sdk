<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BButton class="d-flex text-nowrap gap-2 align-items-center" v-bind="buttonProps">
        <component :is="iconComponent" />
        <slot />
    </BButton>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { BButtonProps } from 'bootstrap-vue-next'
import type { Component } from 'vue'

const props = defineProps<
    BButtonProps & {
        iconComponent?: Component
    }
>()

const buttonProps = computed(() => {
    const { iconComponent, ...rest } = props
    return rest
})
</script>
