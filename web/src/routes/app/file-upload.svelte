<script lang="ts">
	import {
		formatFileSize,
		useFileUpload,
		type DropDetail
	} from '$lib/hooks/use-file-upload.svelte';
	import { Progress } from '$lib/components/ui/progress/index.js';
	import FileTextIcon from '@lucide/svelte/icons/file-text';
	import Dropzone from 'svelte-file-dropzone';
	import { onMount } from 'svelte';
	import { useUploadProgress } from '$lib/hooks/use-upload-progress.svelte';
	import { Dot, File, Trash } from '@lucide/svelte';
	import type { StoredDocumentType } from '$lib/indexed-db/documents';
	import type { DocumentFlow } from './+page.svelte';

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

	const processing = useUploadProgress({
		onCompleted: async () => {
			onFlowChange('ready');
			await upload.clearStoredDocuments();
		},

		onError: () => {
			onFlowChange('selected');
		}
	});

	$effect(() => {
		const jobId = upload.uploadedData?.job_id;

		if (!jobId) return;

		processing.startTracking(jobId);

		return () => {
			processing.stopTracking();
		};
	});
</script>

<div class="mx-auto w-full max-w-3xl space-y-6">
	<Dropzone
		on:drop={handleFilesSelect}
		on:dragenter={upload.handleDragEnter}
		on:dragleave={upload.handleDragLeave}
		accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx"
		maxSize={5242880}
		multiple={false}
		disabled={isLocked}
		aria-disabled={isLocked}
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
						? 'Upload unavailable while your document is processing'
						: 'Upload unavailable once your document is ready'}
				</p>
			{:else}
				<p class="mt-1 text-sm text-muted-foreground">
					Drag files here or
					<span class="font-medium text-primary underline underline-offset-2">browse</span>
				</p>
			{/if}
			<p class="mt-2 text-xs tracking-wide text-muted-foreground uppercase">PDF or DOCX</p>
		</div>
	</Dropzone>

	{#if upload.documents.length > 0}
		<ul>
			{#each upload.documents as document (document.id)}
				<li class="flex items-center rounded-xl border px-4 py-3">
					<div class="flex min-w-0 flex-1 items-center gap-4">
						{@render DocIcon(document.type)}
						<div class="min-w-0 flex-1 space-y-1">
							<p class="truncate text-sm font-semibold text-foreground">{document.name}</p>
							{#if documentFlow == 'selected'}
								<div class="flex items-center gap-2 text-xs text-muted-foreground">
									<span>{document.type.toUpperCase()}</span>
									<Dot class=" size-4" />
									<span>{formatFileSize(document.size)}</span>
									<span
										class="inline-flex items-center gap-1.5 rounded-full bg-gray-200 px-2 py-1 font-medium text-gray-700"
									>
										<span class="size-2 rounded-full bg-gray-600"></span>
										Selected
									</span>
								</div>
							{/if}
							{#if documentFlow == 'processing'}
								<div class="space-y-2 text-xs text-muted-foreground">
									<p>{processing.message}</p>
									<div class="flex items-center gap-3">
										<Progress
											value={processing.progress}
											class="h-2 min-w-0 flex-1 [&_[data-slot=progress-indicator]]:bg-emerald-500"
										/>
										<span class="w-10 shrink-0 text-right text-xs tabular-nums"
											>{processing.progress}%</span
										>
									</div>
								</div>
							{/if}
							{#if documentFlow == 'ready'}
								<div class="flex items-center gap-2 text-xs text-muted-foreground">
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
					{#if documentFlow == 'selected'}
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
		class="flex size-14 items-center justify-center rounded-lg {type === 'pdf'
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
