<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div v-bind="wrapperProps">
        <BPlaceholderWrapper :loading="loading">
            <template #loading>
                <BPlaceholderCard animation="wave" no-button no-footer no-img />
            </template>
            <slot />
        </BPlaceholderWrapper>
    </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { BPlaceholderWrapperProps } from 'bootstrap-vue-next'

const props = defineProps<BPlaceholderWrapperProps>()

const wrapperProps = computed(() => {
    const { loading, ...rest } = props
    return rest
})
</script>
