import { defineConfig } from 'drizzle-kit';

const DATABASE_URL =
	process.env.APP_ENV === 'production'
		? process.env.NEON_DATABASE_URL
		: process.env.LOCAL_DATABASE_URL;

if (!DATABASE_URL) throw new Error('Selected database URL is not set');

export default defineConfig({
	schema: './src/lib/server/db/auth.schema.ts',
	dialect: 'postgresql',
	dbCredentials: { url: DATABASE_URL },
	verbose: true,
	strict: true
});
