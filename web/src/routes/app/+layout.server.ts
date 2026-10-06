import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';
import { api } from '$lib/api';
import API_ROUTES from '$lib/api_routes';
import type { Conversation } from '$lib/types/conversation';

export const load: LayoutServerLoad = async ({ locals, request, depends }) => {
	depends('app:conversations');
	const { session, user } = locals;

	if (!session || !user) {
		redirect(302, '/sign-in');
	}

	const conversations = await getConversations(locals.auth, request.headers);

	return { user, conversations };
};

async function getConversations(auth: App.Locals['auth'], headers: Headers): Promise<Conversation[]> {
	try {
		const { token } = await auth.api.getToken({ headers });

		const { data } = await api.get<Conversation[]>(API_ROUTES.conversation_list, {
			headers: {
				Authorization: `Bearer ${token}`
			}
		});

		return data;
	} catch (error) {
		// The workspace should still render when the API is unreachable.
		console.error('Failed to load conversations:', error);
		return [];
	}
}
