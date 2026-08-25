import React from 'react'
import { AlertTriangle, Trash2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { useDeleteDocument } from '@/hooks/documents'
import { useToast } from '@/components/ui/useToast'
import type { Document } from '@/types/document'

export interface DeleteDocumentModalProps {
  document: Document | null
  isOpen: boolean
  onClose: () => void
  onDeleted?: () => void
}

export function DeleteDocumentModal({
  document,
  isOpen,
  onClose,
  onDeleted,
}: DeleteDocumentModalProps) {
  const { mutateAsync: deleteDoc, isPending: isDeleting } = useDeleteDocument()
  const { toast } = useToast()

  if (!document) return null

  const handleDelete = async () => {
    try {
      await deleteDoc(document.id)
      toast({
        title: 'Document deleted',
        description: `"${document.original_filename}" was successfully deleted.`,
        variant: 'success',
      })
      onDeleted?.()
      onClose()
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        (err as Error).message ||
        'Failed to delete document.'
      toast({
        title: 'Deletion failed',
        description: msg,
        variant: 'error',
      })
    }
  }

  return (
    <Dialog isOpen={isOpen} onClose={onClose}>
      <DialogHeader onClose={onClose}>
        <DialogTitle>Delete Document</DialogTitle>
        <DialogDescription>
          Are you sure you want to delete this document? This action cannot be undone.
        </DialogDescription>
      </DialogHeader>

      <DialogContent>
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-2.5 my-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="space-y-1 text-left">
            <p className="font-semibold">{document.original_filename}</p>
            <p className="text-[11px] leading-relaxed text-rose-700 dark:text-rose-400">
              Deleting this document will remove its raw storage, extracted OCR text, chunk metadata, and vector index.
            </p>
          </div>
        </div>
      </DialogContent>

      <DialogFooter>
        <div className="flex items-center justify-end gap-2.5 w-full">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            size="sm"
            isLoading={isDeleting}
            disabled={isDeleting}
            onClick={handleDelete}
            leftIcon={<Trash2 className="w-4 h-4" />}
          >
            Confirm Delete
          </Button>
        </div>
      </DialogFooter>
    </Dialog>
  )
}
