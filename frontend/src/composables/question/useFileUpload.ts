/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { ref, toRaw, watch } from 'vue'
import type { Ref, WritableComputedRef } from 'vue'

import { usePostQuestionFileUploadMutation } from '@/queries'
import usePendingOperationsStore from '@/stores/usePendingOperationsStore'
import type { ElementPath, FileUploadElement, OptionsFile } from '@/types'

import { useModel } from './elements'

function isBrowserDisplayable(mimeType: string) {
    return ['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/bmp'].includes(mimeType)
}

/**
 * A composable managing the file upload process.
 *
 * @param pathPrefix The parent's path of the form element.
 * @param element The form element definition object.
 * @param toUpload A reactive array of `File` objects to upload.
 * @returns An object containing the file upload data model and state.
 */
function useFileUpload(
    pathPrefix: ElementPath,
    element: FileUploadElement,
    toUpload: Ref<File[]>,
): UseFileUploadReturn {
    const { addOperation, removeOperation } = usePendingOperationsStore()
    const isUploading = ref<boolean>(false)
    // Map file_refs to ObjectURL, so we can show thumbnails even a file is not saved to the question yet
    const objectUrls = ref<Record<string, string>>({})

    const model = useModel(pathPrefix, element)

    watch(toUpload, async (newToUpload) => {
        if (newToUpload.length === 0) {
            return
        }

        const { mutateAsync } = usePostQuestionFileUploadMutation(newToUpload)
        let optionsFiles: OptionsFile[] = []
        const operation = addOperation('file-upload')
        isUploading.value = true

        try {
            optionsFiles = await mutateAsync()
        } finally {
            removeOperation(operation)
            isUploading.value = false
        }

        // Add object URLs for temporary thumbnails
        for (const [i, file] of newToUpload.entries()) {
            const optionsFile = optionsFiles[i]
            if (!optionsFile) {
                throw new Error('Expecting same length')
            }
            if (isBrowserDisplayable(optionsFile.mime_type)) {
                objectUrls.value[optionsFile.file_ref] = URL.createObjectURL(file)
            }
        }

        // Update uploaded files model
        const rawOldValue = toRaw(model.value) ?? [] // Avoid nested proxy objects
        model.value = [...rawOldValue, ...optionsFiles]

        // Reset file input control
        toUpload.value = []
    })

    return { isUploading, model, objectUrls }
}

interface UseFileUploadReturn {
    /** A reactive boolean value that indicates if an upload is currently in progress. */
    isUploading: Ref<boolean>
    /** Data model for file uploads. */
    model: WritableComputedRef<OptionsFile[] | undefined, OptionsFile[]>
    /** A reactive mapping of file refs to temporary object URLs. */
    objectUrls: Ref<Record<string, string>>
}

export { isBrowserDisplayable }
export default useFileUpload
