<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <CollapsibleCard expanded>
        <template #button-title>
            <div class="d-flex gap-2 align-items-center">
                <IMdiFormatListBulleted class="flex-shrink-0 me-2" />
                <div class="text-truncate">{{ title }} ({{ itemCount }})</div>
            </div>
        </template>
        <slot name="prepend-list" />
        <div v-if="itemCount > 0" class="vstack gap-3">
            <div
                v-for="[id, item] in Object.entries(items)"
                :class="['item-wrapper', { highlight: highlightedIds.has(id) }]"
                :key="id"
                :ref="registerElementRef(id)"
            >
                <slot name="item" :item="item" :id="id" />
            </div>
        </div>
        <BAlert v-else :model-value="true" class="mb-0" variant="info">{{ textEmpty }}</BAlert>
    </CollapsibleCard>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { useDeferredItem, useHintItem } from '@/composables/common'
import type { OperationModelType } from '@/stores/usePendingOperationsStore'

const { items, deferredItemModel } = defineProps<{
    items: Record<string, object>
    textEmpty: string
    title: string
    deferredItemModel: OperationModelType
}>()

const itemCount = computed(() => Object.keys(items).length)

const { highlightedIds, hintItem, registerElementRef } = useHintItem()
useDeferredItem(deferredItemModel, () => items, hintItem)
</script>

<style lang="scss" scoped>
.item-wrapper {
    border-radius: var(--bs-border-radius); // for highlight effect

    &.highlight {
        @include highlight-pulse;
    }
}
</style>
