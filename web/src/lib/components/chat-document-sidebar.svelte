<script lang="ts">
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import { FileText, ChevronDown, X } from '@lucide/svelte';
	import { tick } from 'svelte';
	import { getSourceKey, type SourceSelection } from '$lib/source-documents';
	import type { ConversationDocument } from '$lib/types/conversation';
	import type { Message } from '$lib/types/message';

	let {
		messages,
		documentCount,
		documents = [],
		selection = null,
		open = $bindable(true),
		mobileOpen = $bindable(false)
	}: {
		messages: Message[];
		documentCount: number;
		documents?: ConversationDocument[];
		selection?: SourceSelection | null;
		open?: boolean;
		mobileOpen?: boolean;
	} = $props();

	type LibraryDocument = {
		id: string;
		file_name: string;
		file_type?: string | null;
		status?: ConversationDocument['status'];
		created_at?: string;
		page_count?: number | null;
		size_bytes?: number | null;
		preview?: { content: string; page_number?: number | null } | null;
	};

	let activeTab = $state('document');
	let selectedFileName = $state('');
	let expandedSourceKey = $state<string | null>(null);
	let desktopContainer = $state<HTMLElement | null>(null);
	let mobileContainer = $state<HTMLDivElement | null>(null);

	const sources = $derived(
		Array.from(new Map(messages.flatMap((message) => message.source_documents ?? []).map((source) => [getSourceKey(source), source])).values())
	);
	const libraryDocuments = $derived.by(() => {
		const library = new Map<string, LibraryDocument>(documents.map((document) => [document.file_name, document]));
		for (const source of sources) {
			const fileName = source.metadata.file_name || 'Source document';
			if (!library.has(fileName)) {
				library.set(fileName, { id: fileName, file_name: fileName, file_type: source.metadata.file_type, status: 'ready' });
			}
		}
		return Array.from(library.values());
	});
	const selectedDocument = $derived(libraryDocuments.find((document) => document.file_name === selectedFileName) ?? libraryDocuments[0]);
	const selectedDocumentSources = $derived(sources.filter((source) => (source.metadata.file_name || 'Source document') === selectedDocument?.file_name));
	const preview = $derived(selectedDocument?.preview ?? selectedDocumentSources[0]);
	const uploadedAt = $derived(
		selectedDocument?.created_at && Number.isFinite(Date.parse(selectedDocument.created_at))
			? new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }).format(new Date(selectedDocument.created_at)) + ' UTC'
			: 'Not recorded'
	);

	$effect(() => {
		const selected = selection;
		if (!selected) return;
		const key = getSourceKey(selected.source);
		activeTab = 'sources';
		selectedFileName = selected.source.metadata.file_name || 'Source document';
		expandedSourceKey = key;
		void tick().then(() => {
			if (selection !== selected) return;
			const container = mobileOpen ? mobileContainer : desktopContainer;
			const button = Array.from(container?.querySelectorAll<HTMLButtonElement>('button[data-source-key]') ?? []).find((element) => element.dataset.sourceKey === key);
			button?.focus({ preventScroll: true });
			button?.scrollIntoView({ block: 'nearest' });
		});
	});

	function formatSize(bytes: number | null | undefined) {
		if (bytes == null) return 'Not recorded';
		if (bytes < 1024) return bytes + ' B';
		if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
		return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
	}
</script>

{#if open}
	<aside bind:this={desktopContainer} aria-label="Documents and sources" class="hidden h-dvh w-86 shrink-0 flex-col border-l border-border bg-background xl:flex">
		{@render Panel(false)}
	</aside>
{/if}

<Sheet.Root bind:open={mobileOpen}>
	{#if mobileOpen}
	<Sheet.Content side="right" showCloseButton={false} class="w-full max-w-sm gap-0 bg-background p-0 motion-reduce:animate-none motion-reduce:transition-none">
		<Sheet.Title class="sr-only">Documents and sources</Sheet.Title>
		<Sheet.Description class="sr-only">Browse document previews, file details, and supporting passages.</Sheet.Description>
		<div bind:this={mobileContainer} class="flex min-h-0 flex-1 flex-col">
			{@render Panel(true)}
		</div>
	</Sheet.Content>
	{/if}
</Sheet.Root>

{#snippet Panel(isMobile: boolean)}
	<Tabs.Root bind:value={activeTab} class="flex min-h-0 flex-1 flex-col gap-0">
		<div class="relative shrink-0 px-6 pt-7">
			<Tabs.List variant="line" class="h-11 w-full justify-start gap-7 border-b border-border p-0">
				<Tabs.Trigger value="document" class="h-full flex-none rounded-none px-1 pb-3 text-[13px] data-active:text-foreground after:rounded-t-full after:bg-foreground">Document</Tabs.Trigger>
				<Tabs.Trigger value="sources" class="h-full flex-none rounded-none px-1 pb-3 text-[13px] data-active:text-foreground after:rounded-t-full after:bg-foreground">Sources</Tabs.Trigger>
			</Tabs.List>
			{#if isMobile}
				<button type="button" onclick={() => mobileOpen = false} aria-label="Close reference panel" class="absolute top-7 right-5 flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"><X class="size-4" strokeWidth={1.8} /></button>
			{/if}
		</div>
		<div class="min-h-0 flex-1 overflow-y-auto overscroll-contain px-6 pt-5 pb-8">
			<Tabs.Content value="document" class="space-y-6">
				<section class="rounded-lg border border-border/70 px-1.5 pt-3 pb-1.5">
					<h2 class="mb-2 px-2 text-[13px] font-semibold text-foreground">Conversation documents</h2>
					{#if libraryDocuments.length}
						{#each libraryDocuments as document (document.id)}
							<button type="button" onclick={() => selectedFileName = document.file_name} aria-pressed={selectedDocument?.id === document.id} class="flex w-full items-start gap-3 rounded-md px-3 py-3 text-left transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none {selectedDocument?.id === document.id ? 'bg-sidebar-accent/70' : 'hover:bg-muted'}">
								<FileText class="mt-0.5 size-6 shrink-0 text-foreground" strokeWidth={1.8} />
								<span class="min-w-0 flex-1">
									<span class="block font-heading text-[13px] leading-5 font-semibold break-words text-foreground">{document.file_name.replace(/\.(pdf|docx)$/i, '')}</span>
									<span class="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
										{#if document.file_type}<span class="uppercase">{document.file_type}</span>{/if}
										{#if document.status}
											<span aria-hidden="true">·</span>
											<span class="inline-flex items-center gap-1.5 {document.status === 'ready' ? 'text-success' : document.status === 'failed' ? 'text-destructive' : 'text-warning'}">
												<span aria-hidden="true" class="size-1.5 rounded-full bg-current ring-3 ring-current/10"></span>
												{document.status === 'ready' ? 'Ready' : document.status === 'failed' ? 'Failed' : 'Processing'}
											</span>
										{/if}
									</span>
								</span>
							</button>
						{/each}
					{:else}
						<p class="px-2 py-3 text-xs leading-5 text-muted-foreground">{documentCount ? 'Document details are not available yet.' : 'Upload a document to get started.'}</p>
					{/if}
				</section>
				{#if selectedDocument}
					<section class="space-y-2.5">
						<h2 class="text-[13px] font-semibold text-foreground">Preview</h2>
						<div aria-label="Extracted document preview" class="flex min-h-64 flex-col rounded-lg border border-border bg-card px-6 py-5 shadow-xs">
							<p class="font-heading text-[13px] leading-5 font-semibold break-words text-foreground">{selectedDocument.file_name.replace(/\.(pdf|docx)$/i, '')}</p>
							<div class="my-4 border-t border-foreground/40"></div>
							{#if preview?.content}
								<p class="line-clamp-10 text-xs leading-5 break-words whitespace-pre-line text-foreground">{preview.content}</p>
								{@const pageNumber = 'metadata' in preview ? preview.metadata.page_number : preview.page_number}
								{#if pageNumber != null}<p class="mt-auto pt-5 text-right text-[11px] text-muted-foreground">Page {pageNumber}</p>{/if}
							{:else}
								<p class="text-xs leading-5 text-muted-foreground">{selectedDocument.status === 'processing' ? 'The preview will appear when processing finishes.' : 'No extracted text is available for this document.'}</p>
							{/if}
						</div>
					</section>
					<section class="space-y-3">
						<h2 class="text-[13px] font-semibold text-foreground">Document info</h2>
						<dl class="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-x-4 gap-y-2 text-xs leading-5">
							<dt class="text-muted-foreground">Type</dt><dd class="text-foreground uppercase">{selectedDocument.file_type || 'Unknown'}</dd>
							<dt class="text-muted-foreground">Pages</dt><dd class="text-foreground">{selectedDocument.page_count ?? 'Not recorded'}</dd>
							<dt class="text-muted-foreground">Size</dt><dd class="text-foreground">{formatSize(selectedDocument.size_bytes)}</dd>
							<dt class="text-muted-foreground">Uploaded</dt><dd class="text-foreground">{uploadedAt}</dd>
						</dl>
					</section>
				{/if}
			</Tabs.Content>
			<Tabs.Content value="sources" class="space-y-3">
				<h2 class="mb-4 text-[13px] font-semibold text-foreground">Supporting passages</h2>
				{#if sources.length}
					{#each sources as source (getSourceKey(source))}
						{@const key = getSourceKey(source)}
						{@const expanded = expandedSourceKey === key}
						<article class="overflow-hidden rounded-lg border {expanded ? 'border-primary/35 bg-card' : 'border-border bg-card'}">
							<button type="button" data-source-key={key} aria-expanded={expanded} onclick={() => expandedSourceKey = expanded ? null : key} class="w-full p-4 text-left transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring focus-visible:outline-none">
								<span class="flex items-start gap-2.5">
									<FileText class="mt-0.5 size-4 shrink-0 text-foreground" strokeWidth={1.8} />
									<span class="min-w-0 flex-1">
										<span class="block font-heading text-xs leading-5 font-semibold break-words text-foreground">{source.metadata.file_name?.replace(/\.(pdf|docx)$/i, '') || 'Source document'}</span>
										<span class="mt-1 block text-[11px] text-muted-foreground">{source.metadata.page_number != null ? 'Page ' + source.metadata.page_number : 'Passage ' + (source.metadata.chunk_index + 1)}</span>
									</span>
									<ChevronDown class="mt-0.5 size-3.5 shrink-0 text-muted-foreground {expanded ? 'rotate-180' : ''}" strokeWidth={1.8} />
								</span>
								{#if !expanded}<span class="mt-3 block line-clamp-2 text-xs leading-5 text-muted-foreground">{source.content}</span>{/if}
							</button>
							{#if expanded}<p class="px-4 pb-4 text-sm leading-6 break-words whitespace-pre-wrap text-foreground">{source.content}</p>{/if}
						</article>
					{/each}
				{:else}
					<p class="text-xs leading-5 text-muted-foreground">Ask a question to see the passages supporting your answer.</p>
				{/if}
			</Tabs.Content>
		</div>
	</Tabs.Root>
{/snippet}
