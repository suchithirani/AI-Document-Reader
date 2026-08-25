import { useQuery } from '@tanstack/react-query'
import { getHealthStatus } from '@/api/health'
import type { HealthStatusData } from '@/types/api'

export function useHealth() {
  return useQuery<HealthStatusData>({
    queryKey: ['system-health'],
    queryFn: getHealthStatus,
    refetchInterval: 15000,
    retry: 2,
  })
}
