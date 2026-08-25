import React from 'react'
import { FolderKanban, Plus } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'

export function CollectionsPage() {
  return (
    <div className="space-y-6 text-left">
      <PageHeader
        title="Collections"
        description="Organize documents into themed workspaces for targeted queries and cross-document comparison"
        actions={
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            New Collection
          </Button>
        }
      />

      <EmptyState
        icon={FolderKanban}
        title="No collections created"
        description="Group multiple related documents together to run multi-document comparisons and scoped AI research."
        action={
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            Create Collection
          </Button>
        }
      />
    </div>
  )
}
