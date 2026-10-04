export type Conversation = {
	id: string;
	user_id: string;
	title: string;
	created_at: string;
	updated_at: string;
};

export type ConversationHeader = {
	id: string;
	title: string;
	document_count: number;
	documents?: ConversationDocument[];
};

export type ConversationDocument = {
	id: string;
	file_name: string;
	file_type: 'pdf' | 'docx';
	status: 'processing' | 'ready' | 'failed';
	created_at?: string;
	page_count?: number | null;
	size_bytes?: number | null;
	preview?: { content: string; page_number?: number | null } | null;
};
