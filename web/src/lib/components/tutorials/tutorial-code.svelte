<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import Copy from '@lucide/svelte/icons/copy';
	import Check from '@lucide/svelte/icons/check';
	import { Button } from '$lib/components/ui/button';
	import type { TutorialCode } from '$lib/tutorials/inngest-types';

	let { block }: { block: TutorialCode } = $props();
	let copied = $state(false);
	let feedback = $state('');
	let codeViewport = $state<HTMLPreElement>();
	let scrollable = $state(false);
	let timer: ReturnType<typeof setTimeout> | undefined;

	onMount(() => {
		const viewport = codeViewport;
		if (!viewport) return;
		const observer = new ResizeObserver(() => {
			scrollable = viewport.scrollWidth > viewport.clientWidth || viewport.scrollHeight > viewport.clientHeight;
		});
		observer.observe(viewport);
		const content = viewport.querySelector('code');
		if (content) observer.observe(content);
		return () => observer.disconnect();
	});

	async function copy() {
		try {
			await navigator.clipboard.writeText(block.code);
			copied = true;
			feedback = 'Copied to clipboard';
			clearTimeout(timer);
			timer = setTimeout(() => { copied = false; feedback = ''; }, 2500);
		} catch {
			feedback = 'Clipboard unavailable. Select and copy the code manually.';
		}
	}

	onDestroy(() => clearTimeout(timer));
</script>

<figure class="code-block">
	<figcaption>
		<div class="min-w-0">
			<span class="kind">{block.kind}</span>
			<div class="path">{block.path}</div>
		</div>
		<Button variant="ghost" size="sm" onclick={copy} aria-label={'Copy code from ' + block.path}>
			{#if copied}<Check />{:else}<Copy />{/if}
			{copied ? 'Copied' : 'Copy'}
		</Button>
	</figcaption>
	{#if block.note}<p class="source-note">{block.note}</p>{/if}
	<pre bind:this={codeViewport} role="region" tabindex={scrollable ? 0 : undefined} aria-label={block.language + ' code: ' + block.path}><code>{#each block.code.split('\n') as line}<span class="code-line">{line || ' '}</span>{/each}</code></pre>
	{#if feedback}<div class="feedback" role="status">{feedback}</div>{/if}
</figure>

<style>
	.code-block { margin: 1rem 0; border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; background: var(--card); }
	figcaption { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: .75rem 1rem; border-bottom: 1px solid var(--border); }
	.kind { display: block; font-size: .65rem; font-weight: 650; letter-spacing: .07em; text-transform: uppercase; color: var(--muted-foreground); }
	.path { font: .75rem/1.6 ui-monospace, SFMono-Regular, monospace; overflow-wrap: anywhere; margin-top: .2rem; }
	pre { overflow: auto; margin: 0; padding: 1rem 0; background: var(--muted); font: .78rem/1.8 ui-monospace, SFMono-Regular, monospace; tab-size: 4; max-height: 32rem; }
	pre:focus-visible { outline: 2px solid var(--ring); outline-offset: -2px; }
	code { display: block; }
	.code-line { display: block; min-width: max-content; padding: 0 1rem; }
	.feedback { padding: .5rem 1rem; font-size: .75rem; border-top: 1px solid var(--border); color: var(--muted-foreground); }
	.source-note { padding: .75rem 1rem; font-size: .75rem; line-height: 1.7; color: var(--muted-foreground); border-bottom: 1px solid var(--border); }
</style>
