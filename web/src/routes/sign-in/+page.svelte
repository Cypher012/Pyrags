<script lang="ts">
	import BrandLogo from '$lib/assets/logo.svg?component';
	import GoogleLogo from '$lib/assets/google.svg?component';
	import GithubLogo from '$lib/assets/github.svg?component';
	import Button from '$lib/components/ui/button/button.svelte';
	import { ArrowRight, LockKeyhole } from '@lucide/svelte';
	import { authClient } from '$lib/auth-client';

	type Provider = 'google' | 'github';

	const signIn = async (provider: Provider) => {
		switch (provider) {
			case 'google':
				await authClient.signIn.social({
					provider: 'google',
					callbackURL: '/app'
				});
				break;
			case 'github':
				await authClient.signIn.social({
					provider: 'github',
					callbackURL: '/app'
				});
				break;
			default:
				throw new Error(`No ${provider} provider`);
		}
	};
</script>

<main
	class="mx-auto flex min-h-dvh w-full max-w-3xl flex-col items-center justify-center px-5 py-12 sm:px-8"
>
	<BrandLogo class="mb-8 h-auto w-44 sm:mb-10 sm:w-60" />
	<h1
		class="text-muted-accent max-w-2xl text-center font-heading text-3xl leading-tight tracking-tight text-balance sm:text-[42px] sm:leading-[1.15]"
	>
		Understand documents, together with their sources.
	</h1>
	<p class="mt-3 max-w-xl text-center text-base leading-relaxed text-muted-foreground sm:text-lg">
		Sign in to start exploring your course material.
	</p>

	<div class="mt-12 flex w-full max-w-lg flex-col gap-4 sm:mt-16">
		<Button
			onclick={() => signIn('google')}
			variant="outline"
			class="h-16 w-full justify-start gap-3 rounded-xl px-5 text-sm font-normal text-foreground min-[380px]:text-base sm:h-[72px] sm:gap-6 sm:px-7 sm:text-lg"
		>
			<GoogleLogo class="size-6 sm:size-8" />
			<span>Continue with Google</span>
			<ArrowRight class="ml-auto size-5 text-muted-foreground sm:size-6" />
		</Button>
		<Button
			onclick={() => signIn('github')}
			variant="outline"
			class="h-16 w-full justify-start gap-3 rounded-xl px-5 text-sm font-normal text-foreground min-[380px]:text-base sm:h-[72px] sm:gap-6 sm:px-7 sm:text-lg"
		>
			<GithubLogo class="size-6 sm:size-8" />
			<span>Continue with GitHub</span>
			<ArrowRight class="ml-auto size-5 text-muted-foreground sm:size-6" />
		</Button>
	</div>
	<p
		class="mt-14 flex items-center gap-3 text-center text-sm text-muted-foreground sm:mt-20 sm:text-base"
	>
		<LockKeyhole class="size-5 shrink-0 sm:size-6" />
		Your documents stay connected to your conversation.
	</p>
</main>
