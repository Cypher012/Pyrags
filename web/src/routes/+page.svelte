<script lang="ts">
	import BrandLogo from '$lib/assets/logo.svg?component';
	import BrandMark from '$lib/assets/logo-mark.svg?component';
	import HomeProductPreview from '$lib/components/home-product-preview.svelte';
	import {
		ArrowDown,
		ArrowLeft,
		ArrowRight,
		Check,
		ChevronRight,
		FileText,
		MessageCircle,
		Plus,
		Quote,
		UploadCloud
	} from '@lucide/svelte';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';

	let homeRoot = $state<HTMLElement>();
	let activeUseCase = $state(0);
	let activeExample = $state(0);
	const useCases = [
		{
			title: 'Course notes',
			detail:
				'Make difficult concepts click. Turn lecture notes into explanations and study questions.',
			file: 'Introduction to Agent-Based Systems.pdf',
			format: 'PDF',
			icon: FileText
		},
		{
			title: 'Research',
			detail:
				'Find the idea behind the paper. Explore arguments and follow the passages behind an answer.',
			file: 'Research methods and findings.pdf',
			format: 'PDF',
			icon: Quote
		},
		{
			title: 'Everyday docs',
			detail:
				'Get to the useful part. Ask about a report or guide instead of searching page by page.',
			file: 'Project notes and documentation.docx',
			format: 'DOCX',
			icon: MessageCircle
		}
	];
	const exampleQuestions = [
		{
			question: 'Can you explain this like I’m hearing it for the first time?',
			description: 'Make sense of an unfamiliar concept without losing the meaning.',
			topic: 'For the parts that haven’t clicked yet',
			file: 'Your course notes'
		},
		{
			question: 'What are the main ideas I should take away from this?',
			description: 'Find the thread running through a long document.',
			topic: 'For seeing the bigger picture',
			file: 'Your research paper'
		},
		{
			question: 'Give me a few questions to test what I’ve learned.',
			description: 'Turn a passive reading session into an active one.',
			topic: 'For making it stick',
			file: 'Your lecture material'
		}
	];
	const example = $derived(exampleQuestions[activeExample]);

	function changeExample(direction: number) {
		activeExample = (activeExample + direction + exampleQuestions.length) % exampleQuestions.length;
	}

	onMount(() => {
		let disposed = false;
		let cleanup = () => {};
		void (async () => {
			const [{ gsap }, { ScrollTrigger }] = await Promise.all([
				import('gsap'),
				import('gsap/ScrollTrigger')
			]);
			if (disposed || !homeRoot) return;
			gsap.registerPlugin(ScrollTrigger);
			const media = gsap.matchMedia();
			media.add('(min-width: 960px) and (prefers-reduced-motion: no-preference)', () => {
				const context = gsap.context(() => {
					gsap.from('.hero-copy > *', {
						y: 22,
						opacity: 0,
						duration: 0.85,
						stagger: 0.1,
						ease: 'power2.out'
					});
					gsap.from('.hero-product', {
						y: 35,
						opacity: 0,
						duration: 1.1,
						delay: 0.25,
						ease: 'power2.out'
					});
					ScrollTrigger.create({
						trigger: '.workflow-intro',
						start: 'top 23%',
						endTrigger: '.workflow-cards',
						end: 'bottom 75%',
						pin: true,
						pinSpacing: false
					});
					const cards = gsap.utils.toArray<HTMLElement>('.workflow-card');
					cards.slice(0, -1).forEach((card, index) => {
						ScrollTrigger.create({
							trigger: card,
							start: `top ${23 + index * 3}%`,
							endTrigger: '.workflow-cards',
							end: 'bottom 67%',
							pin: true,
							pinSpacing: false
						});
						gsap.to(card, {
							scale: 0.96,
							ease: 'none',
							scrollTrigger: {
								trigger: cards[index + 1],
								start: 'top 85%',
								end: 'top 29%',
								scrub: true
							}
						});
					});
				}, homeRoot);
				return () => context.revert();
			});
			cleanup = () => media.revert();
		})().catch((error) => console.warn('Homepage motion could not load:', error));
		return () => {
			disposed = true;
			cleanup();
		};
	});
</script>

<svelte:head>
	<title>Pyrags — Less searching. More understanding.</title>
	<meta
		name="description"
		content="Turn your PDFs and DOCX files into clear, source-backed conversations. Understand course notes, research, and everyday documents with Pyrags."
	/>
	<meta property="og:title" content="Pyrags — Less searching. More understanding." />
	<meta
		property="og:description"
		content="Your documents. Clearer answers. Sources you can follow."
	/>
</svelte:head>

<main bind:this={homeRoot} class="pyrags-home w-full max-w-full overflow-x-hidden">
	<a class="skip-link" href="#main-content">Skip to content</a>
	<header class="home-nav page-width">
		<a href={resolve('/')} aria-label="Pyrags home"><BrandLogo class="h-auto w-32" /></a>
		<nav aria-label="Main navigation">
			<a class="nav-section" href="#why-pyrags">Why Pyrags</a><a
				class="nav-section"
				href="#how-it-works">How it works</a
			><a class="nav-sign-in" href={resolve('/sign-in')}>Sign in</a><a
				class="nav-start"
				href={resolve('/sign-in')}>Get started <ArrowRight class="size-3.5" /></a
			>
		</nav>
	</header>
	<section id="main-content" class="hero page-width" aria-labelledby="hero-title">
		<div class="hero-copy">
			<h1 id="hero-title" class="max-w-6xl">
				Less searching.<br /><span>More understanding.</span>
			</h1>
			<p>Your documents have a lot to say. <br />Pyrags helps you get to the good part.</p>
			<div class="hero-actions">
				<a class="primary-link" href={resolve('/sign-in')}
					>Start a conversation <ArrowRight class="size-4" /></a
				><a class="text-link" href="#product-preview">Take a look <ArrowDown class="size-3.5" /></a>
			</div>
		</div>
		<div class="hero-product" id="product-preview">
			<div class="product-stage"><HomeProductPreview /></div>
			<div class="product-caption">
				<span><span class="caption-dot"></span> Your reading, with the sources in reach.</span><span
					>Interactive preview · Example content</span
				>
			</div>
		</div>
		<div class="hero-footnote">
			<span>Made for the curious.</span><span>For the “why?” and the “what does that mean?”</span
			><ArrowDown class="size-4" />
		</div>
	</section>
	<section
		id="why-pyrags"
		class="benefits section-space page-width"
		aria-labelledby="benefits-title"
	>
		<div class="section-heading">
			<h2 id="benefits-title">
				A little less digging.<br />A lot more
				<span class="inline-photo"
					><img
						src="https://picsum.photos/seed/quiet-library/320/160"
						alt=""
						loading="lazy"
						width="160"
						height="80"
					/></span
				> clarity.
			</h2>
			<p>
				No more jumping between a hundred pages.<br />Just a question, an answer, and somewhere<br
					class="desktop-break"
				/> to go if you want to dig deeper.
			</p>
		</div>
		<div class="benefit-grid grid-flow-dense">
			<article class="benefit-card use-case-card">
				<div class="card-heading">
					<h3>Whatever’s on your reading list.</h3>
					<p>A new perspective on the files you already have.</p>
				</div>
				<div class="use-cases" aria-label="Explore supported reading use cases">
					{#each useCases as useCase, index (useCase.title)}<div
							class="use-case"
							class:expanded={activeUseCase === index}
						>
							<button
								id={`use-case-${index}`}
								aria-expanded={activeUseCase === index}
								aria-controls={`use-case-panel-${index}`}
								onclick={() => (activeUseCase = index)}
								onmouseenter={() => (activeUseCase = index)}
								><useCase.icon class="size-4" /><span>{useCase.title}</span><Plus
									class="use-case-plus size-4"
								/></button
							>
							<div
								id={`use-case-panel-${index}`}
								class="use-case-details"
								role="region"
								aria-labelledby={`use-case-${index}`}
								hidden={activeUseCase !== index}
							>
								<div class="mini-document">
									<useCase.icon class="size-6" /><strong>{useCase.format}</strong><span
										>{useCase.file}</span
									>
									<div class="mini-lines"><span></span><span></span><span></span></div>
								</div>
								<p>{useCase.detail}</p>
							</div>
						</div>{/each}
				</div>
				<div class="card-bottom">
					<span>PDF & DOCX</span><span
						>Bring your own documents <ChevronRight class="size-3.5" /></span
					>
				</div>
			</article>
			<article class="benefit-card evidence-card">
				<div class="card-heading">
					<h3>Don’t just take its word for it.</h3>
					<p>Follow an answer back to the text behind it.</p>
				</div>
				<div class="evidence-example">
					<p>“An agent perceives its environment and takes actions to achieve its goals.”</p>
					<div>
						<FileText class="size-3.5" /><span>Agent-Based Systems.pdf</span><span>p. 12</span>
					</div>
				</div>
			</article>
			<article class="benefit-card conversation-card">
				<div class="card-heading">
					<h3>Keep the conversation going.</h3>
					<p>Follow-up questions stay connected to your chat.</p>
				</div>
				<div class="mini-chat">
					<span>What does that mean in practice?</span><span
						><BrandMark class="size-4" /> Let’s walk through an example.</span
					>
				</div>
			</article>
		</div>
	</section>
	<section id="how-it-works" class="workflow section-space" aria-labelledby="workflow-title">
		<div class="workflow-grid page-width">
			<div class="workflow-intro">
				<h2 id="workflow-title">From a file<br />to a fresh<br /><span>perspective.</span></h2>
				<p>
					No complicated setup.<br />No perfect prompt required.<br />Just bring something you want
					to understand.
				</p>
				<a class="text-link" href={resolve('/sign-in')}
					>Try it with your document <ArrowRight class="size-4" /></a
				>
			</div>
			<div class="workflow-cards">
				<article class="workflow-card upload-step">
					<div class="workflow-visual">
						<div class="upload-zone">
							<UploadCloud class="size-8" /><strong>A good place to start.</strong><span
								>Drop your PDF or DOCX here</span
							>
							<div><FileText class="size-4" /> Lecture notes.pdf <Check class="size-4" /></div>
						</div>
					</div>
					<div class="workflow-text">
						<h3>Bring your document.</h3>
						<p>
							A lecture, a paper, that report you’ve been meaning to read. Upload a PDF or DOCX to
							give your conversation a starting point.
						</p>
					</div>
				</article>
				<article class="workflow-card ask-step">
					<div class="workflow-visual">
						<div class="example-prompt">
							<span>Ask it your way.</span>
							<p>“What’s the main idea here?”</p>
							<div>
								<span>No special syntax. Just curiosity.</span><span class="prompt-arrow"
									><ArrowRight class="size-4 -rotate-90" /></span
								>
							</div>
						</div>
					</div>
					<div class="workflow-text">
						<h3>Ask what’s on your mind.</h3>
						<p>
							Go broad with a summary. Go deeper into a concept. Ask again when something doesn’t
							quite click.
						</p>
					</div>
				</article>
				<article class="workflow-card source-step">
					<div class="workflow-visual">
						<div class="source-page">
							<div><FileText class="size-4" /><span>Your document · Page 12</span></div>
							<span class="source-line"></span><span class="source-line"></span><mark
								>The answer is right here in the text.</mark
							><span class="source-line"></span><span class="source-line short"></span><span
								class="source-check"><Check class="size-3.5" /> A source you can follow</span
							>
						</div>
					</div>
					<div class="workflow-text">
						<h3>See where it comes from.</h3>
						<p>
							Read the response, then explore its source passages. The original context is always
							part of the conversation.
						</p>
					</div>
				</article>
			</div>
		</div>
	</section>
	<section class="questions section-space page-width" aria-labelledby="questions-title">
		<div class="question-heading">
			<h2 id="questions-title">Ask it like you mean it.</h2>
			<p>A few ways to start a better reading session.</p>
		</div>
		<div
			class="question-carousel"
			role="region"
			aria-roledescription="carousel"
			aria-label="Example questions"
		>
			<div class="question-quote" aria-live="polite" aria-atomic="true">
				<Quote class="quote-icon size-8" />
				<p>{example.topic}</p>
				<blockquote>“{example.question}”</blockquote>
				<span>{example.description}</span>
			</div>
			<div class="carousel-bottom">
				<span><FileText class="size-4" /> {example.file}</span>
				<div>
					<button aria-label="Previous example question" onclick={() => changeExample(-1)}
						><ArrowLeft class="size-4" /></button
					><span aria-label={`Example ${activeExample + 1} of ${exampleQuestions.length}`}
						>{activeExample + 1} / {exampleQuestions.length}</span
					><button aria-label="Next example question" onclick={() => changeExample(1)}
						><ArrowRight class="size-4" /></button
					>
				</div>
			</div>
		</div>
	</section>
	<section class="closing section-space" aria-labelledby="closing-title">
		<div class="page-width">
			<BrandMark class="closing-mark size-12" />
			<h2 id="closing-title">Good questions.<br /><span>Clearer answers.</span></h2>
			<p>Your next “aha” is a conversation away.</p>
			<a class="primary-link" href={resolve('/sign-in')}
				>Start with your document <ArrowRight class="size-4" /></a
			>
			<p class="free-note">Free to start. 6 queries a day.</p>
		</div>
	</section>
	<footer class="home-footer page-width">
		<a href={resolve('/')} aria-label="Pyrags home"><BrandLogo class="h-auto w-28" /></a><span
			>A little clarity goes a long way.</span
		>
		<div>
			<a href="#why-pyrags">Why Pyrags</a><a href={resolve('/tutorials/inngest')}>Documentation</a
			><a href={resolve('/sign-in')}>Get started <ArrowRight class="size-3.5" /></a>
		</div>
	</footer>
</main>

<style>
	.pyrags-home {
		--home-ink: #203729;
		--home-muted: #697460;
		--home-green: #36563b;
		--home-border: #e2e6dc;
		--logo-mark: #426637;
		--logo-wordmark: #243e2b;
		background: #fbfcf8;
		color: var(--home-ink);
		font-family: 'Geist Variable', sans-serif;
		color-scheme: light;
	}
	.page-width {
		width: min(100% - 112px, 1248px);
		margin-inline: auto;
	}
	.section-space {
		padding-block: 128px;
	}
	.pyrags-home :global(a:focus-visible),
	.pyrags-home :global(button:focus-visible) {
		outline: 2px solid #567a42;
		outline-offset: 5px;
	}
	.skip-link {
		position: absolute;
		top: 8px;
		left: 20px;
		z-index: 100;
		padding: 12px 18px;
		transform: translateY(-150%);
		background: var(--home-ink);
		color: white;
		border-radius: 8px;
	}
	.skip-link:focus {
		transform: translateY(0);
	}
	.home-nav {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 105px;
		border-bottom: 1px solid var(--home-border);
	}
	.home-nav nav {
		display: flex;
		align-items: center;
		gap: 34px;
		font-size: 13px;
	}
	.home-nav a {
		transition: color 0.2s;
	}
	.home-nav .nav-section {
		color: #747d70;
	}
	.home-nav .nav-section:hover {
		color: var(--home-ink);
	}
	.home-nav .nav-sign-in {
		margin-left: 24px;
	}
	.nav-start {
		display: inline-flex;
		align-items: center;
		gap: 14px;
		padding: 12px 17px;
		border: 1px solid #cfd8c6;
		border-radius: 7px;
		background: #f0f4e9;
	}
	.nav-start:hover {
		background: #e8efde;
	}
	.hero {
		position: relative;
		padding-top: 95px;
	}
	.hero-copy {
		position: relative;
		z-index: 2;
	}
	h1 {
		width: 100%;
		margin: 0;
		font-size: clamp(48px, 6.1vw, 88px);
		line-height: 1.06;
		letter-spacing: -0.064em;
		font-weight: 450;
	}
	h1 span {
		color: #82917b;
	}
	.hero-copy > p {
		margin-top: 31px;
		color: #747d70;
		font-size: 17px;
		line-height: 1.75;
	}
	.hero-actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 24px;
		margin-top: 28px;
	}
	.primary-link {
		display: inline-flex;
		justify-content: center;
		align-items: center;
		gap: 20px;
		min-height: 49px;
		padding: 13px 21px;
		border: 1px solid var(--home-green);
		border-radius: 7px;
		background: var(--home-green);
		color: #fff;
		font-size: 13px;
		font-weight: 500;
		transition:
			background 0.2s,
			transform 0.2s;
	}
	.primary-link:hover {
		background: #25402b;
		transform: translateY(-2px);
	}
	.text-link {
		display: inline-flex;
		align-items: center;
		gap: 12px;
		font-size: 13px;
	}
	.text-link:hover :global(svg) {
		transform: translateX(3px);
	}
	.text-link :global(svg) {
		transition: transform 0.2s;
	}
	.hero-product {
		position: relative;
		margin: -18px -58px 0 260px;
		padding-top: 83px;
		scroll-margin-top: 30px;
	}
	.hero-product::before {
		position: absolute;
		inset: -110px -60px 70px 30px;
		z-index: 0;
		border-radius: 50%;
		background: radial-gradient(ellipse, #d7e4c7a6 0%, #e9eede55 45%, transparent 72%);
		filter: blur(30px);
		content: '';
		pointer-events: none;
	}
	.product-stage {
		position: relative;
		z-index: 1;
		transform: rotate(-1.2deg);
		transform-origin: center;
		transition: transform 0.7s ease;
	}
	.product-stage:hover {
		transform: rotate(0);
	}
	.product-caption {
		position: relative;
		display: flex;
		justify-content: space-between;
		gap: 20px;
		margin-top: 26px;
		padding-inline: 5px;
		color: #8b9384;
		font-size: 10px;
	}
	.product-caption > span:first-child {
		display: flex;
		align-items: center;
		gap: 7px;
	}
	.caption-dot {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		background: #83a267;
	}
	.hero-footnote {
		display: flex;
		align-items: center;
		gap: 26px;
		margin-top: 79px;
		padding-bottom: 32px;
		border-bottom: 1px solid var(--home-border);
		color: #929989;
		font-size: 11px;
	}
	.hero-footnote span:first-child {
		color: #485b41;
	}
	.hero-footnote > :global(svg) {
		margin-left: auto;
	}
	.section-heading {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 40px;
		margin-bottom: 52px;
	}
	h2 {
		margin: 0;
		font-weight: 440;
		font-size: clamp(36px, 3.7vw, 54px);
		line-height: 1.12;
		letter-spacing: -0.05em;
	}
	.section-heading > p {
		margin-bottom: 4px;
		color: var(--home-muted);
		font-size: 14px;
		line-height: 1.9;
	}
	.inline-photo {
		display: inline-block;
		width: 77px;
		height: 40px;
		margin-inline: 3px;
		overflow: hidden;
		border-radius: 40px;
		vertical-align: baseline;
	}
	.inline-photo img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		filter: grayscale(1) contrast(0.85);
		transition: transform 0.7s;
	}
	.inline-photo:hover img {
		transform: scale(1.1);
	}
	.benefit-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		grid-template-rows: repeat(2, minmax(260px, auto));
		grid-auto-flow: dense;
		gap: 16px;
	}
	.benefit-card {
		min-width: 0;
		overflow: hidden;
		border: 1px solid var(--home-border);
		border-radius: 12px;
		background: #fff;
	}
	.use-case-card {
		grid-column: span 2;
		grid-row: span 2;
		display: flex;
		flex-direction: column;
		background: #f2f5ec;
	}
	.card-heading {
		padding: 29px 29px 0;
	}
	.card-heading h3 {
		font-size: 19px;
		font-weight: 450;
		letter-spacing: -0.035em;
	}
	.card-heading p {
		margin-top: 8px;
		color: var(--home-muted);
		font-size: 12px;
		line-height: 1.7;
	}
	.use-cases {
		display: flex;
		flex: 1;
		gap: 8px;
		margin: 31px 22px 22px;
		min-height: 310px;
	}
	.use-case {
		display: flex;
		min-width: 0;
		flex: 0.35;
		flex-direction: column;
		overflow: hidden;
		border: 1px solid #dfe5d6;
		border-radius: 7px;
		background: #e9eedf;
		transition:
			flex 0.55s cubic-bezier(0.2, 0.7, 0.2, 1),
			background 0.3s;
	}
	.use-case.expanded {
		flex: 2;
		background: #fcfdf9;
	}
	.use-case > button {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 15px;
		width: 100%;
		padding: 19px 9px;
		cursor: pointer;
	}
	.use-case > button span {
		writing-mode: vertical-rl;
		font-size: 12px;
		white-space: nowrap;
	}
	.use-case.expanded > button {
		flex-direction: row;
		justify-content: flex-start;
		gap: 9px;
		padding: 16px;
	}
	.use-case.expanded > button span {
		writing-mode: horizontal-tb;
	}
	.use-case.expanded :global(.use-case-plus) {
		margin-left: auto;
		transform: rotate(45deg);
	}
	.use-case-details {
		padding: 0 17px 20px;
	}
	.use-case-details > p {
		margin-top: 19px;
		color: #7d8775;
		font-size: 11px;
		line-height: 1.8;
	}
	.mini-document {
		position: relative;
		min-height: 164px;
		padding: 19px;
		border: 1px solid #e5e8de;
		border-radius: 5px;
		background: #fff;
		box-shadow: 0 8px 15px #23352a06;
	}
	.mini-document > :global(svg) {
		color: #68805b;
	}
	.mini-document strong {
		position: absolute;
		top: 24px;
		right: 17px;
		color: #97a18e;
		font-size: 9px;
		font-weight: 400;
	}
	.mini-document > span {
		display: block;
		margin-top: 15px;
		font-size: 10px;
		line-height: 1.5;
	}
	.mini-lines {
		display: grid;
		gap: 7px;
		margin-top: 16px;
	}
	.mini-lines span {
		height: 3px;
		border-radius: 2px;
		background: #e7ecdf;
	}
	.mini-lines span:last-child {
		width: 65%;
	}
	.card-bottom {
		display: flex;
		justify-content: space-between;
		gap: 10px;
		padding: 18px 27px;
		border-top: 1px solid #dfe5d6;
		color: #88917e;
		font-size: 10px;
	}
	.card-bottom > span:last-child {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.evidence-card,
	.conversation-card {
		grid-column: span 2;
	}
	.evidence-example {
		margin: 23px 29px 27px;
		padding: 17px 19px;
		border-left: 2px solid #b8cea5;
		border-radius: 0 6px 6px 0;
		background: #f5f8f0;
	}
	.evidence-example > p {
		color: #617455;
		font-size: 13px;
		line-height: 1.8;
	}
	.evidence-example > div {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-top: 16px;
		color: #929d89;
		font-size: 9px;
	}
	.evidence-example > div span:last-child {
		margin-left: auto;
	}
	.conversation-card {
		background: #f6f4ed;
	}
	.mini-chat {
		display: flex;
		flex-direction: column;
		gap: 13px;
		padding: 24px 29px 28px;
		font-size: 12px;
	}
	.mini-chat > span:first-child {
		align-self: flex-end;
		padding: 11px 14px;
		border: 1px solid #e0ddd2;
		border-radius: 9px 9px 2px 9px;
		background: #fffefa;
	}
	.mini-chat > span:last-child {
		display: flex;
		align-items: center;
		gap: 10px;
		color: #888675;
	}
	.workflow {
		border-block: 1px solid #e5e9de;
		background: #f0f3e9;
	}
	.workflow-grid {
		display: grid;
		grid-template-columns: 0.9fr 1.1fr;
		align-items: start;
		gap: 100px;
	}
	.workflow-intro {
		padding-top: 35px;
	}
	.workflow-intro h2 {
		font-size: clamp(42px, 4.8vw, 68px);
	}
	.workflow-intro h2 span {
		color: #8b9a7e;
	}
	.workflow-intro > p {
		margin-top: 26px;
		color: #7b8572;
		font-size: 14px;
		line-height: 1.9;
	}
	.workflow-intro .text-link {
		margin-top: 30px;
	}
	.workflow-cards {
		display: flex;
		flex-direction: column;
		gap: 24px;
		padding-bottom: 35px;
	}
	.workflow-card {
		position: relative;
		overflow: hidden;
		min-height: 370px;
		border: 1px solid #dce3d2;
		border-radius: 13px;
		background: #fdfefa;
		transform-origin: top center;
		box-shadow: 0 8px 20px #243e2905;
	}
	.ask-step {
		background: #e6ecdd;
	}
	.source-step {
		background: #dae5d0;
	}
	.workflow-visual {
		display: grid;
		place-items: center;
		min-height: 234px;
		padding: 25px 35px 15px;
	}
	.upload-zone {
		display: flex;
		align-items: center;
		flex-direction: column;
		width: 82%;
		padding: 22px;
		border: 1px dashed #b8c7ac;
		border-radius: 8px;
		background: #f7f9f2;
	}
	.upload-zone > :global(svg) {
		color: #8fa47e;
	}
	.upload-zone strong {
		margin-top: 12px;
		font-size: 13px;
		font-weight: 450;
	}
	.upload-zone > span {
		margin-top: 5px;
		color: #9ba58f;
		font-size: 10px;
	}
	.upload-zone > div {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		margin-top: 19px;
		padding: 11px;
		border: 1px solid #e0e7d6;
		border-radius: 5px;
		background: #fff;
		font-size: 10px;
	}
	.upload-zone > div > :global(svg:last-child) {
		margin-left: auto;
		color: #769961;
	}
	.workflow-text {
		padding: 17px 35px 31px;
	}
	.workflow-text h3 {
		font-size: 21px;
		font-weight: 450;
		letter-spacing: -0.035em;
	}
	.workflow-text > p {
		max-width: 370px;
		margin-top: 11px;
		color: #7a8571;
		font-size: 12px;
		line-height: 1.9;
	}
	.example-prompt {
		width: 92%;
		padding: 22px;
		border: 1px solid #d2dcc5;
		border-radius: 10px;
		background: #f8faf4;
	}
	.example-prompt > span {
		color: #9aa58f;
		font-size: 10px;
	}
	.example-prompt > p {
		margin-top: 17px;
		font-size: 21px;
		font-weight: 400;
		letter-spacing: -0.04em;
	}
	.example-prompt > div {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 25px;
		font-size: 9px;
		color: #99a38e;
	}
	.prompt-arrow {
		display: grid;
		place-items: center;
		width: 29px;
		height: 29px;
		border-radius: 7px;
		background: #45603e;
		color: #fff;
	}
	.source-page {
		width: 82%;
		padding: 22px;
		border: 1px solid #cad7be;
		border-radius: 8px;
		background: #f9fbf5;
	}
	.source-page > div {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 22px;
		font-size: 10px;
		color: #798c69;
	}
	.source-line {
		display: block;
		height: 4px;
		margin-top: 10px;
		border-radius: 2px;
		background: #e0e7d7;
	}
	.source-line.short {
		width: 65%;
	}
	.source-page mark {
		display: block;
		width: fit-content;
		margin-top: 12px;
		padding: 3px 5px;
		background: #e0edb9;
		color: #596d40;
		font-size: 11px;
	}
	.source-check {
		display: flex;
		align-items: center;
		gap: 7px;
		margin-top: 21px;
		color: #7d9468;
		font-size: 9px;
	}
	.question-heading {
		text-align: center;
	}
	.question-heading p {
		margin-top: 15px;
		color: var(--home-muted);
		font-size: 14px;
	}
	.question-carousel {
		max-width: 960px;
		margin: 47px auto 0;
		overflow: hidden;
		border: 1px solid var(--home-border);
		border-radius: 12px;
		background: #fff;
	}
	.question-quote {
		min-height: 298px;
		padding: 43px 62px 38px;
	}
	.question-quote :global(.quote-icon) {
		color: #9fb48e;
	}
	.question-quote > p {
		margin-top: 22px;
		color: #929b89;
		font-size: 11px;
	}
	.question-quote blockquote {
		max-width: 760px;
		margin-top: 17px;
		font-size: clamp(24px, 2.6vw, 35px);
		line-height: 1.35;
		letter-spacing: -0.035em;
		font-weight: 400;
	}
	.question-quote > span {
		display: block;
		margin-top: 22px;
		color: #7e8877;
		font-size: 13px;
		line-height: 1.7;
	}
	.carousel-bottom {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 15px;
		padding: 19px 30px;
		border-top: 1px solid var(--home-border);
		background: #f8faf4;
		color: #8c9781;
		font-size: 11px;
	}
	.carousel-bottom > span,
	.carousel-bottom > div {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.carousel-bottom > div {
		gap: 18px;
	}
	.carousel-bottom button {
		display: grid;
		place-items: center;
		width: 35px;
		height: 35px;
		border: 1px solid #dce4d3;
		border-radius: 50%;
		background: #fff;
		color: #536d44;
		cursor: pointer;
		transition:
			transform 0.2s,
			background 0.2s;
	}
	.carousel-bottom button:hover {
		transform: scale(1.06);
		background: #edf3e5;
	}
	.closing {
		position: relative;
		border-top: 1px solid var(--home-border);
		text-align: center;
		background: radial-gradient(ellipse at center 120%, #e4edda 0%, #f6f8f0 52%, #fbfcf8 90%);
	}
	.closing :global(.closing-mark) {
		margin: 0 auto 28px;
	}
	.closing h2 {
		font-size: clamp(44px, 5.5vw, 76px);
	}
	.closing h2 span {
		color: #8c9c7d;
	}
	.closing > div > p {
		margin-top: 22px;
		color: #87917e;
		font-size: 15px;
	}
	.closing .primary-link {
		margin-top: 29px;
	}
	.closing > div > p.free-note {
		margin-top: 15px;
		color: #9ca58e;
		font-size: 11px;
	}
	.home-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 25px;
		min-height: 114px;
		color: #949b8d;
		font-size: 11px;
	}
	.home-footer > div {
		display: flex;
		align-items: center;
		gap: 28px;
	}
	.home-footer > div a:last-child {
		display: flex;
		align-items: center;
		gap: 8px;
		color: #5a7050;
	}
	@media (max-width: 1100px) {
		.page-width {
			width: calc(100% - 64px);
		}
		.hero-product {
			margin-left: 90px;
			margin-right: -10px;
			padding-top: 70px;
		}
		.workflow-grid {
			gap: 50px;
		}
		.use-cases {
			margin-inline: 15px;
			gap: 6px;
		}
		.card-heading {
			padding: 24px 24px 0;
		}
		.use-case-details {
			padding-inline: 12px;
		}
		.mini-document {
			padding: 14px;
		}
		.mini-document strong {
			right: 12px;
			top: 19px;
		}
		.evidence-example {
			margin-inline: 24px;
		}
	}
	@media (max-width: 959px) {
		.section-space {
			padding-block: 88px;
		}
		.hero {
			padding-top: 70px;
		}
		.hero-product {
			margin-inline: 0;
			padding-top: 70px;
		}
		.hero-footnote {
			margin-top: 53px;
		}
		.home-nav nav {
			gap: 23px;
		}
		.home-nav .nav-sign-in {
			margin-left: 0;
		}
		.section-heading {
			flex-direction: column;
			align-items: flex-start;
			gap: 22px;
		}
		.desktop-break {
			display: none;
		}
		.workflow-grid {
			grid-template-columns: 1fr;
			gap: 43px;
		}
		.workflow-intro {
			padding-top: 0;
		}
		.workflow-intro h2 {
			font-size: 52px;
		}
		.workflow-intro h2 br {
			display: none;
		}
		.workflow-intro h2 span {
			display: block;
		}
		.workflow-intro > p br {
			display: none;
		}
		.workflow-intro > p {
			max-width: 370px;
		}
		.workflow-cards {
			padding-bottom: 0;
		}
		.workflow-card {
			min-height: 345px;
		}
		.workflow-visual {
			min-height: 210px;
		}
		.workflow-text > p {
			max-width: 470px;
		}
		.upload-zone,
		.source-page,
		.example-prompt {
			max-width: 370px;
		}
		.benefit-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
			grid-template-rows: auto;
		}
		.use-case-card {
			grid-row: auto;
		}
		.use-cases {
			min-height: 295px;
		}
		.use-case.expanded {
			flex: 3;
		}
		.question-quote {
			padding-inline: 38px;
		}
	}
	@media (max-width: 640px) {
		.page-width {
			width: calc(100% - 40px);
		}
		.home-nav {
			height: 82px;
		}
		.home-nav :global(svg) {
			max-width: 108px;
		}
		.home-nav nav {
			gap: 13px;
			font-size: 11px;
		}
		.home-nav .nav-section {
			display: none;
		}
		.nav-start {
			padding: 10px 12px;
			gap: 7px;
		}
		.hero {
			padding-top: 59px;
		}
		h1 {
			font-size: clamp(35px, 8.5vw, 52px);
			letter-spacing: -0.06em;
		}
		.hero-copy > p {
			margin-top: 25px;
			font-size: 14px;
		}
		.hero-actions {
			gap: 18px;
			margin-top: 23px;
		}
		.primary-link {
			padding-inline: 16px;
			min-height: 46px;
			font-size: 12px;
			gap: 13px;
		}
		.text-link {
			font-size: 12px;
			gap: 8px;
		}
		.hero-product {
			padding-top: 55px;
		}
		.product-stage {
			transform: rotate(0);
		}
		.product-caption {
			flex-direction: column;
			align-items: center;
			gap: 7px;
			margin-top: 16px;
			font-size: 9px;
		}
		.hero-footnote {
			margin-top: 44px;
			gap: 13px;
			font-size: 9px;
			padding-bottom: 24px;
		}
		.hero-footnote > span:nth-child(2) {
			max-width: 170px;
		}
		.section-space {
			padding-block: 72px;
		}
		h2 {
			font-size: 35px;
		}
		.section-heading {
			margin-bottom: 32px;
		}
		.section-heading > p {
			font-size: 13px;
		}
		.inline-photo {
			width: 57px;
			height: 29px;
		}
		.benefit-grid {
			gap: 12px;
		}
		.card-heading {
			padding: 23px 21px 0;
		}
		.card-heading h3 {
			font-size: 18px;
		}
		.card-heading p {
			font-size: 11px;
		}
		.use-cases {
			margin: 24px 13px 20px;
			min-height: 290px;
		}
		.use-case {
			flex: 0.4;
		}
		.use-case.expanded {
			flex: 2.7;
		}
		.use-case > button {
			padding: 15px 8px;
		}
		.use-case.expanded > button {
			padding: 14px 12px;
			gap: 6px;
		}
		.use-case.expanded > button span {
			font-size: 11px;
		}
		.use-case.expanded :global(.use-case-plus) {
			display: none;
		}
		.use-case-details {
			padding: 0 10px 15px;
		}
		.mini-document {
			min-height: 145px;
			padding: 13px;
		}
		.mini-document > span {
			font-size: 9px;
		}
		.use-case-details > p {
			font-size: 10px;
		}
		.card-bottom {
			padding-inline: 20px;
			font-size: 9px;
		}
		.evidence-example {
			margin: 22px 21px;
			padding: 15px;
		}
		.evidence-example > p {
			font-size: 12px;
		}
		.mini-chat {
			padding: 22px 21px 25px;
			font-size: 11px;
		}
		.workflow-intro h2 {
			font-size: 43px;
		}
		.workflow-intro > p {
			font-size: 13px;
		}
		.workflow-grid {
			gap: 31px;
		}
		.workflow-card {
			min-height: 350px;
		}
		.workflow-visual {
			padding: 20px 17px 12px;
		}
		.workflow-text {
			padding: 14px 25px 27px;
		}
		.workflow-text h3 {
			font-size: 20px;
		}
		.workflow-text > p {
			font-size: 12px;
		}
		.upload-zone,
		.source-page {
			width: 91%;
		}
		.example-prompt {
			padding: 21px 17px;
		}
		.example-prompt > p {
			font-size: 20px;
		}
		.question-heading p {
			font-size: 13px;
		}
		.question-carousel {
			margin-top: 31px;
		}
		.question-quote {
			min-height: 335px;
			padding: 28px 25px;
		}
		.question-quote blockquote {
			font-size: 25px;
		}
		.question-quote > span {
			font-size: 12px;
		}
		.carousel-bottom {
			padding: 15px 17px;
			font-size: 10px;
		}
		.carousel-bottom > div {
			gap: 11px;
		}
		.carousel-bottom > span {
			gap: 5px;
		}
		.carousel-bottom button {
			width: 31px;
			height: 31px;
		}
		.closing h2 {
			font-size: 48px;
		}
		.closing > div > p {
			font-size: 13px;
		}
		.home-footer {
			flex-wrap: wrap;
			gap: 20px;
			padding-block: 30px;
		}
		.home-footer > span {
			width: calc(100% - 150px);
			text-align: right;
			font-size: 10px;
		}
		.home-footer > div {
			width: 100%;
			justify-content: space-between;
			font-size: 10px;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.pyrags-home :global(*),
		.pyrags-home :global(*::before),
		.pyrags-home :global(*::after) {
			animation: none !important;
			transition: none !important;
		}
	}
</style>
