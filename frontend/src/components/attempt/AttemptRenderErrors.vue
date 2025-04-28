<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <CollapseCard expanded variant="danger" v-if="typedEntries.length > 0">
        <template #button-title>Render errors</template>
        <template v-for="[key, errors] in typedEntries" :key="key">
            <h4>{{ categoryTitle(key) }}</h4>
            <BTableSimple class="mb-0 table-bg">
                <BThead>
                    <BTr>
                        <BTh>Line</BTh>
                        <BTh>Type</BTh>
                        <BTh>Message</BTh>
                    </BTr>
                </BThead>
                <BTbody>
                    <BTr v-for="(error, index) in errors" :key="index">
                        <BTd>{{ error.line }}</BTd>
                        <BTd>{{ error.type }}</BTd>
                        <BTd>{{ error.message }}</BTd>
                    </BTr>
                </BTbody>
            </BTableSimple>
        </template>
    </CollapseCard>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed } from 'vue'

import useAttemptStore from '@/stores/useAttemptStore'
import { assertNever } from '@/utils'
import type { RenderError, RenderErrorCategory } from '@/schema/attempt'

const { renderErrors } = storeToRefs(useAttemptStore())

const typedEntries = computed(() => Object.entries(renderErrors.value) as [RenderErrorCategory, RenderError[]][])

function categoryTitle(key: RenderErrorCategory): string {
    switch (key) {
        case 'formulation':
            return 'Formulation'
        case 'general_feedback':
            return 'General feedback'
        case 'specific_feedback':
            return 'Specific feedback'
        case 'right_answer':
            return 'Right answer'
        default:
            assertNever(key)
    }
}
</script>

<style lang="scss" scoped>
@include color-mode(dark) {
    .table-bg {
        --bs-table-bg: rgba(255, 255, 255, 0.08);
        --bs-table-border-color: rgba(0, 0, 0, 0.3);
    }
}
@include color-mode(light) {
    .table-bg {
        --bs-table-bg: rgba(255, 255, 255, 0.4);
        --bs-table-border-color: rgba(0, 0, 0, 0.1);
    }
}
</style>
