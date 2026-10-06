import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { api } from '$lib/api';
import API_ROUTES from '$lib/api_routes';
import type { ConversationHeader } from '$lib/types/conversation';
import type { Message } from '$lib/types/message';
import { isAxiosError } from 'axios';
import { authLogger } from '$lib/server/auth-logger';

export const load: PageServerLoad = async ({ params, request, parent, locals }) => {
	await parent();

	let stage = 'generate JWT';
	try {
		const { token } = await locals.auth.api.getToken({ headers: request.headers });
		const authHeader = { Authorization: `Bearer ${token}` };
		stage = 'fetch conversation and messages';
		const [conversation, messages] = await Promise.all([
			api.get<ConversationHeader>(API_ROUTES.conversation(params.conversation_id), {
				headers: authHeader
			}),
			api.get<Message[]>(API_ROUTES.conversation_messages(params.conversation_id), {
				headers: authHeader
			})
		]);

		return {
			conversation: conversation.data,
			messages: messages.data
		};
	} catch (loadError) {
		const status = isAxiosError(loadError) ? loadError.response?.status : undefined;
		if (isAxiosError(loadError)) {
			const path = loadError.config?.url;
			const endpoint = path === API_ROUTES.conversation(params.conversation_id)
				? 'conversation'
				: path === API_ROUTES.conversation_messages(params.conversation_id)
					? 'messages'
					: 'unknown';
			authLogger.log(
				'error',
				`Chat load failed: ${stage}; endpoint=${endpoint}; HTTP status=${status ?? 'none'}`,
				new Error(loadError.message, { cause: loadError.cause })
			);
		} else {
			authLogger.log('error', `Chat load failed: ${stage}`, loadError);
		}
		if (status === 404 || status === 422) error(404, 'Conversation not found');
		if (status === 401 || status === 403) error(status, 'Your session has expired. Sign in again.');
		error(503, 'The conversation service is unavailable. Please try again.');
	}
};
