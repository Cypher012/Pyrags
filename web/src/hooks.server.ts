import type { Handle } from '@sveltejs/kit';
import { building } from '$app/environment';
import { createAuth } from '$lib/server/auth';
import { createDatabase } from '$lib/server/db';
import { authLogger } from '$lib/server/auth-logger';
import { svelteKitHandler } from 'better-auth/svelte-kit';

const handleBetterAuth: Handle = async ({ event, resolve }) => {
	if (building) return resolve(event);
	const database = createDatabase();
	try {
		const auth = createAuth(database.db);
		event.locals.auth = auth;
		const session = await auth.api.getSession({ headers: event.request.headers });

		if (session) {
			event.locals.session = session.session;
			event.locals.user = session.user;
		}

		return await svelteKitHandler({ event, resolve, auth, building });
	} finally {
		try {
			await database.close();
		} catch (error) {
			authLogger.log('error', 'Failed to close auth database connection', error);
		}
	}
};

export const handle: Handle = handleBetterAuth;
