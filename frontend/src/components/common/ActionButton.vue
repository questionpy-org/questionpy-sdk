<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BPopover :body="label" teleport-to="body">
        <template #target>
            <BButton
                :aria-label="label"
                class="d-flex gap-2 align-items-center p-1"
                v-bind="{ ...buttonProps, ...$attrs }"
            >
                <component :is="iconComponent" />
            </BButton>
        </template>
    </BPopover>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { BButtonProps } from 'bootstrap-vue-next'
import type { Component } from 'vue'

const props = defineProps<
    BButtonProps & {
        iconComponent?: Component
        label: string
    }
>()

const buttonProps = computed(() => {
    const { iconComponent, label, ...rest } = props
    return rest
})
</script>
