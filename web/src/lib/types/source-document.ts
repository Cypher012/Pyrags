export type SourceDocument = {
	content: string;
	metadata: {
		file_name?: string | null;
		file_type?: 'pdf' | 'docx' | null;
		page_number?: number | null;
		chunk_index: number;
	};
};
