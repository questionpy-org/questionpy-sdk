/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import { computed, onUnmounted } from 'vue'

import {
    useAttemptDataQuery,
    usePostAttemptQuery,
    usePostAttemptRestartQuery,
    usePostAttemptScoreQuery,
} from '@/queries/attempt'
import { usePostOptionsFormDataQuery } from '@/queries/options'

import useAppStateStore from './useAppStateStore'

/** Provides attempt data. */
const useAttemptStore = defineStore('attemptData', () => {
    const { asyncStatus: dataAsyncStatus, state: dataState, refresh: dataRefresh } = useAttemptDataQuery()
    const { asyncStatus: postAsyncStatus, mutateAsync: postAttempt } = usePostAttemptQuery()
    const { asyncStatus: postRestartAsyncStatus, mutateAsync: postRestart } = usePostAttemptRestartQuery()
    const { asyncStatus: postScoreAsyncStatus, mutateAsync: postScore } = usePostAttemptScoreQuery()
    const { onSuccess: onPostOptionsFormDataSuccess } = usePostOptionsFormDataQuery()

    const { setError } = useAppStateStore()

    /** Restarts the attempt. */
    async function restart() {
        try {
            await postRestart()
            await dataRefresh()
        } catch (err) {
            setError(err)
        }
    }

    // Restart attempt when options form data change
    const unsubscribe = onPostOptionsFormDataSuccess(() => {
        restart()
    })
    onUnmounted(() => {
        unsubscribe()
    })

    const isScored = computed(() => typeof dataState.value.data?.scoring_code === 'string')

    return {
        asyncStatus: computed(() =>
            [dataAsyncStatus, postAsyncStatus, postRestartAsyncStatus, postScoreAsyncStatus].every(
                ({ value }) => value === 'idle',
            )
                ? 'idle'
                : 'loading',
        ),

        // Attempt data
        attemptState: computed(() => dataState.value.data?.attempt_state),
        displayStatus: computed(() => {
            switch (dataState.value.data?.attempt_status) {
                case 'IN_PROGRESS':
                    return 'In progress'
                case 'SCORED':
                    return 'Scored'
                case 'STARTED':
                    return 'Started'
                default:
                    return ''
            }
        }),
        error: computed(() => dataState.value.error),
        iframeSrcDoc: computed(() => dataState.value.data?.attempt_html),
        renderErrors: computed(() => dataState.value.data?.render_errors ?? {}),
        rescoreDisabled: computed(() => dataState.value.data?.attempt_status !== 'SCORED'),
        restartDisabled: computed(() => dataState.value.data?.attempt_status === 'STARTED'),
        variant: computed(() => dataState.value.data?.variant),

        // ScoreModel
        displayScore: computed(() => (isScored.value ? dataState.value.data?.score?.toFixed(1) : null)),
        isScored,
        scoringCode: computed(() => (isScored.value ? dataState.value.data?.scoring_code : null)),
        scoringState: computed(() => (isScored.value ? dataState.value.data?.scoring_state : null)),

        /** Saves the attempt. */
        async save(formData: Record<string, unknown>) {
            try {
                await postAttempt(formData)
            } catch (err) {
                setError(err)
            }
        },

        /** Scores the attempt. */
        async score() {
            try {
                await postScore()
                await dataRefresh()
            } catch (err) {
                setError(err)
            }
        },

        restart,
    }
})

export default useAttemptStore
