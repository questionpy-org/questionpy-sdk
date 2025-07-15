<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div>
        <BCollapse v-model="expanded">
            <template #header="{ id, toggle }">
                <BButton
                    :class="['fs-4 d-flex align-items-center w-100', { expanded }]"
                    @click="toggle"
                    :aria-controls="id"
                    :aria-expanded="expanded"
                    :variant="variant"
                >
                    <div class="flex-grow-1 text-start text-truncate pe-2">
                        <slot name="button-title" :expanded />
                    </div>
                    <i-mdi-chevron-up :class="['fs-3 collapse-icon', { collapsed: !expanded }]" />
                </BButton>
            </template>
            <BCard no-body :class="['card', 'overflow-hidden', cardTextCls]" :variant="variant">
                <BCardBody :bg-variant="cardBgVariant">
                    <slot />
                </BCardBody>
            </BCard>
        </BCollapse>
    </div>
</template>

<script lang="ts" setup>
import { storeToRefs } from 'pinia'
import { computed, ref } from 'vue'
import type { ColorExtendables, ColorVariant } from 'bootstrap-vue-next'

import useAppStateStore from '@/stores/useAppStateStore'

const { colorMode } = storeToRefs(useAppStateStore())

const { expanded: initialExpanded = false, variant } = defineProps<{
    expanded?: boolean
    variant?: ColorVariant
}>()

const expanded = ref(initialExpanded)

const cardBgVariant = computed(() => (variant ? `${variant}-subtle` : null) as ColorExtendables['bgVariant'])
const cardTextCls = computed(() => (colorMode.value === 'dark' ? 'text-light' : 'text-dark'))
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
