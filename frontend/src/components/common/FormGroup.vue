<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BFormGroup :disabled="hasPendingOperations" class="mb-3" label-cols-sm="3" content-cols-sm="9">
        <slot />
    </BFormGroup>
</template>

<script lang="ts" setup>
import { storeToRefs } from 'pinia'

import usePendingOperationsStore from '@/stores/usePendingOperationsStore'

const { hasPendingOperations } = storeToRefs(usePendingOperationsStore())
</script>
