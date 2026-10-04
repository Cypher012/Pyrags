import { browser } from '$app/environment';
import { createQuery } from '@tanstack/svelte-query';
import { api } from '$lib/api';
import API_ROUTES from '$lib/api_routes';
import type { QueryUsage } from '$lib/types/query-usage';

export const queryUsageKey = ['daily-query-usage'] as const;

export function useQueryUsage() {
	const usage = createQuery<QueryUsage>(() => ({
		queryKey: queryUsageKey,
		queryFn: async () => (await api.get<QueryUsage>(API_ROUTES.query_usage)).data,
		enabled: browser,
		staleTime: 30_000,
		refetchInterval: 60_000,
		retry: 1
	}));

	return {
		get data() { return usage.data; },
		get isError() { return usage.isError; },
		get exhausted() { return usage.data?.remaining === 0 && !usage.data.unlimited; }
	};
}
