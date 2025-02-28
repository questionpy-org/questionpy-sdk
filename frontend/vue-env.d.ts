/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

export {}

declare module 'vue-router' {
    // Augment route meta with custom page title property
    export interface RouteMeta {
        title: string
    }
}
