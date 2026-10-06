import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './auth.schema';
import { env } from '$env/dynamic/private';

export function createDatabase() {
	const databaseUrl = env.APP_ENV === 'production' ? env.NEON_DATABASE_URL : env.LOCAL_DATABASE_URL;
	if (!databaseUrl) throw new Error('DATABASE_URL is not set');
	const client = postgres(databaseUrl, { max: 1 });
	return {
		db: drizzle(client, { schema }),
		close: () => client.end({ timeout: 5 })
	};
}

export type AuthDatabase = ReturnType<typeof createDatabase>['db'];
