import { useEffect, useState } from 'react';
import { listCleaners, type CleanerListItem } from '../api/cleaners';
import type { ServiceType } from '../api/job_requests';

export type PreferredCleanerId = number | '';

type UseEligibleCleanersArgs = {
  serviceType: ServiceType | '';
  preferredDate: string;
  preferredTimeStart: string;
  preferredTimeEnd: string;
  excludeJobRequestId?: number;
};

export function useEligibleCleaners({
  serviceType,
  preferredDate,
  preferredTimeStart,
  preferredTimeEnd,
  excludeJobRequestId,
}: UseEligibleCleanersArgs) {
  const [cleaners, setCleaners] = useState<CleanerListItem[]>([]);
  const [preferredCleanerId, setPreferredCleanerId] = useState<PreferredCleanerId>('');
  const canLoadCleaners = Boolean(serviceType && preferredDate);

  useEffect(() => {
    let mounted = true;

    if (!canLoadCleaners) {
      setCleaners([]);
      setPreferredCleanerId('');
      return () => {
        mounted = false;
      };
    }

    (async () => {
      try {
        const res = await listCleaners({
          service_type: serviceType as ServiceType,
          preferred_date: preferredDate,
          preferred_time_start: preferredTimeStart || undefined,
          preferred_time_end: preferredTimeEnd || undefined,
          exclude_job_request_id: excludeJobRequestId,
        });
        if (!mounted) return;

        setCleaners(res.cleaners);
        setPreferredCleanerId((current) => (
          current !== '' && !res.cleaners.some((cleaner) => cleaner.user_id === current)
            ? ''
            : current
        ));
      } catch (e: unknown) {
        console.error(e);
        if (mounted) {
          setCleaners([]);
          setPreferredCleanerId('');
        }
      }
    })();

    return () => {
      mounted = false;
    };
  }, [
    canLoadCleaners,
    excludeJobRequestId,
    serviceType,
    preferredDate,
    preferredTimeStart,
    preferredTimeEnd,
  ]);

  return {
    cleaners,
    preferredCleanerId,
    setPreferredCleanerId,
    canLoadCleaners,
  };
}
