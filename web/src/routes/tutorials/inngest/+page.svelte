<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import Check from '@lucide/svelte/icons/check';
	import List from '@lucide/svelte/icons/list';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import BookOpen from '@lucide/svelte/icons/book-open';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';
	import { toggleMode } from 'mode-watcher';
	import { Button } from '$lib/components/ui/button';
	import { Progress } from '$lib/components/ui/progress';
	import * as Sheet from '$lib/components/ui/sheet';
	import TutorialCode from '$lib/components/tutorials/tutorial-code.svelte';
	import WorkflowWalkthrough from '$lib/components/tutorials/workflow-walkthrough.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const storageKey = 'pyrags:inngest-workbook:v1';
	const groups = ['Understand', 'Implement', 'Run & ship'] as const;
	let selected = $state(0);
	let completed = $state<string[]>([]);
	let ready = $state(false);
	let storageWarning = $state('');
	let menuOpen = $state(false);
	let heading = $state<HTMLHeadingElement>();
	let lesson = $derived(data.lessons[selected]);
	let percentage = $derived(Math.round(completed.length / data.lessons.length * 100));

	function indexFromHash() {
		return data.lessons.findIndex((item) => '#' + item.id === window.location.hash);
	}

	onMount(() => {
		try {
			const stored = JSON.parse(localStorage.getItem(storageKey) || 'null');
			if (stored && typeof stored === 'object') {
				if (Array.isArray(stored.completed)) {
					completed = data.lessons.filter((item) => stored.completed.includes(item.id)).map((item) => item.id);
				}
				const savedIndex = data.lessons.findIndex((item) => item.id === stored.lesson);
				if (savedIndex >= 0) selected = savedIndex;
			}
		} catch {
			storageWarning = 'Saved progress could not be read. You can still use the workbook.';
		}
		const hashIndex = indexFromHash();
		if (hashIndex >= 0) selected = hashIndex;
		ready = true;

		function syncHash() {
			const next = indexFromHash();
			if (next >= 0) selected = next;
		}
		window.addEventListener('hashchange', syncHash);
		window.addEventListener('popstate', syncHash);
		return () => {
			window.removeEventListener('hashchange', syncHash);
			window.removeEventListener('popstate', syncHash);
		};
	});

	$effect(() => {
		if (!ready) return;
		try {
			localStorage.setItem(storageKey, JSON.stringify({ completed, lesson: data.lessons[selected].id }));
		} catch {
			storageWarning = 'Progress cannot be saved in this browser. It will last for this visit only.';
		}
	});

	async function navigate(index: number) {
		selected = index;
		menuOpen = false;
		await goto('#' + data.lessons[index].id, { noScroll: true, keepFocus: true });
		await tick();
		heading?.focus({ preventScroll: true });
		window.scrollTo({ top: 0, behavior: 'instant' });
	}

	function toggleComplete() {
		completed = completed.includes(lesson.id)
			? completed.filter((id) => id !== lesson.id)
			: [...completed, lesson.id];
	}

	async function reset() {
		if (!window.confirm('Reset all workbook progress on this browser? This does not change your code or database.')) return;
		completed = [];
		await navigate(0);
	}
</script>

<svelte:head>
	<title>Inngest workbook · Pyrags</title>
	<meta name="description" content="A local, hands-on guide to durable document ingestion in Pyrags." />
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

{#snippet navigation()}
	<nav aria-label="Workbook lessons" class="lesson-nav">
		{#each groups as group}
			<div class="nav-group">
				<h2>{group}</h2>
				{#each data.lessons as item, index}
					{#if item.group === group}
						<a
							href={'#' + item.id}
							class:current={selected === index}
							aria-current={selected === index ? 'step' : undefined}
							onclick={(event) => { event.preventDefault(); navigate(index); }}
						>
							<span class:done={completed.includes(item.id)} class="lesson-number">
								{#if completed.includes(item.id)}<Check size={13} aria-label="Completed" />{:else}{String(index + 1).padStart(2, '0')}{/if}
							</span>
							<span>{item.title}</span>
						</a>
					{/if}
				{/each}
			</div>
		{/each}
	</nav>
{/snippet}

{#snippet progressSummary()}
	<div class="progress-summary">
		<div class="progress-text"><span>Your progress</span><span>{completed.length} / {data.lessons.length}</span></div>
		<Progress value={percentage} aria-label="Workbook completion" class="h-1.5" />
		<p>Saved on this browser. Mark lessons yourself.</p>
		<Button variant="ghost" size="sm" class="-ml-2 text-muted-foreground" onclick={reset}>Reset progress</Button>
	</div>
{/snippet}

{#snippet architecture()}
	<figure class="architecture" aria-label="Proposed durable ingestion architecture">
		<figcaption>Target flow · extracted text is the durable input</figcaption>
		<ol>
			<li><strong>SvelteKit</strong><span>Authenticated upload</span></li>
			<li><strong>FastAPI</strong><span>Validate & extract</span></li>
			<li><strong>PostgreSQL</strong><span>Commit source + job</span></li>
			<li><strong>Inngest</strong><span>Event → signed API calls</span></li>
			<li><strong>Python steps</strong><span>Chunk → embed → save</span></li>
		</ol>
		<p>Vectors & status return to PostgreSQL. The existing UI reads progress through FastAPI.</p>
	</figure>
{/snippet}

<a class="skip-link" href="#lesson-content">Skip to lesson</a>
<header class="workbook-header">
	<div class="brand">
		<a href="/" aria-label="Pyrags home"><BookOpen size={20} /><strong>Pyrags</strong></a>
		<span class="divider">/</span>
		<span class="header-label">Engineering workbook</span>
	</div>
	<div class="header-actions">
		<span class="local-label"><span></span>Local development only</span>
		<Button href="/app" variant="ghost" size="sm" class="hidden sm:inline-flex">Back to app <ArrowRight /></Button>
		<Button variant="ghost" size="icon-sm" onclick={toggleMode} aria-label="Toggle theme" title="Toggle theme">
			<Sun class="size-4 dark:hidden" />
			<Moon class="hidden size-4 dark:block" />
		</Button>
		<Button variant="outline" size="sm" class="lg:hidden" onclick={() => menuOpen = true} aria-label="Open lesson navigation"><List /> Lessons</Button>
	</div>
</header>

<div class="workbook">
	<aside class="desktop-sidebar">
		<div class="course-label">Pyrags / backend track</div>
		<h1>Durable ingestion<br />with Inngest</h1>
		<p class="sidebar-description">Learn it by changing<br />the code you already have.</p>
		{@render progressSummary()}
		{@render navigation()}
		<div class="sidebar-note">17 lessons · self-paced<br />PostgreSQL + FastAPI + SvelteKit<br />No Redis. No automatic code execution.</div>
	</aside>

	<main id="lesson-content" class="lesson-content">
		<div class="lesson-meta">
			<span>{lesson.group}</span>
			<span>Lesson {String(selected + 1).padStart(2, '0')} of {data.lessons.length}</span>
		</div>
		{#key lesson.id}
			<article>
				<div class="lesson-title">
					<h2 bind:this={heading} tabindex="-1">{lesson.title}</h2>
					<p>{lesson.summary}</p>
				</div>
				<div class="scope-note"><BookOpen size={16} /><p>Complete reference code for your project. Examples do not execute here or modify your backend automatically. Completion is self-reported.</p></div>
				{#if storageWarning}<p role="status" class="storage-warning">{storageWarning}</p>{/if}
				<section aria-label="Concept">
					{#each lesson.concepts as concept}<p class="body-copy">{concept}</p>{/each}
				</section>
				{#if lesson.diagram === 'architecture'}{@render architecture()}{/if}
				{#if lesson.diagram === 'simulation'}<WorkflowWalkthrough />{/if}

				<section class="why-section">
					<h3>Why are we doing this?</h3>
					<p>{lesson.why}</p>
				</section>

				<section class="section-block" aria-label="Existing project context">
					<div class="section-heading"><span class="section-number">01</span><h3>In your codebase</h3></div>
					<p class="section-description">These excerpts come directly from your current files. They are context, not replacement code.</p>
					{#each lesson.context as block}<TutorialCode {block} />{/each}
				</section>

				<section class="section-block" aria-label="Implementation exercise">
					<div class="section-heading"><span class="section-number">02</span><h3>Your task</h3></div>
					<div class="task-panel">
						<div class="task-label">{lesson.group === 'Understand' ? 'Read & reason about' : 'Work in these files'}</div>
						<ul class="file-list">{#each lesson.files as path}<li><code>{path}</code></li>{/each}</ul>
						<ol class="task-list">{#each lesson.tasks as task}<li>{task}</li>{/each}</ol>
					</div>
					{#each lesson.exercise || [] as block}<TutorialCode {block} />{/each}
					{#if lesson.hint}
						<details class="reveal">
							<summary>Need a hint? <span>Reveal a narrow reference</span></summary>
							<div><p>{lesson.hint.explanation}</p>{#if lesson.hint.code}<TutorialCode block={lesson.hint.code} />{/if}</div>
						</details>
					{/if}
				</section>

				<section class="section-block">
					<div class="section-heading"><span class="section-number">03</span><h3>Verify it</h3></div>
					<ul class="verify-list">{#each lesson.verify as item}<li><span class="check-box" aria-hidden="true"></span>{item}</li>{/each}</ul>
					<div class="expected"><strong>Expected result</strong><p>{lesson.expected}</p></div>
					{#if lesson.checkpoint}
						<details class="reveal">
							<summary>Check your understanding</summary>
							<div><p><strong>{lesson.checkpoint.question}</strong></p><p>{lesson.checkpoint.answer}</p></div>
						</details>
					{/if}
				</section>

				<section class="references" aria-label="Official references">
					<h3>Go deeper</h3>
					{#each lesson.references as reference}
						<a href={reference.url} target="_blank" rel="noreferrer">{reference.label}<ExternalLink size={13} /><span class="sr-only">(opens in a new tab)</span></a>
					{/each}
				</section>

				<footer class="lesson-footer">
					<div class="completion-row">
						<Button variant={completed.includes(lesson.id) ? 'secondary' : 'default'} onclick={toggleComplete} aria-pressed={completed.includes(lesson.id)}>
							<Check /> {completed.includes(lesson.id) ? 'Completed · undo' : 'Mark lesson complete'}
						</Button>
						<span>{completed.includes(lesson.id) ? 'Nice. Your progress is recorded here.' : 'Finished the checks? Save your progress.'}</span>
					</div>
					<div class="pager">
						<Button variant="ghost" onclick={() => navigate(selected - 1)} disabled={selected === 0}><ArrowLeft /> Previous</Button>
						<span>{selected + 1} / {data.lessons.length}</span>
						<Button variant="outline" onclick={() => navigate(selected + 1)} disabled={selected === data.lessons.length - 1}>Next lesson <ArrowRight /></Button>
					</div>
					{#if completed.length === data.lessons.length}
						<p class="course-complete" role="status">All lessons marked complete. Your next challenge: design a second workflow and explain its recovery boundaries.</p>
					{/if}
				</footer>
			</article>
		{/key}
	</main>
</div>

<Sheet.Root bind:open={menuOpen}>
	<Sheet.Content side="left" class="w-[min(90vw,340px)] gap-0 overflow-y-auto motion-reduce:animate-none">
		<Sheet.Header class="px-5 pt-6">
			<Sheet.Title>Inngest workbook</Sheet.Title>
			<Sheet.Description>Choose a lesson. Progress stays in this browser.</Sheet.Description>
		</Sheet.Header>
		<div class="px-5 pb-8">{@render progressSummary()}{@render navigation()}</div>
	</Sheet.Content>
</Sheet.Root>

<style>
	.skip-link { position: fixed; left: 1rem; top: -5rem; z-index: 100; background: var(--foreground); color: var(--background); padding: .75rem 1rem; border-radius: var(--radius); }
	.skip-link:focus { top: .5rem; }
	.workbook-header { position: sticky; top: 0; z-index: 20; height: 4rem; padding: 0 1.75rem; background: var(--background); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
	.brand, .brand a, .header-actions { display: flex; align-items: center; gap: .75rem; }
	.brand a { gap: .5rem; }
	.brand strong { font-size: 1rem; letter-spacing: -.025em; }
	.divider { color: var(--border); }
	.header-label { font-size: .8rem; color: var(--muted-foreground); }
	.local-label { display: flex; gap: .4rem; align-items: center; font-size: .7rem; color: var(--muted-foreground); }
	.local-label > span { width: .35rem; height: .35rem; border-radius: 50%; background: var(--success); }
	.workbook { display: grid; grid-template-columns: 280px minmax(0, 1fr); max-width: 1440px; margin: 0 auto; }
	.desktop-sidebar { position: sticky; top: 4rem; height: calc(100dvh - 4rem); overflow-y: auto; padding: 2rem 1.5rem; border-right: 1px solid var(--border); scrollbar-width: thin; }
	.course-label { text-transform: uppercase; letter-spacing: .08em; color: var(--muted-foreground); font-size: .65rem; font-weight: 600; }
	.desktop-sidebar h1 { margin: .65rem 0; font-size: 1.25rem; font-weight: 600; line-height: 1.4; letter-spacing: -.03em; }
	.sidebar-description { color: var(--muted-foreground); font-size: .8rem; line-height: 1.7; }
	.progress-summary { padding: 1.2rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1.1rem; }
	.progress-text { display: flex; align-items: center; justify-content: space-between; font-size: .75rem; margin-bottom: .7rem; font-weight: 500; }
	.progress-summary p { color: var(--muted-foreground); font-size: .65rem; margin: .65rem 0 .25rem; }
	.nav-group { margin: 1.2rem 0; }
	.nav-group h2 { text-transform: uppercase; letter-spacing: .1em; color: var(--muted-foreground); font-size: .6rem; font-weight: 650; margin: 0 0 .6rem .4rem; }
	.lesson-nav a { display: flex; align-items: flex-start; gap: .6rem; padding: .6rem .5rem; margin: .125rem 0; border-radius: var(--radius); font-size: .75rem; line-height: 1.5; color: var(--muted-foreground); }
	.lesson-nav a:hover { color: var(--foreground); background: var(--muted); }
	.lesson-nav a.current { color: var(--foreground); background: var(--accent); font-weight: 550; }
	.lesson-number { font: .65rem/1.8 ui-monospace, monospace; width: 1.25rem; flex-shrink: 0; display: flex; justify-content: center; }
	.lesson-number.done { color: var(--success); padding-top: .125rem; }
	.sidebar-note { border-top: 1px solid var(--border); padding-top: 1rem; margin-top: 1.5rem; font-size: .65rem; color: var(--muted-foreground); line-height: 1.9; }
	.lesson-content { min-width: 0; width: 100%; max-width: 900px; padding: 2.5rem 3rem 4rem; margin: 0 auto; scroll-margin-top: 5rem; }
	.lesson-meta { display: flex; align-items: center; justify-content: space-between; gap: 1rem; text-transform: uppercase; font-size: .65rem; font-weight: 550; letter-spacing: .08em; color: var(--muted-foreground); padding-bottom: 1.25rem; border-bottom: 1px solid var(--border); }
	.lesson-title { margin: 1.75rem 0; }
	.lesson-title h2 { font-size: clamp(1.65rem, 3vw, 2.25rem); font-weight: 550; letter-spacing: -.045em; line-height: 1.2; outline: none; }
	.lesson-title p { color: var(--muted-foreground); font-size: 1rem; line-height: 1.65; margin-top: .75rem; }
	.scope-note { display: flex; gap: .6rem; align-items: flex-start; color: var(--muted-foreground); background: var(--muted); padding: .75rem 1rem; font-size: .75rem; line-height: 1.65; margin-bottom: 1.5rem; border-radius: var(--radius); }
	.scope-note :global(svg) { flex-shrink: 0; margin-top: .2rem; }
	.body-copy { font-size: .9rem; line-height: 1.85; margin: .85rem 0; }
	.why-section { border-left: 2px solid var(--primary); padding: .5rem 0 .5rem 1rem; margin: 1.75rem 0; }
	.why-section h3 { font-size: .8rem; font-weight: 650; }
	.why-section p { font-size: .85rem; line-height: 1.8; margin-top: .4rem; color: var(--muted-foreground); }
	.section-block { margin-top: 2.25rem; }
	.section-heading { display: flex; align-items: center; gap: .6rem; margin-bottom: .65rem; }
	.section-heading h3 { font-size: 1rem; font-weight: 600; }
	.section-number { font: .7rem ui-monospace, monospace; color: var(--muted-foreground); }
	.section-description { font-size: .8rem; line-height: 1.7; color: var(--muted-foreground); }
	.task-panel { border: 1px solid var(--border); border-top: 2px solid var(--warning); padding: 1.2rem; border-radius: var(--radius); }
	.task-label { font-size: .65rem; font-weight: 650; text-transform: uppercase; letter-spacing: .06em; color: var(--muted-foreground); }
	.file-list { list-style: none; padding: 0; margin: .5rem 0 1rem; }
	.file-list code { font: .75rem/1.8 ui-monospace, monospace; overflow-wrap: anywhere; }
	.task-list { padding-left: 1.2rem; margin: 0; font-size: .85rem; line-height: 1.8; }
	.task-list li { padding-left: .25rem; margin: .55rem 0; }
	.task-list li::marker { color: var(--warning); font-size: .75rem; }
	.reveal { border: 1px solid var(--border); margin-top: 1rem; border-radius: var(--radius); font-size: .8rem; }
	.reveal summary { cursor: pointer; padding: .8rem 1rem; font-weight: 550; }
	.reveal summary span { color: var(--muted-foreground); font-size: .7rem; margin-left: .5rem; font-weight: 400; }
	.reveal > div { padding: 0 1rem 1rem; line-height: 1.8; }
	.reveal p + p { margin-top: .5rem; }
	.verify-list { list-style: none; padding: 0; margin: 1rem 0; }
	.verify-list li { display: flex; gap: .75rem; align-items: flex-start; font-size: .85rem; line-height: 1.8; margin: .65rem 0; }
	.check-box { width: .85rem; height: .85rem; margin-top: .32rem; border: 1px solid var(--border); border-radius: 2px; flex-shrink: 0; }
	.expected { background: var(--accent); padding: 1rem 1.2rem; border-radius: var(--radius); }
	.expected strong { font-size: .7rem; font-weight: 650; }
	.expected p { font-size: .85rem; line-height: 1.75; margin-top: .35rem; }
	.references { border-top: 1px solid var(--border); padding-top: 1.25rem; margin-top: 2rem; }
	.references h3 { text-transform: uppercase; font-size: .65rem; letter-spacing: .08em; font-weight: 600; color: var(--muted-foreground); margin-bottom: .7rem; }
	.references a { display: inline-flex; align-items: center; gap: .5rem; font-size: .8rem; margin: .25rem 1.25rem .25rem 0; text-decoration: underline; text-underline-offset: 3px; }
	.lesson-footer { margin-top: 2.25rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }
	.completion-row { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; }
	.completion-row > span { font-size: .7rem; color: var(--muted-foreground); }
	.pager { display: flex; align-items: center; justify-content: space-between; gap: .5rem; margin-top: 1.5rem; }
	.pager > span { color: var(--muted-foreground); font: .7rem ui-monospace, monospace; }
	.course-complete { color: var(--success); font-size: .85rem; line-height: 1.75; margin-top: 1.5rem; }
	.storage-warning { font-size: .75rem; color: var(--warning); margin: .75rem 0; }
	.architecture { margin: 1.75rem 0; }
	.architecture figcaption { font-size: .65rem; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--muted-foreground); margin-bottom: .75rem; }
	.architecture ol { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border: 1px solid var(--border); border-radius: var(--radius); list-style: none; padding: 0; overflow: hidden; }
	.architecture li { padding: .9rem .65rem; border-right: 1px solid var(--border); background: var(--card); }
	.architecture li:last-child { border: 0; }
	.architecture strong { display: block; font-size: .75rem; font-weight: 600; }
	.architecture li span { display: block; font-size: .65rem; line-height: 1.6; margin-top: .3rem; color: var(--muted-foreground); }
	.architecture p { font-size: .75rem; line-height: 1.7; color: var(--muted-foreground); margin-top: .65rem; }
	a:focus-visible, summary:focus-visible { outline: 2px solid var(--ring); outline-offset: 3px; }
	@media (max-width: 1023px) {
		.workbook { display: block; }
		.desktop-sidebar { display: none; }
		.lesson-content { padding: 2rem 2rem 3rem; max-width: 820px; }
	}
	@media (max-width: 640px) {
		.workbook-header { padding: 0 1rem; height: 3.5rem; }
		.header-label, .divider, .local-label { display: none; }
		.lesson-content { padding: 1.5rem 1rem 2.5rem; }
		.lesson-title { margin: 1.4rem 0; }
		.architecture ol { grid-template-columns: 1fr; }
		.architecture li { border-right: 0; border-bottom: 1px solid var(--border); display: grid; grid-template-columns: 7rem 1fr; align-items: center; }
		.architecture li span { margin-top: 0; }
		.reveal summary span { display: none; }
		.task-panel { padding: 1rem; }
	}
	@media (prefers-reduced-motion: reduce) {
		:global(.progress-summary [data-slot="progress-indicator"]) { transition: none; }
	}
</style>
