<script lang="ts">
	import BrandMark from '$lib/assets/logo-mark.svg?component';
	import { ArrowUp, Check, FileText, Plus, Quote } from '@lucide/svelte';
	import { resolve } from '$app/paths';

	let activeTab = $state('document');
	let activeQuestion = $state(0);
	const examples = [
		{ question: 'What is the perceive–reason–act cycle?', answer: 'It’s the loop an agent uses to interact with its environment:', points: ['Perceive what’s happening through its sensors.', 'Reason about that information and choose an action.', 'Act, then observe what changes and repeat.'], excerpt: 'An agent perceives its environment, reasons about its observations, and takes actions to achieve its goals.' },
		{ question: 'Give me the main ideas in this document.', answer: 'Start with these three ideas from the course notes:', points: ['Agents observe and act within an environment.', 'Their decisions are directed toward a goal.', 'Multiple agents can work together as a system.'], excerpt: 'Agent-based systems are composed of agents that interact with one another and with their environment.' },
		{ question: 'Help me check my understanding.', answer: 'Try explaining these in your own words:', points: ['What does an agent need to perceive its environment?', 'How does reasoning connect an observation to an action?', 'What changes when several agents work together?'], excerpt: 'The perceive–reason–act cycle connects observations and decisions with actions in an environment.' }
	];
	const example = $derived(examples[activeQuestion]);
</script>

<div class="product-preview" aria-label="Interactive Pyrags preview with example course notes">
	<aside class="preview-nav">
		<div class="preview-brand"><BrandMark class="size-6" /><strong>Pyrags</strong></div>
		<a href={resolve('/sign-in')}><Plus class="size-3.5" /> New chat</a>
		<span class="preview-recents">Recents</span>
		<div class="preview-current">Agent-Based Systems</div>
		<div class="preview-other">Programming Paradigms</div>
		<div class="preview-account"><span>Y</span> Your workspace</div>
	</aside>
	<div class="preview-chat">
		<div class="preview-topbar"><FileText class="size-4" /><span>Agent-Based Systems</span><span class="preview-ready"><Check class="size-3" /> Ready</span></div>
		<div class="preview-messages" aria-live="polite">
			<div class="preview-question">{example.question}</div>
			<div class="preview-answer"><BrandMark class="size-5" /><div><p>{example.answer}</p><ol>{#each example.points as point (point)}<li>{point}</li>{/each}</ol></div></div>
			<button class="preview-citation" onclick={() => activeTab = 'sources'}><FileText class="size-4" /><span><strong>Introduction to Agent-Based Systems.pdf</strong><small>Page 12 · View source</small></span><Quote class="size-3.5" /></button>
			{#if activeTab === 'sources'}
				<div class="mobile-source"><p>{example.excerpt}</p><span>Agent-Based Systems.pdf · Page 12</span><button onclick={() => activeTab = 'document'}>Close source</button></div>
			{/if}
			<div class="preview-prompts" aria-label="Try an example question">{#each ['Explain a concept', 'Summarize', 'Study questions'] as label, index (label)}<button class:chosen={activeQuestion === index} onclick={() => activeQuestion = index}>{label}</button>{/each}</div>
		</div>
		<div class="preview-composer"><span>Ask a follow-up question…</span><a href={resolve('/sign-in')} aria-label="Sign in to ask your own question"><ArrowUp class="size-4" /></a></div>
		<p class="preview-limit">A little clarity, every day.</p>
	</div>
	<aside class="preview-document">
		<div class="preview-tabs"><button class:active={activeTab === 'document'} onclick={() => activeTab = 'document'}>Document</button><button class:active={activeTab === 'sources'} onclick={() => activeTab = 'sources'}>Sources</button></div>
		{#if activeTab === 'document'}
			<p class="preview-section-title">Conversation documents</p>
			<div class="preview-file"><FileText class="size-5" /><div><strong>Introduction to<br />Agent-Based Systems</strong><small>PDF <span>· Ready</span></small></div></div>
			<p class="preview-section-title">Preview</p>
			<div class="preview-paper"><strong>Introduction to<br />Agent-Based Systems</strong><hr /><b>What is an agent?</b><p>An agent observes its environment and takes actions to achieve its goals.</p><p>These decisions form a continuous perceive–reason–act cycle.</p><span>Page 12</span></div>
		{:else}
			<p class="preview-section-title">Behind this answer</p>
			<div class="preview-source"><Quote class="size-5" /><p>{example.excerpt}</p><strong>Agent-Based Systems.pdf</strong><span>Page 12</span></div>
			<p class="preview-source-note">Follow the answer back to its source.</p>
		{/if}
	</aside>
</div>

<style>
	.product-preview { display: grid; grid-template-columns: 145px minmax(0, 1fr) 215px; width: 100%; min-height: 500px; overflow: hidden; border: 1px solid #d9e0d8; border-radius: 14px; background: #fff; color: #23352a; font-family: 'Geist Variable', sans-serif; text-align: left; box-shadow: 0 32px 90px -40px #243e2945, 0 2px 8px #243e2908; }
	.preview-nav { display: flex; flex-direction: column; padding: 21px 12px; background: #f5f7f2; border-right: 1px solid #e5e9e2; font-size: 10px; }
	.preview-brand { display: flex; align-items: center; gap: 5px; margin-bottom: 30px; font-size: 17px; letter-spacing: -.6px; }
	.preview-nav > a { display: flex; align-items: center; gap: 6px; padding: 7px 3px; }
	.preview-recents { margin: 26px 3px 10px; color: #7b877a; font-size: 9px; }
	.preview-current, .preview-other { padding: 10px 7px; border-radius: 5px; line-height: 1.5; }
	.preview-current { background: #e7eee2; }
	.preview-other { color: #6d786e; }
	.preview-account { display: flex; align-items: center; gap: 7px; margin-top: auto; color: #637063; }
	.preview-account span { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: #e2e8df; }
	.preview-chat { display: flex; min-width: 0; flex-direction: column; }
	.preview-topbar { display: flex; align-items: center; gap: 7px; height: 52px; padding: 0 17px; border-bottom: 1px solid #e8ece5; font-size: 11px; font-weight: 500; }
	.preview-ready { display: flex; align-items: center; gap: 3px; margin-left: auto; color: #55794a; font-size: 9px; }
	.preview-messages { flex: 1; padding: 28px 24px 15px; }
	.preview-question { width: fit-content; max-width: 92%; margin-left: auto; padding: 10px 12px; border-radius: 11px 11px 3px 11px; background: #edf2e7; font-size: 11px; }
	.preview-answer { display: flex; align-items: flex-start; gap: 10px; margin-top: 29px; font-size: 11px; line-height: 1.9; }
	.preview-answer > :global(svg) { flex-shrink: 0; margin-top: 2px; }
	.preview-answer ol { padding-left: 15px; margin-top: 9px; list-style: decimal; }
	.preview-answer li { padding-left: 3px; margin-bottom: 6px; }
	.preview-citation { display: flex; align-items: center; gap: 9px; width: calc(100% - 30px); margin: 19px 0 0 30px; padding: 12px; border: 1px solid #dce7d3; border-radius: 8px; background: #f7f9f3; text-align: left; cursor: pointer; transition: background .2s, transform .2s; }
	.preview-citation:hover { background: #ecf2e5; transform: translateY(-2px); }
	.preview-citation > :global(svg) { flex-shrink: 0; }
	.preview-citation > :global(svg:last-child) { margin-left: auto; color: #72925f; }
	.preview-citation strong { display: block; font-size: 9px; font-weight: 500; }
	.preview-citation small { display: block; margin-top: 4px; color: #7b8677; font-size: 9px; }
	.preview-prompts { display: flex; flex-wrap: wrap; gap: 5px; margin: 17px 0 0 30px; }
	.preview-prompts button { padding: 5px 7px; border: 1px solid #e4e8df; border-radius: 5px; color: #7a8675; font-size: 9px; cursor: pointer; transition: background .2s; }
	.preview-prompts button:hover, .preview-prompts button.chosen { background: #f0f4e9; color: #365431; }
	.preview-composer { display: flex; justify-content: space-between; align-items: center; margin: 9px 24px 0; padding: 12px; border: 1px solid #e0e6db; border-radius: 10px; color: #8b9487; font-size: 10px; }
	.preview-composer a { display: grid; place-items: center; width: 25px; height: 25px; border-radius: 7px; background: #315339; color: #fff; }
	.preview-limit { padding: 9px 15px 15px; color: #929b8e; text-align: center; font-size: 8px; }
	.preview-document { padding: 0 15px 20px; border-left: 1px solid #e5e9e2; background: #fcfdfb; font-size: 10px; }
	.preview-tabs { display: flex; gap: 22px; height: 52px; border-bottom: 1px solid #e0e5da; }
	.preview-tabs button { position: relative; color: #939b8f; cursor: pointer; font-size: 10px; }
	.preview-tabs button.active { color: #2a4830; font-weight: 600; }
	.preview-tabs button.active::after { position: absolute; bottom: -1px; left: 0; width: 100%; height: 2px; border-radius: 2px; background: #315339; content: ''; }
	.preview-section-title { margin: 22px 0 11px; font-size: 10px; font-weight: 500; }
	.preview-file { display: flex; align-items: flex-start; gap: 9px; padding: 12px 10px; border-radius: 7px; background: #edf2e8; }
	.preview-file strong { font-size: 9px; line-height: 1.6; font-weight: 500; }
	.preview-file small { display: block; margin-top: 6px; font-size: 9px; color: #87917f; }
	.preview-file small span { color: #57824a; }
	.preview-paper { display: flex; flex-direction: column; min-height: 223px; padding: 18px 15px 12px; border: 1px solid #e3e8dd; border-radius: 6px; background: #fff; font-size: 9px; line-height: 1.8; box-shadow: 0 3px 8px #23352a04; }
	.preview-paper strong { font-size: 10px; line-height: 1.5; }
	.preview-paper hr { margin: 14px 0 19px; border-color: #bbc6b4; }
	.preview-paper b { margin-bottom: 9px; font-weight: 500; }
	.preview-paper p { margin-bottom: 8px; color: #778470; }
	.preview-paper span { margin: auto 0 0 auto; padding-top: 11px; color: #8f9b87; font-size: 8px; }
	.preview-source { padding: 18px 13px; border: 1px solid #dfe8d7; border-radius: 8px; background: #f4f7ef; }
	.preview-source > :global(svg) { color: #719559; }
	.preview-source p { margin: 16px 0 24px; font-size: 12px; line-height: 1.9; }
	.preview-source strong, .preview-source span { display: block; font-size: 9px; }
	.preview-source span { margin-top: 5px; color: #85917c; }
	.preview-source-note { margin-top: 15px; color: #8a967f; line-height: 1.8; font-size: 9px; }
	.mobile-source { display: none; }
	.product-preview :is(button, a):focus-visible { outline: 2px solid #527640; outline-offset: 3px; }
	@media (max-width: 1100px) { .product-preview { grid-template-columns: 110px minmax(0, 1fr) 190px; } .preview-nav { padding-inline: 9px; } .preview-messages { padding-inline: 17px; } .preview-citation { margin-left: 0; width: 100%; } .preview-prompts { margin-left: 0; } }
	@media (max-width: 640px) { .product-preview { grid-template-columns: minmax(0, 1fr); min-height: 430px; } .preview-nav, .preview-document { display: none; } .preview-messages { padding: 24px 18px 12px; } .preview-answer, .preview-question { font-size: 12px; } .preview-topbar { padding-inline: 18px; } .preview-citation strong { font-size: 10px; } .preview-composer { margin-inline: 18px; } }
	@media (prefers-reduced-motion: reduce) { .product-preview :is(button, a) { transition: none; } }
	@media (max-width: 640px) { .mobile-source { display: block; margin-top: 12px; padding: 14px; border: 1px solid #dce7d3; border-radius: 8px; background: #f4f7ef; font-size: 12px; line-height: 1.8; } .mobile-source > span { display: block; margin-top: 12px; font-size: 10px; color: #64765a; } .mobile-source > button { min-height: 36px; margin-top: 8px; font-size: 11px; color: #365431; cursor: pointer; } .preview-prompts button { min-height: 32px; padding-inline: 9px; font-size: 10px; } }
</style>
