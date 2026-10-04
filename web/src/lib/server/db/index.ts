import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './auth.schema';
import { env } from '$env/dynamic/private';

const DATABASE_URL = env.APP_ENV === 'production' ? env.NEON_DATABASE_URL : env.LOCAL_DATABASE_URL;

if (!DATABASE_URL) throw new Error('DATABASE_URL is not set');

const client = postgres(DATABASE_URL);

export const db = drizzle(client, { schema });
