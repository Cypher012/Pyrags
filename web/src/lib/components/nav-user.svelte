<script lang="ts">
	import ChevronsUpDownIcon from '@lucide/svelte/icons/chevrons-up-down';
	import LogOutIcon from '@lucide/svelte/icons/log-out';
	import * as Avatar from '$lib/components/ui/avatar/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { useSidebar } from '$lib/components/ui/sidebar/index.js';
	import ThemeSwitcher from './theme-switcher.svelte';
	import type { User } from '$lib/types/user';
	import { authClient } from '$lib/auth-client';

	let { user }: { user: User } = $props();
	const sidebar = useSidebar();

	function getInitials(fullname: string): string {
		const names = fullname.trim().split(/\s+/).filter(Boolean);
		if (names.length === 0) return '';
		if (names.length === 1) return names[0][0].toUpperCase();
		return (names[0][0] + names[names.length - 1][0]).toUpperCase();
	}

	async function logout() {
		await authClient.signOut();
		window.location.href = '/sign-in';
	}
</script>

<Sidebar.Menu>
	<Sidebar.MenuItem>
		<DropdownMenu.Root>
			<DropdownMenu.Trigger>
				{#snippet child({ props })}
					<Sidebar.MenuButton
						size="lg"
						class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
						{...props}
					>
						<Avatar.Root class="size-8 rounded-lg">
							{#if user.image}<Avatar.Image src={user.image} alt={user.name} />{/if}
							<Avatar.Fallback class="rounded-lg">{getInitials(user.name)}</Avatar.Fallback>
						</Avatar.Root>
						<div class="grid flex-1 text-start text-sm leading-tight">
							<span class="truncate font-medium">{user.name}</span>
							<span class="truncate text-xs">{user.email}</span>
						</div>
						<ChevronsUpDownIcon class="ms-auto size-4" />
					</Sidebar.MenuButton>
				{/snippet}
			</DropdownMenu.Trigger>
			<DropdownMenu.Content
				class="w-(--bits-dropdown-menu-anchor-width) min-w-64 rounded-xl p-2 shadow-lg"
				side={sidebar.isMobile ? 'bottom' : 'right'}
				align="end"
				sideOffset={4}
			>
				<DropdownMenu.Label class="px-2 py-2 font-normal">
					<div class="flex items-center gap-3 text-start text-sm">
						<Avatar.Root class="size-9 rounded-lg ring-1 ring-border">
							{#if user.image}<Avatar.Image src={user.image} alt={user.name} />{/if}
							<Avatar.Fallback class="rounded-lg">CN</Avatar.Fallback>
						</Avatar.Root>
						<div class="grid flex-1 text-start text-sm leading-tight">
							<span class="truncate font-medium">{user.name}</span>
							<span class="truncate text-xs">{user.email}</span>
						</div>
					</div>
				</DropdownMenu.Label>
				<DropdownMenu.Separator class="my-2" />
				<DropdownMenu.Group>
					<ThemeSwitcher inMenu />
				</DropdownMenu.Group>
				<DropdownMenu.Separator class="my-2" />
				<DropdownMenu.Item onclick={logout} class="px-2 py-2">
					<LogOutIcon />
					Log out
				</DropdownMenu.Item>
			</DropdownMenu.Content>
		</DropdownMenu.Root>
	</Sidebar.MenuItem>
</Sidebar.Menu>
