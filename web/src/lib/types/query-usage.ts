export type QueryUsage = {
	limit: number | null;
	used: number;
	remaining: number | null;
	unlimited: boolean;
	resets_at: string;
};
