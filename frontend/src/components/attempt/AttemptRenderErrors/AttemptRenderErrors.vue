<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <CollapsibleCard expanded variant="danger" v-if="renderErrorsEntries.length > 0">
        <template #button-title>Render errors</template>
        <div v-for="[key, errors] in renderErrorsEntries" :key="key" class="table-wrapper">
            <h5>
                {{ errors.length }} error{{ errors.length > 1 ? 's' : '' }} occurred while rendering
                {{ categoryTitle(key) }}
            </h5>
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
                        <BTd
                            ><samp>{{ error.type }}</samp></BTd
                        >
                        <BTd><ErrorTemplate :template="error.template" :values="error.template_kwargs" /></BTd>
                    </BTr>
                </BTbody>
            </BTableSimple>
        </div>
    </CollapsibleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { assertNever } from '@/types'
import type { ErrorSectionKey, SectionErrorMap } from '@/types'

const { renderErrors } = defineProps<{ renderErrors: SectionErrorMap }>()

const renderErrorsEntries = computed(() => Object.entries(renderErrors ?? {}))

function categoryTitle(strKey: string): string {
    const key = strKey as ErrorSectionKey // Cast since auto-translated types are imprecise
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

.table-wrapper {
    margin-bottom: $spacer * 1.5;

    &:last-of-type {
        margin-bottom: 0;
    }
}
</style>
