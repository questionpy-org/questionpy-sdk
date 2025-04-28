<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <CollapseCard expanded variant="secondary">
        <template #button-title>Display options</template>
        <BContainer class="px-0" fluid>
            <BRow>
                <BCol>
                    <BFormGroup label="Show">
                        <BFormCheckbox v-model="displayOptions.generalFeedback">General feedback</BFormCheckbox>
                        <BFormCheckbox v-model="displayOptions.specificFeedback">Specific feedback</BFormCheckbox>
                        <BFormCheckbox v-model="displayOptions.rightAnswer">Right answer</BFormCheckbox>
                    </BFormGroup>
                </BCol>
                <BCol>
                    <BFormGroup label="Roles">
                        <BFormCheckboxGroup v-model="rolesModel" :options="roleOptions" stacked />
                    </BFormGroup>
                </BCol>
            </BRow>
        </BContainer>
    </CollapseCard>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed } from 'vue'

import useDisplayOptionsStore from '@/stores/useDisplayOptionsStore'

const { displayOptions } = storeToRefs(useDisplayOptionsStore())

const roleOptions = [
    { text: 'Developer', value: 'DEVELOPER' },
    { text: 'Proctor', value: 'PROCTOR' },
    { text: 'Scorer', value: 'SCORER' },
    { text: 'Teacher', value: 'TEACHER' },
]

const rolesModel = computed({
    get() {
        return Array.from(displayOptions.value.roles)
    },
    set(newRoles) {
        displayOptions.value.roles = new Set(newRoles)
    },
})
</script>
