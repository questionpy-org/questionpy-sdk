<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div class="mb-4">
        <BCollapse v-model="expanded">
            <template #header="{ id, toggle }">
                <BButton
                    :class="['d-flex align-items-center w-100', { expanded }]"
                    @click="toggle"
                    :aria-controls="id"
                    :aria-expanded="expanded"
                >
                    <div class="flex-grow-1 text-start text-truncate pe-2">
                        <slot name="button-title" :expanded />
                    </div>
                    <i-mdi-chevron-up :class="['fs-3 collapse-icon', { collapsed: !expanded }]" />
                </BButton>
            </template>
            <BCard no-body class="card overflow-hidden">
                <slot />
            </BCard>
        </BCollapse>
    </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'

const { expanded: initialExpanded = false } = defineProps<{
    expanded?: boolean
}>()

const expanded = ref(initialExpanded)
</script>

<style lang="scss" scoped>
.expanded {
    border-bottom-right-radius: 0;
    border-bottom-left-radius: 0;
    transition: border-radius 0.35s ease-out;
}

.card {
    border-top: none;
    border-top-left-radius: 0;
    border-top-right-radius: 0;
}

.collapse-icon {
    @include transition($transition-base);

    transform: rotateZ(0deg);
    transform-origin: center;

    &.collapsed {
        transform: rotateZ(180deg);
    }
}
</style>
