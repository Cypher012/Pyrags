import type { SourceDocument } from '$lib/types/source-document';

export type SourceSelection = { source: SourceDocument; requestId: number };

export function getSourceKey(source: SourceDocument): string {
	return JSON.stringify([
		source.metadata.file_name,
		source.metadata.file_type,
		source.metadata.page_number,
		source.metadata.chunk_index,
		source.content
	]);
}
