<script lang="ts">
	import {
		formatFileSize,
		MAX_DOCUMENT_BYTES,
		MAX_DOCUMENTS,
		useFileUpload,
		type DropDetail
	} from '$lib/hooks/use-file-upload.svelte';
	import { Progress } from '$lib/components/ui/progress/index.js';
	import FileTextIcon from '@lucide/svelte/icons/file-text';
	import Dropzone from 'svelte-file-dropzone';
	import { onMount, untrack } from 'svelte';
	import { useUploadProgress, type UploadProgress } from '$lib/hooks/use-upload-progress.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Dot, File, Trash } from '@lucide/svelte';
	import type { StoredDocumentType } from '$lib/indexed-db/documents';
	import type { DocumentFlow } from './+page.svelte';
	import { goto, invalidate } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { toast } from 'svelte-sonner';

	interface Props {
		documentFlow: DocumentFlow;
		onFlowChange: (flow: DocumentFlow) => void;
		isLocked: boolean;
	}

	let { documentFlow, onFlowChange, isLocked }: Props = $props();

	const upload = useFileUpload();

	export async function uploadDocument() {
		await upload.handleUploadDocument();
	}

	onMount(async () => {
		await upload.restoreDocuments();

		if (upload.documents.length > 0) {
			onFlowChange('selected');
		}
	});

	async function handleFilesSelect(event: CustomEvent<DropDetail>) {
		await upload.handleFilesSelect(event);

		if (upload.documents.length > 0) {
			onFlowChange('selected');
		}
	}

	async function handleFileRemoval(id: string) {
		await upload.handleFileRemoval(id);

		if (upload.documents.length === 0) {
			onFlowChange('selecting');
		}
	}

	type Tracker = { jobId: string; progress: ReturnType<typeof useUploadProgress> };
	let trackers = $state<Record<string, Tracker>>({});
	let updates = $state<Record<string, UploadProgress>>({});
	let connectionErrors = $state<Record<string, string>>({});
	let hasPreviousBatch = $state(false);
	const completedCount = $derived(Object.values(updates).filter((item) => item.stage === 'completed').length);
	const failedCount = $derived(Object.values(updates).filter((item) => item.stage === 'error').length);

	$effect(() => {
		const batch = upload.uploadedData;
		if (!batch) {
			trackers = {};
			updates = {};
			connectionErrors = {};
			return;
		}
		const selected = untrack(() => upload.documents);
		const conversationId = batch.conversation_id;
		let active = true;
		let settled = false;
		hasPreviousBatch = true;
		updates = {};
		connectionErrors = {};

		async function settleBatch() {
			if (!active || settled) return;
			const snapshots = selected.map((document) => updates[document.id]);
			if (!snapshots.every((item) => item && ['completed', 'error'].includes(item.stage))) return;
			settled = true;
			if (snapshots.some((item) => item.stage === 'error')) {
				onFlowChange('failed');
				return;
			}
			onFlowChange('ready');
			try {
				await upload.clearStoredDocuments();
			} catch {
				toast.error('Your documents are ready, but their local copies could not be cleared.');
			}
			try {
				await invalidate('app:conversations');
				await goto(resolve('/app/chat/[conversation_id]', { conversation_id: conversationId }));
			} catch {
				toast.error('Your documents are ready. Open the conversation from Recents.');
			}
		}

		const next = Object.fromEntries(batch.jobs.map((job, index) => {
			const document = selected[index];
			return [document.id, {
				jobId: job.job_id,
				progress: useUploadProgress({
					onProgress: (data) => {
						if (!active) return;
						updates[document.id] = data;
						connectionErrors[document.id] = '';
					},
					onCompleted: () => { void settleBatch(); },
					onError: (message) => {
						if (!active) return;
						if (updates[document.id]?.stage === 'error') {
							toast.error(`${job.filename}: ${message}`);
							void settleBatch();
						} else {
							connectionErrors[document.id] = message;
						}
					}
				})
			}];
		}));
		trackers = next;
		for (const tracker of Object.values(next)) void tracker.progress.startTracking(tracker.jobId);
		return () => {
			active = false;
			for (const tracker of Object.values(next)) tracker.progress.stopTracking();
		};
	});

	function reconnect(documentId: string) {
		const tracker = trackers[documentId];
		connectionErrors[documentId] = '';
		void tracker.progress.startTracking(tracker.jobId);
	}

</script>

<div class="mx-auto w-full max-w-3xl space-y-6">
	<Dropzone
		on:drop={handleFilesSelect}
		on:dragenter={upload.handleDragEnter}
		on:dragleave={upload.handleDragLeave}
		accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx"
		maxSize={MAX_DOCUMENT_BYTES - 1}
		multiple={true}
		disabled={isLocked || upload.isSaving}
		aria-disabled={isLocked || upload.isSaving}
		disableDefaultStyles={true}
		containerClasses="flex min-h-60 w-full flex-col items-center justify-center rounded-xl border border-dashed px-6 py-10 text-center outline-none transition-colors duration-200
		{isLocked
			? 'cursor-not-allowed border-border bg-muted/30 opacity-60'
			: upload.isDragging
				? 'cursor-pointer border-primary bg-primary/5'
				: 'cursor-pointer border-border bg-background hover:border-primary/50 hover:bg-accent/30 dark:bg-card/20'}"
	>
		<div class="flex flex-col items-center">
			<div
				class="mb-4 flex size-16 items-center justify-center rounded-full bg-primary/5 text-primary transition-transform duration-200 {upload.isDragging &&
				!isLocked
					? 'scale-105'
					: ''}"
			>
				<FileTextIcon class="size-8" strokeWidth={1.8} />
			</div>
			<p class="text-base font-semibold text-foreground">Add documents</p>
			{#if isLocked}
				<p class="mt-1 text-sm text-muted-foreground">
					{documentFlow === 'processing'
						? 'Upload unavailable while your documents are processing'
						: 'Upload unavailable once your documents are ready'}
				</p>
			{:else}
				<p class="mt-1 text-sm text-muted-foreground">
					Drag files here or
					<span class="font-medium text-primary underline underline-offset-2">browse</span>
				</p>
			{/if}
			<p class="mt-2 text-xs tracking-wide text-muted-foreground uppercase">PDF or DOCX · Each smaller than 10 MiB</p>
		</div>
	</Dropzone>

	<div class="flex items-center justify-between text-sm text-muted-foreground" aria-live="polite">
		<span>{upload.documents.length}/{MAX_DOCUMENTS} documents selected</span>
		{#if documentFlow === 'processing'}<span>{completedCount}/{upload.documents.length} ready</span>{/if}
	</div>
	{#if failedCount > 0}
		<div class="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm" role="alert">
			<p class="font-medium text-destructive">All documents must succeed before you can chat.</p>
			<p class="mt-1 text-muted-foreground">{failedCount} document{failedCount === 1 ? '' : 's'} failed. {documentFlow === 'processing' ? 'The remaining documents are still processing.' : 'You can edit the selection and reprocess all documents.'}</p>
		</div>
	{/if}
	{#if hasPreviousBatch && !isLocked}
		<p class="text-sm text-muted-foreground">Processing again creates a new conversation and reprocesses every selected document, including successful files. Embedding charges may apply.</p>
	{/if}
	{#if upload.documents.length > 0}
		<ul class="space-y-3">
			{#each upload.documents as document (document.id)}
				{@const tracker = trackers[document.id]}
				{@const update = updates[document.id]}
				<li class="flex items-center rounded-xl border px-4 py-3">
					<div class="flex min-w-0 flex-1 items-center gap-3 sm:gap-4">
						{@render DocIcon(document.type)}
						<div class="min-w-0 flex-1 space-y-1">
							<p class="truncate text-sm font-semibold text-foreground">{document.name}</p>
							{#if !tracker}
								<div class="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
									<span>{document.type.toUpperCase()}</span>
									<Dot class=" size-4" />
									<span>{formatFileSize(document.size)}</span>
									<span
										class="inline-flex items-center gap-1.5 rounded-full bg-gray-200 px-2 py-1 font-medium text-gray-700"
									>
										<span class="size-2 rounded-full bg-gray-600"></span>
										{documentFlow === 'processing' ? 'Uploading' : 'Selected'}
									</span>
								</div>
							{/if}
							{#if tracker}
								<div class="space-y-2 text-xs text-muted-foreground" aria-live="polite">
									<p class:text-destructive={update?.stage === 'error'}>{connectionErrors[document.id] || update?.message || tracker.progress.message}</p>
									{#if connectionErrors[document.id]}
										<Button variant="outline" size="sm" onclick={() => reconnect(document.id)}>Reconnect</Button>
									{:else if update?.stage === 'completed'}
										<span class="inline-flex rounded-full bg-primary/10 px-2 py-1 font-medium text-primary">Ready</span>
									{:else if update?.stage !== 'error'}
										<div class="flex items-center gap-3">
											<Progress value={tracker.progress.progress} class="h-2 min-w-0 flex-1" />
											<span class="w-10 shrink-0 text-right tabular-nums">{tracker.progress.progress}%</span>
										</div>
									{/if}
								</div>
							{/if}
							{#if documentFlow == 'ready'}
								<div class="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
									<span>{document.type.toUpperCase()}</span>
									<span aria-hidden="true">·</span>
									<span>{formatFileSize(document.size)}</span>
									<span
										class="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2 py-1 font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
									>
										<span class="size-2 rounded-full bg-emerald-500"></span>
										Ready
									</span>
								</div>
							{/if}
						</div>
					</div>
					{#if !isLocked && !upload.isSaving}
						<button
							class="ml-4 shrink-0"
							aria-label={`Remove ${document.name}`}
							onclick={() => handleFileRemoval(document.id)}
						>
							<Trash
								class="size-5 text-muted-foreground transition duration-150 hover:text-red-700"
							/>
						</button>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
</div>

{#snippet DocIcon(type: StoredDocumentType)}
	<div
		class="flex size-14 shrink-0 items-center justify-center rounded-lg {type === 'pdf'
			? 'bg-red-300/10'
			: 'bg-sky-300/10'}"
	>
		{#if type === 'pdf'}
			<File class="size-8 text-red-700" strokeWidth={1.8} />
		{:else}
			<FileTextIcon class="size-8 text-sky-700" strokeWidth={1.8} />
		{/if}
	</div>
{/snippet}
