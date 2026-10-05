import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	const { lessons } = await import('$lib/server/tutorials/inngest');
	return { lessons };
};
