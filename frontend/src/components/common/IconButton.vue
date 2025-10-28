<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BButton :disabled="disabled" class="d-flex text-nowrap gap-2 align-items-center" v-bind="buttonProps">
        <component :is="iconComponent" />
        <slot />
    </BButton>
</template>

<script lang="ts" setup>
import { storeToRefs } from 'pinia'
import { computed } from 'vue'
import type { BButtonProps } from 'bootstrap-vue-next'
import type { Component } from 'vue'

import usePendingOperationsStore from '@/stores/usePendingOperationsStore'

const { hasPendingOperations } = storeToRefs(usePendingOperationsStore())

const props = defineProps<
    BButtonProps & {
        iconComponent?: Component
    }
>()

const buttonProps = computed(() => {
    const { iconComponent, disabled, ...rest } = props
    return rest
})

const disabled = computed(() => props.disabled || hasPendingOperations.value)
</script>
