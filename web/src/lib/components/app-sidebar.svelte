<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import BrandLogo from '$lib/assets/logo.svg?component';
	import LogoMark from '$lib/assets/logo-mark.svg?component';
	import PanelLeftIcon from '@lucide/svelte/icons/panel-left';
	import NavUser from './nav-user.svelte';
	import type { ComponentProps } from 'svelte';
	import { resolve } from '$app/paths';
	import { Plus } from '@lucide/svelte';
	import type { User } from '$lib/types/user';

	const items = [
		{
			title: 'New Chat',
			url: '/app',
			icon: Plus
		}
	] as const;

	let {
		user,
		ref = $bindable(null),
		collapsible = 'icon',
		...restProps
	}: ComponentProps<typeof Sidebar.Root> & { user: User } = $props();
	const sidebar = Sidebar.useSidebar();
</script>

<Sidebar.Root bind:ref {collapsible} {...restProps}>
	<Sidebar.Header
		class="h-16 justify-center px-4 py-0 group-data-[collapsible=icon]:items-center group-data-[collapsible=icon]:px-2"
	>
		<div
			class="group/logo relative flex h-10 w-full items-center group-data-[collapsible=icon]:size-8"
		>
			<BrandLogo
				class="h-auto w-40 max-w-[calc(100%-2.5rem)] group-data-[collapsible=icon]:hidden"
			/>
			<button
				type="button"
				aria-label="Expand sidebar"
				onclick={() => sidebar.toggle()}
				class="group/mark hidden size-8 items-center justify-center rounded-md text-sidebar-foreground group-data-[collapsible=icon]:flex hover:bg-sidebar-accent focus-visible:ring-2 focus-visible:ring-sidebar-ring focus-visible:outline-none"
			>
				<LogoMark class="size-8 group-hover/mark:hidden" />
				<PanelLeftIcon class="hidden size-4 group-hover/mark:block" />
			</button>
			<Sidebar.Trigger
				class="absolute top-1 right-0 opacity-0 transition-opacity group-hover/logo:opacity-100 group-data-[collapsible=icon]:hidden focus-visible:opacity-100"
			/>
		</div>
	</Sidebar.Header>
	<Sidebar.Content>
		<Sidebar.Menu>
			{#each items as item (item.title)}
				<Sidebar.MenuItem class="mt-8 px-3">
					<Sidebar.MenuButton class="px-3 py-6">
						{#snippet child({ props })}
							<a href={resolve(item.url)} {...props}>
								<item.icon />
								<span>{item.title}</span>
							</a>
						{/snippet}
					</Sidebar.MenuButton>
				</Sidebar.MenuItem>
			{/each}
		</Sidebar.Menu>
	</Sidebar.Content>
	<Sidebar.Footer>
		<NavUser {user} />
	</Sidebar.Footer>
	<Sidebar.Rail />
</Sidebar.Root>
