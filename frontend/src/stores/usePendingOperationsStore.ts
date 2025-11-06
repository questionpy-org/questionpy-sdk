/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import { computed, reactive } from 'vue'

/** A form submit operation. */
interface SubmitOperation {
    type: 'submit'
    modelType: OperationModelType
}

/** An attempt score operation. */
interface ScoreOperation {
    type: 'score'
}

/** A delete operation. */
interface DeleteOperation {
    type: 'delete'
    modelType: OperationModelType
}

/** A cloning operation. */
interface CloneOperation {
    type: 'clone'
    modelType: OperationModelType
}

/**
 * Deferred operation for an item that will appear asynchronously.
 * Can be processed once the item exists.
 */
interface DeferredItemOperation {
    type: 'deferred-item'
    modelType: OperationModelType
    id: string
}

/** A file upload operation. */
interface FileUploadOperation {
    type: 'file-upload'
}

type OperationModelType = 'attempt' | 'question'
type OperationType = Operation['type']
type Operation =
    | SubmitOperation
    | ScoreOperation
    | DeleteOperation
    | CloneOperation
    | DeferredItemOperation
    | FileUploadOperation

type ExtractOperation<K extends OperationType> = Extract<Operation, { type: K }>

/**
 * Store for managing pending background operations that may affect multiple components
 * or persist across page navigation.
 *
 * Tracks operations such as cloning items or deferred items, allowing components to react
 * to ongoing or future operations and maintain consistent UI state.
 */
const usePendingOperationsStore = defineStore('pendingOperations', () => {
    const operations = reactive<Operation[]>([])

    function getOperationsByType<K extends OperationType>(type: K) {
        return operations.filter((op): op is ExtractOperation<K> => op.type === type)
    }

    function addOperation<K extends OperationType>(
        type: K,
        opts: Omit<ExtractOperation<K>, 'type'> = {} as ExtractOperation<K>,
    ): ExtractOperation<K> {
        const op = { type, ...opts } as ExtractOperation<K>
        operations.push(op)
        return op
    }

    function removeOperation(op: Operation) {
        const index = operations.indexOf(op)
        return operations.splice(index, 1)
    }

    const hasPendingOperations = computed(() => operations.length > 0)

    return {
        operations,
        getOperationsByType,
        addOperation,
        removeOperation,
        hasPendingOperations,
    }
})

export type { OperationModelType }
export default usePendingOperationsStore
