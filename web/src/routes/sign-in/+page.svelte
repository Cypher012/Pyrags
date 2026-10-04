<script lang="ts">
	import BrandLogo from '$lib/assets/logo.svg?component';
	import BrandMark from '$lib/assets/logo-mark.svg?component';
	import GoogleLogo from '$lib/assets/google.svg?component';
	import GithubLogo from '$lib/assets/github.svg?component';
	import { ArrowLeft, ArrowRight, FileText, LoaderCircle, LockKeyhole, Quote } from '@lucide/svelte';
	import { authClient } from '$lib/auth-client';
	import { toast } from 'svelte-sonner';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';

	type Provider = 'google' | 'github';
	let pendingProvider = $state<Provider | null>(null);
	let signInError = $state('');
	let authRoot = $state<HTMLElement>();

	const signIn = async (provider: Provider) => {
		if (pendingProvider) return;
		pendingProvider = provider;
		signInError = '';
		try {
			const { error } = await authClient.signIn.social({ provider, callbackURL: '/app' });
			if (error) {
				signInError = error.message || 'Unable to sign in. Please try again.';
				toast.error(signInError);
			}
		} catch {
			signInError = 'Unable to connect to sign-in. Please try again.';
			toast.error(signInError);
		} finally {
			pendingProvider = null;
		}
	};

	onMount(() => {
		let disposed = false;
		let cleanup = () => {};
		void import('gsap').then(({ gsap }) => {
			if (disposed || !authRoot) return;
			const media = gsap.matchMedia();
			media.add('(prefers-reduced-motion: no-preference)', () => {
				const context = gsap.context(() => {
					gsap.from('[data-auth-reveal]', { y: 16, opacity: 0, duration: .65, stagger: .08, ease: 'power2.out' });
					gsap.from('.document-scene', { y: 20, opacity: 0, duration: .9, delay: .2, ease: 'power2.out' });
				}, authRoot);
				return () => context.revert();
			});
			cleanup = () => media.revert();
		}).catch((error) => console.warn('Sign-in motion could not load:', error));
		return () => { disposed = true; cleanup(); };
	});
</script>

<svelte:head>
	<title>Sign in — Pyrags</title>
	<meta name="description" content="Sign in to Pyrags to explore your documents, ask better questions, and follow the sources behind your answers." />
</svelte:head>

<main bind:this={authRoot} class="auth-page">
	<header class="auth-nav page-width">
		<a href={resolve('/')} aria-label="Pyrags home"><BrandLogo class="h-auto w-32" /></a>
		<a class="back-link" href={resolve('/')}><ArrowLeft class="size-3.5" /> Back to home</a>
	</header>

	<div class="auth-layout page-width">
		<section class="welcome-panel" aria-labelledby="welcome-title">
			<div class="welcome-copy" data-auth-reveal><h2 id="welcome-title">A little clarity.<br /><span>A new perspective.</span></h2><p>For the things you want to understand.<br />And the questions that get you there.</p></div>
			<div class="document-scene" aria-hidden="true">
				<div class="document-shadow"></div>
				<div class="document-paper"><div class="paper-heading"><FileText class="size-5" /><span>Your reading, reimagined.</span></div><h3>There’s a good idea<br />in here somewhere.</h3><div class="paper-lines"><span></span><span></span><span class="short"></span></div><mark>Let’s find it together.</mark><div class="paper-lines"><span></span><span class="short"></span></div><span class="paper-page">Your document · Page 12</span></div>
				<div class="source-note"><div class="source-note-icon"><Quote class="size-5" /></div><div><strong>Clearer answers. Sources in reach.</strong><p>Follow the answer back to the text.</p></div></div>
			</div>
			<div class="welcome-bottom"><span class="small-dot"></span> Made for the curious.</div>
		</section>

		<section class="sign-in-panel" aria-labelledby="sign-in-title">
			<div class="sign-in-content">
				<div class="form-mark" data-auth-reveal><BrandMark class="size-9" /></div>
				<div data-auth-reveal><h1 id="sign-in-title">Your next “aha”<br /><span>starts here.</span></h1><p class="sign-in-description">Sign in or create an account.<br />Your documents are waiting to make sense.</p></div>
				<div class="provider-buttons" data-auth-reveal aria-busy={pendingProvider !== null}>
					<button type="button" class="provider-button google-button" onclick={() => signIn('google')} disabled={pendingProvider !== null} aria-describedby={signInError ? 'sign-in-error' : undefined}><GoogleLogo class="size-5" /><span>{pendingProvider === 'google' ? 'Connecting to Google…' : 'Continue with Google'}</span>{#if pendingProvider === 'google'}<LoaderCircle class="provider-spinner size-4" />{:else}<ArrowRight class="provider-arrow size-4" />{/if}</button>
					<button type="button" class="provider-button github-button" onclick={() => signIn('github')} disabled={pendingProvider !== null} aria-describedby={signInError ? 'sign-in-error' : undefined}><GithubLogo class="size-5" /><span>{pendingProvider === 'github' ? 'Connecting to GitHub…' : 'Continue with GitHub'}</span>{#if pendingProvider === 'github'}<LoaderCircle class="provider-spinner size-4" />{:else}<ArrowRight class="provider-arrow size-4" />{/if}</button>
				</div>
				{#if signInError}<p id="sign-in-error" class="sign-in-error" role="alert">{signInError}</p>{/if}
				<p class="connecting-status" role="status">{pendingProvider ? `Opening ${pendingProvider === 'google' ? 'Google' : 'GitHub'} sign-in. Please wait.` : ''}</p>
				<div class="account-note" data-auth-reveal><span></span><p>One account. A little clarity, every day.</p><span></span></div>
				<div class="free-note" data-auth-reveal><span class="small-dot"></span><p>Free to start. <strong>6 queries a day.</strong></p></div>
				<p class="privacy-note" data-auth-reveal><LockKeyhole class="size-3.5" /><span>Your documents and conversations belong<br class="privacy-break" /> to your workspace.</span></p>
			</div>
		</section>
	</div>

	<footer class="auth-footer page-width"><span>A little clarity goes a long way.</span><span>Read. Ask. Understand.</span></footer>
</main>

<style>
	.auth-page { --auth-ink: #203729; --auth-muted: #707d67; --auth-border: #e2e6dc; --logo-mark: #426637; --logo-wordmark: #243e2b; display: flex; min-height: 100dvh; flex-direction: column; overflow-x: clip; background: #fbfcf8; color: var(--auth-ink); color-scheme: light; font-family: 'Geist Variable', sans-serif; }
	.page-width { width: min(100% - 112px, 1248px); margin-inline: auto; }
	.auth-nav { display: flex; align-items: center; justify-content: space-between; min-height: 105px; border-bottom: 1px solid var(--auth-border); }
	.back-link { display: inline-flex; align-items: center; gap: 10px; color: #74816b; font-size: 12px; transition: color .2s; }
	.back-link:hover { color: var(--auth-ink); }
	.back-link :global(svg) { transition: transform .2s; }
	.back-link:hover :global(svg) { transform: translateX(-3px); }
	.auth-layout { display: grid; flex: 1; grid-template-columns: 1.05fr 1fr; gap: 60px; align-items: center; padding-block: 42px; }
	.welcome-panel { position: relative; display: flex; min-height: 622px; flex-direction: column; overflow: hidden; padding: 48px 44px 30px; border: 1px solid #e3e9d9; border-radius: 15px; background: radial-gradient(ellipse at 55% 60%, #e0eaca 0%, #edf2e4 50%, #f1f5eb 100%); }
	.welcome-copy { position: relative; z-index: 2; }
	.welcome-copy h2 { margin: 0; font-size: clamp(37px, 3.5vw, 49px); font-weight: 450; line-height: 1.13; letter-spacing: -.055em; }
	.welcome-copy h2 span { color: #7f9270; }
	.welcome-copy > p { margin-top: 23px; color: #77876a; font-size: 13px; line-height: 1.85; }
	.document-scene { position: relative; width: min(100%, 387px); height: 298px; margin: 31px auto 0; }
	.document-shadow { position: absolute; top: 27px; right: 20px; width: 272px; height: 267px; border: 1px solid #d7e1ca; border-radius: 9px; background: #e5eddb; transform: rotate(7deg); }
	.document-paper { position: absolute; top: 6px; right: 40px; width: 272px; height: 273px; padding: 25px; border: 1px solid #dbe3d1; border-radius: 8px; background: #fcfdf9; box-shadow: 0 16px 30px -20px #3d59373b; transform: rotate(-5deg); }
	.paper-heading { display: flex; align-items: center; gap: 9px; color: #8d9a81; font-size: 9px; }
	.paper-heading :global(svg) { color: #71905a; }
	.document-paper h3 { margin-top: 21px; font-size: 16px; font-weight: 450; line-height: 1.4; letter-spacing: -.025em; }
	.paper-lines { display: grid; gap: 8px; margin-top: 17px; }
	.paper-lines > span { height: 4px; border-radius: 2px; background: #e7ebdf; }
	.paper-lines > span.short { width: 66%; }
	.document-paper mark { display: block; width: fit-content; margin-top: 13px; padding: 3px 6px; background: #e5efc9; color: #6a7d50; font-size: 10px; }
	.paper-page { display: block; margin-top: 18px; color: #99a38f; text-align: right; font-size: 8px; }
	.source-note { position: absolute; right: -7px; bottom: 1px; z-index: 2; display: flex; align-items: center; gap: 12px; width: 315px; padding: 16px; border: 1px solid #d8e3cc; border-radius: 9px; background: #ffffffed; box-shadow: 0 10px 30px -15px #34502c40; transform: rotate(2deg); }
	.source-note-icon { display: grid; flex-shrink: 0; place-items: center; width: 34px; height: 34px; border-radius: 7px; background: #eff4e6; color: #7e9b64; }
	.source-note strong { font-size: 11px; font-weight: 500; }
	.source-note p { margin-top: 5px; color: #89957d; font-size: 10px; }
	.welcome-bottom { display: flex; align-items: center; gap: 8px; margin-top: auto; padding-top: 33px; color: #89987a; font-size: 10px; }
	.small-dot { display: inline-block; flex-shrink: 0; width: 5px; height: 5px; border-radius: 50%; background: #86a368; }
	.sign-in-panel { display: flex; justify-content: center; min-width: 0; padding: 20px 10px; }
	.sign-in-content { width: 100%; max-width: 348px; }
	.form-mark { display: grid; place-items: center; width: 62px; height: 62px; margin-bottom: 27px; border: 1px solid #e0e7d8; border-radius: 14px; background: #f1f5eb; }
	h1 { font-size: 42px; font-weight: 450; line-height: 1.14; letter-spacing: -.055em; }
	h1 span { color: #819277; }
	.sign-in-description { margin-top: 17px; color: var(--auth-muted); font-size: 13px; line-height: 1.9; }
	.provider-buttons { display: flex; flex-direction: column; gap: 11px; margin-top: 30px; }
	.provider-button { display: flex; align-items: center; gap: 13px; width: 100%; min-height: 54px; padding: 13px 17px; border: 1px solid #dce4d4; border-radius: 8px; background: #fff; color: #31472d; text-align: left; font-size: 13px; font-weight: 450; cursor: pointer; transition: transform .2s, background .2s, border-color .2s; }
	.provider-button > :global(svg:first-child) { flex-shrink: 0; }
	.provider-button :global(.provider-arrow), .provider-button :global(.provider-spinner) { margin-left: auto; color: #8f9c84; }
	.provider-button:hover:not(:disabled) { transform: translateY(-2px); border-color: #b5c5a5; background: #f5f8ef; }
	.provider-button :global(.provider-arrow) { transition: transform .2s; }
	.provider-button:hover:not(:disabled) :global(.provider-arrow) { transform: translateX(3px); }
	.provider-button:disabled { cursor: wait; opacity: .65; }
	.provider-button:disabled :global(.provider-spinner) { color: #577c40; animation: provider-spin 1s linear infinite; }
	.sign-in-error { margin-top: 14px; padding: 11px 13px; border: 1px solid #ebd7d1; border-radius: 7px; background: #fcf3f0; color: #9a4538; font-size: 12px; line-height: 1.7; }
	.connecting-status { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
	.account-note { display: flex; align-items: center; gap: 13px; margin-top: 29px; }
	.account-note span { height: 1px; flex: 1; background: var(--auth-border); }
	.account-note p { color: #919a88; font-size: 10px; white-space: nowrap; }
	.free-note { display: flex; align-items: center; justify-content: center; gap: 7px; margin-top: 23px; font-size: 11px; color: #7b8b6b; }
	.free-note strong { font-weight: 450; color: #526a41; }
	.privacy-note { display: flex; justify-content: center; align-items: flex-start; gap: 8px; margin-top: 25px; color: #87937c; text-align: center; font-size: 10px; line-height: 1.8; }
	.privacy-note > :global(svg) { flex-shrink: 0; margin-top: 2px; }
	.auth-footer { display: flex; align-items: center; justify-content: space-between; min-height: 76px; border-top: 1px solid var(--auth-border); color: #929d88; font-size: 10px; }
	.auth-page a:focus-visible, .provider-button:focus-visible { outline: 2px solid #567a42; outline-offset: 5px; }
	@keyframes provider-spin { to { transform: rotate(360deg); } }
	@media (min-width: 1500px) { .auth-layout { gap: 100px; } .welcome-panel { padding-inline: 53px; } }
	@media (max-width: 1100px) { .page-width { width: calc(100% - 64px); } .auth-layout { gap: 32px; grid-template-columns: 1fr 1fr; } .welcome-panel { padding: 40px 28px 28px; min-height: 610px; } .welcome-copy h2 { font-size: 37px; } .source-note { right: -10px; width: 292px; padding: 14px; gap: 9px; } .source-note strong { font-size: 10px; } .document-paper { right: 25px; width: 248px; padding: 22px; } .document-shadow { right: 9px; width: 248px; } .sign-in-panel { padding-inline: 0; } h1 { font-size: 38px; } }
	@media (max-width: 850px) { .auth-nav { min-height: 88px; } .auth-layout { grid-template-columns: 1fr; padding-block: 58px 62px; } .welcome-panel { display: none; } .sign-in-panel { padding: 0; } .sign-in-content { max-width: 370px; } .auth-footer { min-height: 73px; } h1 { font-size: 45px; } .form-mark { margin-bottom: 28px; } .sign-in-description { font-size: 14px; } .provider-button { min-height: 56px; font-size: 14px; } }
	@media (max-width: 480px) { .page-width { width: calc(100% - 40px); } .auth-nav { min-height: 82px; } .auth-nav > a:first-child :global(svg) { max-width: 108px; } .back-link { gap: 7px; font-size: 11px; } .auth-layout { padding-block: 42px 46px; } .sign-in-content { max-width: 340px; } .form-mark { width: 55px; height: 55px; border-radius: 12px; margin-bottom: 23px; } .form-mark :global(svg) { width: 31px; height: 31px; } h1 { font-size: 40px; } .sign-in-description { margin-top: 15px; font-size: 12px; } .provider-buttons { margin-top: 27px; } .provider-button { min-height: 54px; font-size: 12px; gap: 11px; padding-inline: 15px; } .account-note { gap: 9px; margin-top: 26px; } .account-note p { font-size: 9px; } .privacy-note { margin-top: 22px; } .auth-footer { min-height: 65px; font-size: 9px; } }
	@media (prefers-reduced-motion: reduce) { .auth-page :global(*), .auth-page :global(*::before), .auth-page :global(*::after) { animation: none !important; transition: none !important; } }
</style>
