<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BFormInvalidFeedback v-if="validation.text" :state="validation.state">{{ validation.text }}</BFormInvalidFeedback>
</template>

<script lang="ts" setup>
import type { ValidationInfo } from '@/types'

defineProps<{ validation: ValidationInfo }>()
</script>
