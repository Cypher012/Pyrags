<script lang="ts">
	import Textarea from '$lib/components/ui/textarea/textarea.svelte';
	import { ArrowUp, ChevronDown } from '@lucide/svelte';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import ChatSources from '$lib/components/chat-sources.svelte';
	import AppHeader from '$lib/components/app-header.svelte';
	import ChatDocumentSidebar from '$lib/components/chat-document-sidebar.svelte';
	import BrandMark from '$lib/assets/logo-mark.svg?component';
	import type { ConversationHeader } from '$lib/types/conversation';
	import type { Message } from '$lib/types/message';
	import type { SourceDocument } from '$lib/types/source-document';
	import { getSourceKey, type SourceSelection } from '$lib/source-documents';
	import { useChat } from '$lib/hooks/use-chat.svelte';
	import { useQueryUsage } from '$lib/hooks/use-query-usage.svelte';
	import DOMPurify from 'dompurify';
	import { marked } from 'marked';
	import { onMount, untrack } from 'svelte';

	let { conversation, messages }: { conversation: ConversationHeader; messages: Message[] } =
		$props();
	const chat = untrack(() => useChat(conversation.id, messages));
	const queryUsage = useQueryUsage();
	const hasMessages = $derived(chat.messages.length > 0 || chat.isSending);
	let sourceSelection = $state<SourceSelection | null>(null);
	let sourcePanelOpen = $state(true);
	let mobileSourcesOpen = $state(false);
	let draft = $state('');
	let composerInput = $state<HTMLTextAreaElement | null>(null);
	const starterPrompts = [
		{ label: 'Summarize the document', question: 'Summarize this document and its main ideas.' },
		{ label: 'Explain key concepts', question: 'Explain the key concepts in this document in simple terms.' },
		{ label: 'Help me study', question: 'Create study questions based on this document.' }
	];
	let model = $state('gpt-5-nano');
	let streamMode = $state('on');
	const models = [
		{ value: 'gpt-5-nano', label: 'GPT-5 Nano', description: 'Quick, lightweight answers' },
		{ value: 'gpt-5-mini', label: 'GPT-5 Mini', description: 'A balance of speed and capability' },
		{ value: 'gpt-5', label: 'GPT-5', description: 'For more demanding questions' }
	];
	const selectedModel = $derived(models.find((option) => option.value === model)?.label);
	let isMounted = $state(false);
	let scrollContainer = $state<HTMLDivElement | null>(null);

	$effect(() => {
		if (chat.messages.map((message) => message.content).join('') && scrollContainer) {
			scrollContainer.scrollTop = scrollContainer.scrollHeight;
		}
	});

	onMount(() => {
		isMounted = true;
	});

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		const content = draft.trim();
		if (!content || chat.isSending || queryUsage.exhausted) return;

		draft = '';
		try {
			await chat.sendMessage(content, { model, isStream: streamMode === 'on' });
		} catch {
			draft = content;
		}
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
		event.preventDefault();
		(event.currentTarget as HTMLTextAreaElement).form?.requestSubmit();
	}

	function selectPrompt(question: string) {
		draft = question;
		composerInput?.focus();
	}

	function showSource(source: SourceDocument) {
		sourceSelection = { source, requestId: (sourceSelection?.requestId ?? 0) + 1 };
		sourcePanelOpen = true;
		mobileSourcesOpen = !window.matchMedia('(min-width: 1280px)').matches;
	}

	function toggleSourcePanel() {
		if (window.matchMedia('(min-width: 1280px)').matches) {
			sourcePanelOpen = !sourcePanelOpen;
		} else {
			mobileSourcesOpen = true;
		}
	}
</script>

<main class="flex h-dvh min-w-0">
	<div class="flex min-w-0 flex-1 flex-col">
		<AppHeader {conversation} onSourcesOpen={toggleSourcePanel} />
		<div class="flex min-h-0 flex-1 flex-col" class:justify-center={!hasMessages}>
			<div bind:this={scrollContainer} class="min-h-0 flex-1 overflow-y-auto" class:hidden={!hasMessages}>
				<div class="mx-auto flex w-full max-w-4xl flex-col gap-8 px-4 py-8 sm:px-6 sm:py-10">
					{#each chat.messages as message (message.id)}
						{#if message.role === 'user'}
							<div class="flex justify-end">
								<div
									aria-label={message.pending ? 'Sending message' : undefined}
									class="max-w-[85%] min-w-0 rounded-2xl bg-primary/30 px-4 py-3 text-sm leading-relaxed break-words whitespace-pre-wrap text-foreground transition-opacity sm:max-w-[75%] {message.pending
										? 'opacity-60 motion-safe:animate-pulse'
										: ''}"
								>
									{message.content}
								</div>
							</div>
						{:else}
							<div class="min-w-0 space-y-4">
								<div
									class="assistant-message prose max-w-[75ch] min-w-0 font-heading text-base leading-7 break-words sm:text-[17px] sm:leading-[1.75]"
								>
									{#if isMounted}
										<!-- Markdown is sanitized with DOMPurify before rendering. -->
										<!-- eslint-disable-next-line svelte/no-at-html-tags -->
										{@html DOMPurify.sanitize(marked.parse(message.content) as string)}
									{:else}
										<p class="whitespace-pre-wrap">{message.content}</p>
									{/if}
								</div>
								{#if message.source_documents?.length}
									<div class="max-w-[75ch] font-heading text-base sm:text-[17px]">
										<ChatSources sources={message.source_documents} onSelect={showSource} selectedSourceKey={sourceSelection ? getSourceKey(sourceSelection.source) : undefined} />
									</div>
								{/if}
							</div>
						{/if}
					{/each}
					{#if chat.isThinking}
						<div role="status" class="flex items-center gap-2 text-sm text-muted-foreground">
							<span
								class="size-2 rounded-full bg-primary motion-safe:animate-pulse"
								aria-hidden="true"
							></span>
							Thinking…
						</div>
					{/if}
				</div>
			</div>
			<div class="shrink-0 bg-background px-4 py-4 sm:px-6">
				<div class="mx-auto w-full max-w-3xl">
					{#if !hasMessages}
						<div class="mb-8 flex flex-col items-center text-center">
							<BrandMark class="mb-5 size-11 sm:size-14" />
							<h2 class="font-heading text-2xl font-medium tracking-tight text-foreground sm:text-3xl">
								What would you like to understand?
							</h2>
							<p class="mt-3 max-w-md text-sm leading-6 text-muted-foreground sm:text-base">
								Explore your document with Pyrags. Ask a question and follow the sources.
							</p>
						</div>
					{/if}
					{@render TextAreaComp()}
					<p class="mt-2 text-center text-xs leading-5 text-muted-foreground" aria-live="polite">
						{#if queryUsage.data?.unlimited}
							Unlimited queries
						{:else if queryUsage.exhausted}
							Daily limit reached — all {queryUsage.data?.limit} queries used. Resets at midnight (Lagos time).
						{:else if queryUsage.data}
							{queryUsage.data.remaining} of {queryUsage.data.limit} queries left today · Resets at midnight (Lagos time)
						{:else}
							{queryUsage.isError ? 'Daily usage unavailable' : 'Checking daily query limit…'}
						{/if}
					</p>
					{#if !hasMessages}
						<div class="mt-5 flex flex-wrap justify-center gap-2">
							{#each starterPrompts as prompt (prompt.label)}
								<button
									type="button"
									onclick={() => selectPrompt(prompt.question)}
									class="rounded-full border border-border px-4 py-2 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:bg-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none sm:text-sm"
								>
									{prompt.label}
								</button>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
	<ChatDocumentSidebar messages={chat.messages} documentCount={conversation.document_count} documents={conversation.documents} selection={sourceSelection} bind:open={sourcePanelOpen} bind:mobileOpen={mobileSourcesOpen} />
</main>

{#snippet TextAreaComp()}
	<form class="w-full rounded-2xl border border-input bg-card" onsubmit={handleSubmit}>
		<Textarea
			bind:ref={composerInput}
			bind:value={draft}
			aria-label="Ask Pyrags about your document"
			onkeydown={handleKeyDown}
			disabled={chat.isSending}
			rows={1}
			placeholder="Ask Pyrags"
			class="max-h-60 min-h-14 resize-none rounded-2xl border-0 bg-transparent px-4 py-4 text-base! leading-6 shadow-none focus-visible:border-input focus-visible:ring-0 focus-visible:outline-none dark:bg-transparent"
		/>
		<div class="flex items-center justify-end gap-2 px-3 pb-3">
			<DropdownMenu.Root>
				<DropdownMenu.Trigger
					type="button"
					disabled={chat.isSending}
					aria-label="Choose streaming mode"
					class="flex h-8 items-center gap-1.5 rounded-full px-3 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:opacity-50"
				>
					Stream {streamMode === 'on' ? 'On' : 'Off'}
					<ChevronDown class="size-3.5" />
				</DropdownMenu.Trigger>
				<DropdownMenu.Content side="top" align="end" sideOffset={8} class="w-60 rounded-2xl p-2">
					<DropdownMenu.Label>Response delivery</DropdownMenu.Label>
					<DropdownMenu.RadioGroup bind:value={streamMode}>
						<DropdownMenu.RadioItem value="on" class="rounded-xl px-3 py-2.5 pr-8">
							<div>
								<p class="font-medium">On</p>
								<p class="mt-0.5 text-xs text-muted-foreground">Show the answer as it arrives</p>
							</div>
						</DropdownMenu.RadioItem>
						<DropdownMenu.RadioItem value="off" class="rounded-xl px-3 py-2.5 pr-8">
							<div>
								<p class="font-medium">Off</p>
								<p class="mt-0.5 text-xs text-muted-foreground">Show the complete answer</p>
							</div>
						</DropdownMenu.RadioItem>
					</DropdownMenu.RadioGroup>
				</DropdownMenu.Content>
			</DropdownMenu.Root>
			<DropdownMenu.Root>
				<DropdownMenu.Trigger
					type="button"
					disabled={chat.isSending}
					aria-label="Choose GPT model"
					class="flex h-8 items-center gap-1.5 rounded-full bg-muted px-3 text-xs text-foreground transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:opacity-50"
				>
					{selectedModel}
					<ChevronDown class="size-3.5" />
				</DropdownMenu.Trigger>
				<DropdownMenu.Content side="top" align="end" sideOffset={8} class="w-64 rounded-2xl p-2">
					<DropdownMenu.Label>GPT model</DropdownMenu.Label>
					<DropdownMenu.RadioGroup bind:value={model}>
						{#each models as option (option.value)}
							<DropdownMenu.RadioItem value={option.value} class="rounded-xl px-3 py-2.5 pr-8">
								<div>
									<p class="font-medium">{option.label}</p>
									<p class="mt-0.5 text-xs text-muted-foreground">{option.description}</p>
								</div>
							</DropdownMenu.RadioItem>
						{/each}
					</DropdownMenu.RadioGroup>
				</DropdownMenu.Content>
			</DropdownMenu.Root>
			{#if draft.trim()}
				<button
					type="submit"
					aria-label="Send message"
					disabled={chat.isSending || queryUsage.exhausted}
					class="flex size-8 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground transition-colors hover:bg-primary/80 disabled:cursor-not-allowed disabled:opacity-50"
				>
					<ArrowUp class="size-4" />
				</button>
			{/if}
		</div>
	</form>
{/snippet}

<style>
	.assistant-message {
		--tw-prose-body: var(--foreground);
		--tw-prose-headings: var(--foreground);
		--tw-prose-lead: var(--muted-foreground);
		--tw-prose-links: var(--primary);
		--tw-prose-bold: var(--foreground);
		--tw-prose-counters: var(--muted-foreground);
		--tw-prose-bullets: var(--muted-foreground);
		--tw-prose-hr: var(--border);
		--tw-prose-quotes: var(--foreground);
		--tw-prose-quote-borders: var(--border);
		--tw-prose-captions: var(--muted-foreground);
		--tw-prose-code: var(--foreground);
		--tw-prose-pre-code: var(--foreground);
		--tw-prose-pre-bg: var(--card);
		--tw-prose-th-borders: var(--border);
		--tw-prose-td-borders: var(--border);
	}

	.assistant-message :global(p) {
		margin-block: 1em;
		white-space: pre-line;
	}

	.assistant-message :global(h1),
	.assistant-message :global(h2),
	.assistant-message :global(h3),
	.assistant-message :global(h4) {
		font-weight: 600;
		letter-spacing: -0.02em;
		line-height: 1.35;
	}

	.assistant-message :global(pre) {
		max-width: 100%;
		overflow-x: auto;
		border: 1px solid var(--border);
		border-radius: 0.75rem;
	}

	.assistant-message :global(:not(pre) > code) {
		border-radius: 0.25rem;
		background: var(--muted);
		padding: 0.15em 0.35em;
		font-size: 0.85em;
		font-weight: 400;
		overflow-wrap: anywhere;
	}

	.assistant-message :global(code::before),
	.assistant-message :global(code::after) {
		content: none;
	}

	.assistant-message :global(a) {
		text-underline-offset: 0.2em;
		overflow-wrap: anywhere;
	}

	.assistant-message :global(table) {
		display: block;
		max-width: 100%;
		overflow-x: auto;
	}

	.assistant-message :global(blockquote) {
		font-weight: 400;
		font-style: normal;
	}

	.assistant-message > :global(:first-child) {
		margin-top: 0;
	}

	.assistant-message > :global(:last-child) {
		margin-bottom: 0;
	}
</style>
