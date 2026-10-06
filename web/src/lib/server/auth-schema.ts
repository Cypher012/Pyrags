import { createAuth } from './auth';
import { createDatabase } from './db';

export const auth = createAuth(createDatabase().db);
