import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = ({ locals }) => {
	const { session, user } = locals;

	if (!session || !user) {
		redirect(302, '/sign-in');
	}

	return { user };
};
