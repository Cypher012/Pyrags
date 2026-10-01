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
	export type DocumentFlow = 'selecting' | 'selected' | 'processing' | 'ready';
</script>

<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import { ArrowRight, Check } from '@lucide/svelte';
	import FileUpload from './file-upload.svelte';

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

<main class="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center pt-40">
	<div class="space-y-4">
		<h2
			class="text-center font-heading text-3xl font-semibold text-secondary-foreground sm:text-4xl"
		>
			Choose what you want to explore
		</h2>
		<p class="text-center text-muted-foreground">
			Add a PDF or DOCX, Prepare it then start asking questions
		</p>
	</div>

	<div
		class="mt-10 hidden w-full items-start sm:flex {selectingDocuments ? 'max-w-5xl' : 'max-w-3xl'}"
		aria-label="Document setup progress"
	>
		{#each steps as step, index (step.id)}
			{@const complete =
				(step.id === 1 && (documentFlow === 'processing' || documentFlow === 'ready')) ||
				(step.id === 2 && documentFlow === 'ready')}

			{@const active =
				(step.id === 1 && (documentFlow === 'selecting' || documentFlow === 'selected')) ||
				(step.id === 2 && documentFlow === 'processing') ||
				(step.id === 3 && documentFlow === 'ready')}

			<div
				class="flex min-w-0 items-start gap-2 sm:gap-3"
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

					<p class="mt-0.5 hidden text-xs text-muted-foreground sm:block">
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
				<span class="mx-2 mt-4 h-px min-w-4 flex-1 bg-border"></span>
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
		<div class="mt-16">
			<Button
				onclick={handleProcessDocument}
				disabled={documentFlow !== 'selected'}
				class="h-14 w-[22rem] rounded-xl text-base disabled:cursor-not-allowed disabled:bg-black/20 disabled:text-foreground"
			>
				Process documents <ArrowRight class="ml-3" />
			</Button>
		</div>
	{/if}
</main>
