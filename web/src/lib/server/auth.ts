import { env } from '$env/dynamic/private';
import { env as publicEnv } from '$env/dynamic/public';
import { betterAuth } from 'better-auth/minimal';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';
import { sveltekitCookies } from 'better-auth/svelte-kit';
import { getRequestEvent } from '$app/server';
import type { AuthDatabase } from '$lib/server/db';
import { jwt } from 'better-auth/plugins';
import { authLogger } from './auth-logger';

export const createAuth = (db: AuthDatabase) => betterAuth({
	logger: authLogger,
	baseURL: env.ORIGIN || publicEnv.PUBLIC_ORIGIN,
	secret: env.BETTER_AUTH_SECRET,
	database: drizzleAdapter(db, { provider: 'pg' }),
	socialProviders: {
		github: {
			clientId: env.GITHUB_CLIENT_ID,
			clientSecret: env.GITHUB_CLIENT_SECRET
		},
		google: {
			clientId: env.GOOGLE_CLIENT_ID,
			clientSecret: env.GOOGLE_CLIENT_SECRET
		}
	},
	plugins: [
		jwt({
			jwt: {
				definePayload: ({ user }) => ({
					id: user.id,
					email: user.email
				})
			}
		}),
		sveltekitCookies(getRequestEvent) // make sure this is the last plugin in the array
	]
});
