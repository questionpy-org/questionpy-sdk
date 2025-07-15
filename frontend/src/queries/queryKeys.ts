/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import type { ClientQuestionDisplayOptions } from '@/types'

/** Query cache keys. */
const QUERY_KEYS = {
    package: {
        root: ['package'],
        manifest: () => [...QUERY_KEYS.package.root, 'manifest'],
    },
    question: {
        root: ['question'],
        list: () => [...QUERY_KEYS.question.root, 'list'],
        formDefinitionById: (questionId: string) => [...QUERY_KEYS.question.root, questionId, 'form-definition'],
        stateById: (questionId: string) => [...QUERY_KEYS.question.root, questionId, 'state'],
    },
    attempt: {
        root: ['attempt'],
        list: (questionId: string) => [...QUERY_KEYS.attempt.root, 'list', questionId],
        byQuestionId: (questionId: string) => [...QUERY_KEYS.attempt.root, questionId],
        byId: (questionId: string, attemptId: string) => [...QUERY_KEYS.attempt.byQuestionId(questionId), attemptId],
        renderedbyId: (
            questionId: string,
            attemptId: string,
            displayOptions: Readonly<ClientQuestionDisplayOptions>,
        ) => [...QUERY_KEYS.attempt.byId(questionId, attemptId), displayOptions],
    },
} as const

export default QUERY_KEYS
