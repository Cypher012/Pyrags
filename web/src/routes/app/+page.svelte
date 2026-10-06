<script module lang="ts">
	const steps = [
		{
			id: 1,
			label: 'Add documents',
			completedText: 'Documents selected'
		},
		{
			id: 2,
			label: 'Process documents',
			completedText: 'Documents ready'
		},
		{
			id: 3,
			label: 'Conversation',
			completedText: 'Ready to ask questions'
		}
	];
	export type DocumentFlow = 'selecting' | 'selected' | 'processing' | 'ready' | 'failed';
</script>

<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import { ArrowRight, Check } from '@lucide/svelte';
	import FileUpload from './file-upload.svelte';
	import { Trigger as SidebarTrigger } from '$lib/components/ui/sidebar';

	let documentFlow = $state<DocumentFlow>('selecting');

	const selectingDocuments = $derived(documentFlow === 'selecting');

	let fileUpload: FileUpload;

	async function handleProcessDocument() {
		documentFlow = 'processing';

		try {
			await fileUpload.uploadDocument();
		} catch {
			documentFlow = 'selected';
		}
	}

	const isLocked = $derived(documentFlow === 'processing' || documentFlow === 'ready');
</script>

<main
	class="relative mx-auto flex w-full max-w-5xl min-w-0 flex-1 flex-col items-center px-4 py-14 sm:px-6 sm:py-12 xl:p-20"
>
	<SidebarTrigger class="absolute top-2 left-4 size-10 md:hidden" />
	<div class="space-y-4">
		<h2
			class="text-center font-heading text-3xl font-semibold text-secondary-foreground sm:text-4xl"
		>
			Choose what you want to explore
		</h2>
		<p class="text-center text-muted-foreground">
			Add up to three PDF or DOCX documents, then explore them in one conversation
		</p>
	</div>

	<div
		class="mt-10 flex w-full flex-col items-center sm:flex-row sm:items-start {selectingDocuments
			? 'max-w-5xl'
			: 'max-w-3xl'}"
		aria-label="Document setup progress"
	>
		{#each steps as step, index (step.id)}
			{@const complete =
				(step.id === 1 && (documentFlow === 'processing' || documentFlow === 'ready')) ||
				(step.id === 2 && documentFlow === 'ready')}

			{@const active =
				(step.id === 1 &&
					(documentFlow === 'selecting' ||
						documentFlow === 'selected' ||
						documentFlow === 'failed')) ||
				(step.id === 2 && documentFlow === 'processing') ||
				(step.id === 3 && documentFlow === 'ready')}

			<div
				class="flex min-w-0 flex-col items-center gap-3 text-center sm:flex-row sm:items-start sm:text-left"
				aria-current={active ? 'step' : undefined}
			>
				<div
					class="flex size-8 shrink-0 items-center justify-center rounded-full text-xs {complete ||
					active
						? 'bg-primary text-primary-foreground'
						: 'bg-muted text-muted-foreground'}"
				>
					{#if complete}
						<Check class="size-4" />
					{:else}
						{step.id}
					{/if}
				</div>

				<div class="min-w-0 pt-0.5">
					<p
						class="text-xs font-medium {complete || active
							? 'text-foreground'
							: 'text-muted-foreground'}"
					>
						{step.id}. {step.label}
					</p>

					<p class="mt-0.5 text-xs text-muted-foreground">
						{#if step.id === 1}
							{documentFlow === 'selecting' ? 'Waiting for documents' : step.completedText}
						{:else if step.id === 2}
							{documentFlow === 'processing'
								? 'Processing documents'
								: documentFlow === 'ready'
									? step.completedText
									: 'Waiting to process'}
						{:else if step.id === 3}
							{documentFlow === 'ready' ? step.completedText : 'Waiting for documents to be ready'}
						{/if}
					</p>
				</div>
			</div>

			{@const isLastStep = index === steps.length - 1}

			{#if !isLastStep}
				<span
					aria-hidden="true"
					class="my-2 h-6 w-px shrink-0 bg-border sm:mx-2 sm:my-0 sm:mt-4 sm:h-px sm:w-auto sm:min-w-4 sm:flex-1"
				></span>
			{/if}
		{/each}
	</div>

	<div class="mt-12 w-full">
		<FileUpload
			bind:this={fileUpload}
			{isLocked}
			{documentFlow}
			onFlowChange={(flow) => (documentFlow = flow)}
		/>
	</div>
	{#if !isLocked}
		<div class="mt-16 w-full max-w-[22rem]">
			<Button
				onclick={handleProcessDocument}
				disabled={documentFlow !== 'selected' && documentFlow !== 'failed'}
				class="h-14 w-full rounded-xl text-base disabled:cursor-not-allowed disabled:bg-black/20 disabled:text-foreground"
			>
				{documentFlow === 'failed' ? 'Reprocess all documents' : 'Process documents'}
				<ArrowRight class="ml-3" />
			</Button>
		</div>
	{/if}
</main>
