<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <CollapseCard expanded variant="info">
        <template #button-title>Current attempt</template>
        <BContainer class="p-0" fluid>
            <BRow class="mb-3">
                <BCol>Attempt status</BCol>
                <BCol class="fw-bold">{{ displayStatus }}</BCol>
            </BRow>
            <BRow class="mb-3">
                <BCol>Variant</BCol>
                <BCol class="fw-bold">{{ variant }}</BCol>
            </BRow>
            <BRow class="mb-3">
                <BCol>Attempt state</BCol>
                <BCol>
                    <div class="bg-body-secondary border rounded-1 p-2">
                        <pre class="mb-0"><code>{{ attemptState }}</code></pre>
                    </div>
                </BCol>
            </BRow>
            <BRow class="mb-3">
                <BCol>Storage location</BCol>
                <BCol class="fw-bold"></BCol>
            </BRow>
            <template v-if="isScored">
                <BRow class="mb-3">
                    <BCol>Scoring code</BCol>
                    <BCol class="fw-bold">{{ scoringCode }}</BCol>
                </BRow>
                <BRow class="mb-3">
                    <BCol>Score</BCol>
                    <BCol class="fw-bold">{{ displayScore }}</BCol>
                </BRow>
                <BRow class="mb-3">
                    <BCol>Scoring state</BCol>
                    <BCol>
                        <div class="bg-body-secondary border rounded-1 p-2" v-if="scoringState">
                            <pre class="mb-0"><code>{{ scoringState }}</code></pre>
                        </div>
                    </BCol>
                </BRow>
                <BRow class="mb-3">
                    <BCol>Scoring state files</BCol>
                    <BCol class="fw-bold"></BCol>
                </BRow>
            </template>
        </BContainer>
    </CollapseCard>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'

import useAttemptStore from '@/stores/useAttemptStore'

const { attemptState, displayScore, displayStatus, isScored, scoringCode, scoringState, variant } =
    storeToRefs(useAttemptStore())
</script>
