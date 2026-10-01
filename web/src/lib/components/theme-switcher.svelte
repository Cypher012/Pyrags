<script lang="ts">
	import MoonIcon from '@lucide/svelte/icons/moon';
	import SunIcon from '@lucide/svelte/icons/sun';
	import SunMoonIcon from '@lucide/svelte/icons/sun-moon';
	import { toggleMode } from 'mode-watcher';
	import { Button } from '$lib/components/ui/button/index.js';
	import { cn } from '$lib/utils.js';

	let { inMenu = false }: { inMenu?: boolean } = $props();
</script>

<div
	class={cn(
		'flex items-center justify-between gap-4 text-sm',
		inMenu
			? 'w-full rounded-md px-2 py-2'
			: 'w-fit min-w-44 rounded-lg border border-border bg-card px-3 py-2.5'
	)}
>
	<span class="flex items-center gap-2 text-foreground">
		<SunMoonIcon class="size-4 text-muted-foreground" />
		Theme
	</span>
	<Button onclick={toggleMode} variant="outline" size="icon" aria-label="Toggle theme">
		<SunIcon
			class="h-[1.2rem] w-[1.2rem] scale-100 rotate-0 !transition-all dark:scale-0 dark:-rotate-90"
		/>
		<MoonIcon
			class="absolute h-[1.2rem] w-[1.2rem] scale-0 rotate-90 !transition-all dark:scale-100 dark:rotate-0"
		/>
	</Button>
</div>
