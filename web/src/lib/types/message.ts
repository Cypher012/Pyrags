export type Role = 'user' | 'assistant';

export type Message = {
	id: string;
	conversation_id: string;
	role: Role;
	content: string;
	created_at: string;
	updated_at: string;
	source_documents?: SourceDocument[];
};
import type { SourceDocument } from './source-document';
