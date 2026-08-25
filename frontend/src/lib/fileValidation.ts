export const ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg'] as const
export const ALLOWED_DOCUMENT_MIME_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
] as const

export const MAX_DOCUMENT_FILE_SIZE_BYTES = 20 * 1024 * 1024 // 20 MB

export interface FileValidationResult {
  isValid: boolean
  error?: string
}

export interface BatchFileValidationResult {
  isValid: boolean
  validFiles: File[]
  errors: Array<{ file: File; error: string }>
}

/**
 * Validates a single document file against supported extensions, MIME types, and 20MB size limit.
 */
export function validateDocumentFile(file: File): FileValidationResult {
  if (!file) {
    return { isValid: false, error: 'No file provided.' }
  }

  // Size check
  if (file.size > MAX_DOCUMENT_FILE_SIZE_BYTES) {
    return {
      isValid: false,
      error: `File "${file.name}" exceeds the maximum upload size of 20MB.`,
    }
  }

  if (file.size === 0) {
    return {
      isValid: false,
      error: `File "${file.name}" is empty (0 bytes).`,
    }
  }

  // Extension check
  const extension = file.name.split('.').pop()?.toLowerCase() || ''
  const isAllowedExt = (ALLOWED_DOCUMENT_EXTENSIONS as readonly string[]).includes(extension)

  // MIME check (fallback if MIME is empty on some platforms)
  const isAllowedMime = file.type
    ? (ALLOWED_DOCUMENT_MIME_TYPES as readonly string[]).includes(file.type.toLowerCase())
    : isAllowedExt

  if (!isAllowedExt && !isAllowedMime) {
    return {
      isValid: false,
      error: `File "${file.name}" has an unsupported format. Allowed types: PDF, PNG, JPG, JPEG.`,
    }
  }

  return { isValid: true }
}

/**
 * Validates a batch of files and segregates valid files and error details.
 */
export function validateDocumentFiles(files: File[]): BatchFileValidationResult {
  if (!files || files.length === 0) {
    return {
      isValid: false,
      validFiles: [],
      errors: [{ file: new File([], 'none'), error: 'No files provided.' }],
    }
  }

  const validFiles: File[] = []
  const errors: Array<{ file: File; error: string }> = []

  for (const file of files) {
    const result = validateDocumentFile(file)
    if (result.isValid) {
      validFiles.push(file)
    } else {
      errors.push({ file, error: result.error || 'Invalid file.' })
    }
  }

  return {
    isValid: errors.length === 0 && validFiles.length > 0,
    validFiles,
    errors,
  }
}
