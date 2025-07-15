<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <CollapsibleCard expanded variant="secondary">
        <template #button-title>Display options</template>
        <BContainer class="px-0" fluid>
            <BRow>
                <BCol>
                    <BFormGroup label="Show">
                        <BFormCheckbox v-model="displayOptions.general_feedback">General feedback</BFormCheckbox>
                        <BFormCheckbox v-model="displayOptions.specific_feedback">Specific feedback</BFormCheckbox>
                        <BFormCheckbox v-model="displayOptions.right_answer">Right answer</BFormCheckbox>
                        <BFormCheckbox v-model="displayOptions.correctness">Correctness</BFormCheckbox>
                    </BFormGroup>
                </BCol>
                <BCol>
                    <BFormGroup label="Roles">
                        <BFormCheckboxGroup v-model="displayOptions.roles" :options="roleOptions" stacked />
                    </BFormGroup>
                </BCol>
            </BRow>
        </BContainer>
    </CollapsibleCard>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'

import useDisplayOptionsStore from '@/stores/useDisplayOptionsStore'
import type { DisplayRole } from '@/types'

interface RoleOption {
    text: string
    value: DisplayRole
}

const { displayOptions } = storeToRefs(useDisplayOptionsStore())

const roleOptions = [
    { text: 'Developer', value: 'DEVELOPER' },
    { text: 'Proctor', value: 'PROCTOR' },
    { text: 'Scorer', value: 'SCORER' },
    { text: 'Teacher', value: 'TEACHER' },
] satisfies RoleOption[]
</script>
