<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div>
        <LoadingIndicator v-if="asyncStatus === 'loading'" />
        <ErrorCard v-if="state.error" :error="state.error" />
        <CollapsibleCard variant="success" v-else-if="manifest" expanded>
            <BContainer class="px-0" fluid>
                <BRow>
                    <BCol class="mb-3" md="3">
                        <BCardImg :src="manifest.iconSrc" alt="Package logo" class="rounded-0 card-image" />
                    </BCol>
                    <BCol md="9" cols="12">
                        <BCardTitle>{{ manifest.name }}</BCardTitle>
                        <BCardSubtitle text-variant="secondary">{{ manifest.packageIdentifier }}</BCardSubtitle>
                        <BCardText class="d-flex flex-wrap gap-4">
                            <dl class="row mb-0">
                                <DElement term="Author">{{ manifest.author }}</DElement>
                                <DElement term="Description" v-if="manifest.description">
                                    {{ manifest.description }}
                                </DElement>
                                <DElement term="Version">{{ manifest.version }}</DElement>
                                <DElement term="API version">{{ manifest.api_version }}</DElement>
                                <DElement term="Languages">{{ manifest.languages }}</DElement>
                                <DElement term="URL" v-if="manifest.url">
                                    <BLink :href="manifest.url" target="_blank" rel="noopener">{{
                                        manifest.url
                                    }}</BLink>
                                </DElement>
                                <DElement term="License" v-if="manifest.license">
                                    {{ manifest.license }}
                                </DElement>
                            </dl>
                        </BCardText>
                    </BCol>
                </BRow>
            </BContainer>
            <template #button-title="{ expanded }">
                <div class="d-flex gap-2 align-items-center">
                    <div class="fs-4 me-2 flex-shrink-0">📦️</div>
                    <div :class="['fw-bold me-auto fs-5 text-truncate', { 'd-none d-md-block': !expanded }]">
                        Loaded package
                    </div>
                    <div class="fs-5 text-truncate" v-if="!expanded">{{ manifest.name }}</div>
                    <div class="pkg-id font-monospace fs-6 text-truncate" v-if="!expanded">
                        {{ manifest.packageIdentifier }}
                    </div>
                </div>
            </template>
        </CollapsibleCard>
    </div>
</template>

<script lang="ts" setup>
import { useManifestQuery } from '@/queries'

const { asyncStatus, manifest, state } = useManifestQuery()
</script>

<style lang="scss" scoped>
.card-image {
    min-width: 5rem;
    max-height: 30rem;
    object-fit: contain;
}

.color-muted {
    color: $gray-200;
}

.pkg-id {
    color: $gray-200;
    /* compensate font size difference */
    margin-top: 4px;
}
</style>
