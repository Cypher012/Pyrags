<script lang="ts">
	import { FileText, ArrowUpRight } from '@lucide/svelte';
	import { getSourceKey } from '$lib/source-documents';
	import type { SourceDocument } from '$lib/types/source-document';

	let { sources, selectedSourceKey, onSelect }: {
		sources: SourceDocument[];
		selectedSourceKey?: string;
		onSelect: (source: SourceDocument) => void;
	} = $props();
</script>

<div class="space-y-2.5" aria-label="Response sources">
	<p class="text-xs font-medium text-muted-foreground">Sources for this answer</p>
	<div class="flex flex-wrap gap-2">
		{#each sources as source, index (source)}
			<button
				type="button"
				onclick={() => onSelect(source)}
				aria-label={`Read source ${index + 1}: ${source.metadata.file_name || 'Source document'}${source.metadata.page_number != null ? `, page ${source.metadata.page_number}` : ''}`}
				aria-pressed={selectedSourceKey === getSourceKey(source)}
				title={source.metadata.file_name || 'Source document'}
				class="group flex max-w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-xs transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none {selectedSourceKey === getSourceKey(source) ? 'border-primary/40 bg-accent text-accent-foreground' : 'border-border bg-background text-foreground hover:border-primary/40 hover:bg-accent/50'}"
			>
				<span class="font-medium text-muted-foreground">{index + 1}</span>
				<FileText class="size-3.5 shrink-0" strokeWidth={1.8} />
				<span class="max-w-40 truncate font-medium sm:max-w-48">
					{source.metadata.file_name?.replace(/\.(pdf|docx)$/i, '') || 'Source document'}
				</span>
				{#if source.metadata.page_number != null}
					<span class="shrink-0 text-muted-foreground">p. {source.metadata.page_number}</span>
				{/if}
				<ArrowUpRight class="size-3.5 shrink-0 text-muted-foreground group-hover:text-foreground" strokeWidth={1.8} />
			</button>
		{/each}
	</div>
</div>
