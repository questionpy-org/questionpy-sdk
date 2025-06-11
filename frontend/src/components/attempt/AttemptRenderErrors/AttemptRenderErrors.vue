<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <CollapseCard expanded variant="danger" v-if="renderErrorsEntries.length > 0">
        <template #button-title>Render errors</template>
        <div v-for="[key, errors] in renderErrorsEntries" :key="key" class="table-wrapper">
            <h5>
                {{ errors.length }} error{{ errors.length > 1 ? 's' : '' }} occurred while rendering
                {{ categoryTitle(key as ErrorSectionKey) }}
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
    </CollapseCard>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed } from 'vue'

import useAttemptStore from '@/stores/useAttemptStore'
import { assertNever, type ErrorSectionKey } from '@/types'

const { renderErrors } = storeToRefs(useAttemptStore())

const renderErrorsEntries = computed(() => Object.entries(renderErrors.value))

function categoryTitle(key: ErrorSectionKey): string {
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
