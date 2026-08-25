import React, { useRef, useState } from 'react'
import {
  FileText,
  FileUp,
  Image as ImageIcon,
  Loader2,
  Upload,
  X,
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { formatFileSize, cn } from '@/lib/utils'
import {
  validateDocumentFile,
  ALLOWED_DOCUMENT_EXTENSIONS,
} from '@/lib/fileValidation'
import { useUploadDocuments } from '@/hooks/documents'
import { useToast } from '@/components/ui/useToast'

export interface UploadDropzoneProps {
  onUploadSuccess?: () => void
  className?: string
}

interface StagedFile {
  id: string
  file: File
  error?: string
}

export function UploadDropzone({ onUploadSuccess, className }: UploadDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [stagedFiles, setStagedFiles] = useState<StagedFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { mutateAsync: upload, isPending: isUploading } = useUploadDocuments()
  const { toast } = useToast()

  const handleFiles = (incomingFiles: FileList | File[]) => {
    const newStaged: StagedFile[] = []

    Array.from(incomingFiles).forEach((file) => {
      const validation = validateDocumentFile(file)
      newStaged.push({
        id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
        file,
        error: validation.isValid ? undefined : validation.error,
      })
    })

    setStagedFiles((prev) => [...prev, ...newStaged])
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const removeStagedFile = (id: string) => {
    setStagedFiles((prev) => prev.filter((f) => f.id !== id))
  }

  const clearAllStaged = () => {
    setStagedFiles([])
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const validStagedFiles = stagedFiles.filter((f) => !f.error).map((f) => f.file)
  const hasErrors = stagedFiles.some((f) => Boolean(f.error))

  const handleUpload = async () => {
    if (validStagedFiles.length === 0 || isUploading) return

    try {
      const res = await upload(validStagedFiles)
      toast({
        title: 'Upload complete',
        description: `Successfully uploaded ${res.count} document(s).`,
        variant: 'success',
      })
      clearAllStaged()
      onUploadSuccess?.()
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        (err as Error).message ||
        'Failed to upload documents.'
      toast({
        title: 'Upload failed',
        description: msg,
        variant: 'error',
      })
    }
  }

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    if (ext === 'pdf') {
      return <FileText className="w-5 h-5 text-rose-500 shrink-0" />
    }
    return <ImageIcon className="w-5 h-5 text-blue-500 shrink-0" />
  }

  return (
    <GlassCard
      variant="interactive"
      className={cn(
        'p-6 sm:p-8 transition-all duration-200 text-center select-none',
        isDragOver
          ? 'border-[#886F4E] bg-[#886F4E]/5 dark:border-white/40 dark:bg-white/[0.08]'
          : 'border-dashed border-[rgba(90,70,50,0.22)] dark:border-white/[0.12]',
        className,
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
        className="hidden"
        onChange={(e) => {
          if (e.target.files) handleFiles(e.target.files)
        }}
      />

      {stagedFiles.length === 0 ? (
        <div className="flex flex-col items-center justify-center space-y-3.5 py-4">
          <div className="w-12 h-12 rounded-2xl bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A] flex items-center justify-center shadow-xs">
            <FileUp className="w-6 h-6" />
          </div>

          <div className="space-y-1 max-w-md">
            <h4 className="text-sm font-semibold text-[#211C17] dark:text-white">
              Drag and drop document files here
            </h4>
            <p className="text-xs text-[#71695F] dark:text-zinc-400">
              Supports {ALLOWED_DOCUMENT_EXTENSIONS.map((e) => e.toUpperCase()).join(', ')} up to 20MB.
            </p>
          </div>

          <Button
            type="button"
            variant="secondary"
            size="sm"
            leftIcon={<Upload className="w-3.5 h-3.5" />}
            onClick={() => fileInputRef.current?.click()}
          >
            Browse Files
          </Button>
        </div>
      ) : (
        <div className="space-y-4 text-left">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#211C17] dark:text-white">
                Staged Files ({validStagedFiles.length} ready
                {hasErrors && `, ${stagedFiles.length - validStagedFiles.length} invalid`})
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
              >
                Add More
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="text-rose-600 hover:text-rose-700 dark:text-rose-400"
                onClick={clearAllStaged}
                disabled={isUploading}
              >
                Clear All
              </Button>
            </div>
          </div>

          {/* Staged file list */}
          <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
            {stagedFiles.map((item) => (
              <div
                key={item.id}
                className={cn(
                  'p-3 rounded-xl border flex items-center justify-between gap-3 text-xs transition-colors',
                  item.error
                    ? 'bg-rose-500/10 border-rose-500/25 text-rose-700 dark:text-rose-400'
                    : 'bg-[#FFFCF8] dark:bg-white/[0.04] border-[rgba(90,70,50,0.14)] dark:border-white/[0.08] text-[#211C17] dark:text-zinc-200',
                )}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {getFileIcon(item.file.name)}
                  <div className="min-w-0 space-y-0.5">
                    <p className="font-medium truncate">{item.file.name}</p>
                    <p className="text-[11px] text-[#71695F] dark:text-zinc-400">
                      {formatFileSize(item.file.size)}
                      {item.error && ` • ${item.error}`}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => removeStagedFile(item.id)}
                  disabled={isUploading}
                  aria-label={`Remove ${item.file.name}`}
                  className="p-1 rounded-lg text-[#9A9187] hover:text-[#211C17] dark:text-zinc-400 dark:hover:text-white transition-colors cursor-pointer shrink-0"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Upload Button */}
          <div className="flex items-center justify-end gap-3 pt-2 border-t border-[rgba(90,70,50,0.10)] dark:border-white/[0.08]">
            <Button
              type="button"
              variant="primary"
              size="md"
              disabled={validStagedFiles.length === 0 || isUploading}
              isLoading={isUploading}
              onClick={handleUpload}
              leftIcon={
                isUploading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )
              }
            >
              {isUploading
                ? 'Uploading...'
                : `Upload ${validStagedFiles.length} ${validStagedFiles.length === 1 ? 'Document' : 'Documents'}`}
            </Button>
          </div>
        </div>
      )}
    </GlassCard>
  )
}
