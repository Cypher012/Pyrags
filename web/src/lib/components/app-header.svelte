<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar';
	import type { ConversationHeader } from '$lib/types/conversation';
	import { FileTextIcon, PanelRight } from '@lucide/svelte';

	const { conversation, onSourcesOpen }: { conversation: ConversationHeader; onSourcesOpen?: () => void } = $props();
	const { document_count, title } = $derived(conversation);
</script>

<header class="flex h-16 w-full items-center border px-5 py-9">
	<div class=" block md:hidden">
		<Sidebar.Trigger />
	</div>
	<div class="flex min-w-0 flex-1 items-center justify-center gap-3 md:justify-start md:gap-6">
		<FileTextIcon class="size-6 sm:size-7" />
		<div class="flex min-w-0 flex-col gap-0.5">
			<h1 class="truncate font-heading text-base font-semibold sm:text-lg" title={title}>{title}</h1>
			<p class="text-xs text-muted-foreground sm:text-sm">
				{document_count}
				{document_count === 1 ? 'document' : 'documents'} in this conversation
			</p>
		</div>
	</div>
	{#if onSourcesOpen}
		<button type="button" onclick={onSourcesOpen} aria-label="Toggle documents and sources" title="Documents and sources" class="ml-3 flex size-9 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none">
			<PanelRight class="size-4.5" strokeWidth={1.8} />
		</button>
	{/if}
</header>
