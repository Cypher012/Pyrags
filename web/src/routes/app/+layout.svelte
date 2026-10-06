<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import type { Snippet } from 'svelte';
	import type { LayoutData } from './$types';

	interface Props {
		children: Snippet;
		data: LayoutData;
	}

	let { children, data }: Props = $props();

	const user = $derived(data.user);
	const conversations = $derived(data.conversations);
</script>

<Sidebar.Provider class="[--sidebar-width:16rem]! lg:[--sidebar-width:18rem]! xl:[--sidebar-width:20rem]! 2xl:[--sidebar-width:22rem]!">
	<AppSidebar {user} {conversations} />
	<Sidebar.Inset>
		<div class="flex flex-1 flex-col gap-4">
			{@render children()}
		</div>
	</Sidebar.Inset>
</Sidebar.Provider>
