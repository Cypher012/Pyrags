<script lang="ts">
	import { Button } from '$lib/components/ui/button';

	const states = [
		{ title: 'A user uploads a PDF', detail: 'SvelteKit sends an authenticated multipart request to FastAPI. No durable job exists yet.', postgres: 'No job yet', inngest: 'No event yet', memory: 'Original bytes in the request' },
		{ title: 'FastAPI extracts the text', detail: 'The current PDF extractor retains one-based page numbers. This work is still in the upload request, not an Inngest step.', postgres: 'No committed job yet', inngest: 'No event yet', memory: 'Bytes + extracted source parts' },
		{ title: 'Commit the recovery input', detail: 'One transaction creates the conversation, PROCESSING document and ingestion job. Source text is now durable; the original bytes can be discarded.', postgres: 'Source parts + job, PROCESSING', inngest: 'No event yet: delivery gap', memory: 'Temporary request data' },
		{ title: 'Publish the event', detail: 'FastAPI awaits event acceptance. The payload contains only job_id. An outbox is needed to automatically recover a crash before this send.', postgres: 'Committed job + source parts', inngest: 'Accepted document.uploaded event', memory: 'No recovery input needed here' },
		{ title: 'Start the function', detail: 'Inngest calls /api/inngest on your Python host. The handler validates the job ID and schedules the first step.', postgres: 'Job remains PROCESSING', inngest: 'Run started', memory: 'A fresh handler invocation' },
		{ title: 'Chunk preparation succeeds', detail: 'prepare_chunks saves the chunk manifest in PostgreSQL. Inngest records a small count result for prepare-chunks.', postgres: 'Source + immutable prepared chunks', inngest: 'prepare-chunks ✓; saved counts', memory: 'Temporary chunk objects released' },
		{ title: 'Embedding fails once', detail: 'A transient provider error escapes the embedding step. There was no vector commit. This is a retryable attempt, not a terminal document failure.', postgres: 'PROCESSING; manifest retained', inngest: 'embed-store-0 failed; retry pending', memory: 'Failed invocation can disappear' },
		{ title: 'Retry the failed step', detail: 'The handler replays. prepare-chunks returns its recorded counts; its body does not rerun. embed-store-0 tries again on your API host.', postgres: 'Same persisted manifest', inngest: 'prepare-chunks reused; batch retry', memory: 'Fresh session and embedding call' },
		{ title: 'Store the batch', detail: 'The batch transaction commits vectors with the existing unique chunk key. Inngest checkpoints the small stored count after the step returns.', postgres: 'Chunks + 1,024-dimensional vectors', inngest: 'embed-store-0 ✓; saved count', memory: 'Embedding arrays can be discarded' },
		{ title: 'Complete and update the UI', detail: 'finish_job verifies the expected rows and marks READY/completed. The UI reads that snapshot and navigates using conversation_id.', postgres: 'READY, completed, 100%', inngest: 'finish-document ✓; run completed', memory: 'No running Python task required' }
	];
	let index = $state(0);
	let current = $derived(states[index]);
</script>

<section class="walkthrough" aria-label="Workflow simulation">
	<div class="simulation-label">Simulation only · no requests or paid calls</div>
	<ol class="milestones" aria-label="Execution timeline">
		{#each states as state, position}
			<li><button onclick={() => index = position} aria-label={'Show step ' + (position + 1) + ': ' + state.title} aria-current={index === position ? 'step' : undefined} class:past={position < index} class:active={position === index}>{position + 1}</button></li>
		{/each}
	</ol>
	<div aria-live="polite" aria-atomic="true">
		<h3>{current.title}</h3>
		<p>{current.detail}</p>
		<dl>
			<div><dt>PostgreSQL</dt><dd>{current.postgres}</dd></div>
			<div><dt>Inngest</dt><dd>{current.inngest}</dd></div>
			<div><dt>Python memory</dt><dd>{current.memory}</dd></div>
		</dl>
	</div>
	<div class="controls">
		<Button variant="ghost" size="sm" onclick={() => index = 0} disabled={index === 0}>Reset simulation</Button>
		<div class="flex gap-2">
			<Button variant="outline" size="sm" onclick={() => index--} disabled={index === 0}>Back</Button>
			<Button size="sm" onclick={() => index++} disabled={index === states.length - 1}>{index === 6 ? 'Retry failed step' : 'Next step'}</Button>
		</div>
	</div>
</section>

<style>
	.walkthrough { border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; margin: 1.5rem 0; }
	.simulation-label { color: var(--muted-foreground); font-size: .7rem; margin-bottom: 1rem; }
	.milestones { display: flex; flex-wrap: wrap; gap: .4rem; padding: 0; list-style: none; margin: 0 0 1.25rem; }
	.milestones button { width: 2rem; height: 2rem; border: 1px solid var(--border); border-radius: 50%; font-size: .75rem; }
	.milestones button:hover { background: var(--muted); }
	.milestones button:focus-visible { outline: 2px solid var(--ring); outline-offset: 3px; }
	.milestones button.active { background: var(--foreground); color: var(--background); border-color: var(--foreground); }
	.milestones button.past { border-color: var(--primary); color: var(--primary); }
	h3 { font-size: 1rem; font-weight: 600; }
	p { margin: .5rem 0 1rem; font-size: .875rem; line-height: 1.7; color: var(--muted-foreground); }
	dl { font-size: .8rem; margin: 0; }
	dl > div { display: grid; grid-template-columns: 8rem 1fr; gap: .5rem; padding: .65rem 0; border-top: 1px solid var(--border); }
	dt { font-weight: 600; }
	dd { margin: 0; color: var(--muted-foreground); }
	.controls { display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem; margin-top: 1rem; }
	@media (max-width: 450px) { dl > div { grid-template-columns: 1fr; gap: .2rem; } }
</style>
