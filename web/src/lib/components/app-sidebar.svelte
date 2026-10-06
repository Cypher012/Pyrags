<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Collapsible from '$lib/components/ui/collapsible/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import Input from '$lib/components/ui/input/input.svelte';
	import Button from '$lib/components/ui/button/button.svelte';
	import BrandLogo from '$lib/assets/logo.svg?component';
	import LogoMark from '$lib/assets/logo-mark.svg?component';
	import PanelLeftIcon from '@lucide/svelte/icons/panel-left';
	import NavUser from './nav-user.svelte';
	import type { ComponentProps } from 'svelte';
	import { resolve } from '$app/paths';
	import { ChevronRight, Ellipsis, Plus, PencilLine, Trash2 } from '@lucide/svelte';
	import type { User } from '$lib/types/user';
	import type { Conversation } from '$lib/types/conversation';
	import { goto, invalidate } from '$app/navigation';
	import { page } from '$app/state';
	import { api } from '$lib/api';
	import API_ROUTES from '$lib/api_routes';
	import { useQueryClient } from '@tanstack/svelte-query';
	import { toast } from 'svelte-sonner';
	import { useQueryUsage } from '$lib/hooks/use-query-usage.svelte';

	const items = [
		{
			title: 'New Chat',
			url: '/app',
			icon: Plus
		}
	] as const;

	let {
		user,
		conversations,
		ref = $bindable(null),
		collapsible = 'icon',
		...restProps
	}: ComponentProps<typeof Sidebar.Root> & { user: User; conversations: Conversation[] } = $props();
	const sidebar = Sidebar.useSidebar();
	const queryClient = useQueryClient();
	const queryUsage = useQueryUsage();
	let selectedConversation = $state<Conversation | null>(null);
	let action = $state<'rename' | 'delete'>('rename');
	let dialogOpen = $state(false);
	let titleDraft = $state('');
	let actionError = $state('');
	let isSaving = $state(false);

	function openConversationAction(conversation: Conversation, selectedAction: 'rename' | 'delete') {
		selectedConversation = conversation;
		action = selectedAction;
		titleDraft = conversation.title;
		actionError = '';
		dialogOpen = true;
	}

	async function refreshConversations(deletedId?: string) {
		try {
			if (deletedId && page.params.conversation_id === deletedId) {
				await goto(resolve('/app'), { invalidateAll: true });
			} else {
				await invalidate('app:conversations');
			}
		} catch {
			if (deletedId && page.params.conversation_id === deletedId) {
				window.location.assign(resolve('/app'));
			} else {
				toast.warning('Change saved. Refresh the page to update your conversation list.');
			}
		}
	}

	async function saveRename(event: SubmitEvent) {
		event.preventDefault();
		const title = titleDraft.trim();
		if (!selectedConversation || isSaving) return;
		if (!title || title.length > 200) {
			actionError = 'Enter a title between 1 and 200 characters.';
			return;
		}
		isSaving = true;
		actionError = '';
		try {
			const { data } = await api.patch<Conversation>(API_ROUTES.conversation(selectedConversation.id), { title });
			conversations = conversations.map((conversation) => conversation.id === data.id ? data : conversation);
			dialogOpen = false;
			toast.success('Conversation renamed');
			await refreshConversations();
		} catch {
			actionError = 'Could not rename this conversation. Please try again.';
		} finally {
			isSaving = false;
		}
	}

	async function confirmDelete() {
		if (!selectedConversation || isSaving) return;
		const conversationId = selectedConversation.id;
		isSaving = true;
		actionError = '';
		try {
			await api.delete(API_ROUTES.conversation(conversationId));
			conversations = conversations.filter((conversation) => conversation.id !== conversationId);
			queryClient.removeQueries({ queryKey: ['conversation-messages', conversationId] });
			dialogOpen = false;
			toast.success('Conversation deleted');
			await refreshConversations(conversationId);
		} catch {
			actionError = 'Could not delete this conversation. Please try again.';
		} finally {
			isSaving = false;
		}
	}
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
							<a href={resolve(item.url)} {...props} aria-label={item.title}>
								<item.icon />
								<span class="group-data-[collapsible=icon]:hidden">{item.title}</span>
							</a>
						{/snippet}
					</Sidebar.MenuButton>
				</Sidebar.MenuItem>
			{/each}
		</Sidebar.Menu>

		<Collapsible.Root open class="group/collapsible group-data-[collapsible=icon]:hidden">
			<Sidebar.Group>
				<Sidebar.GroupLabel>
					{#snippet child({ props })}
						<Collapsible.Trigger {...props}>
							Recents
							<ChevronRight
								class="ml-3 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90"
							/>
						</Collapsible.Trigger>
					{/snippet}
				</Sidebar.GroupLabel>

				<Collapsible.Content>
					<Sidebar.GroupContent>
						<Sidebar.Menu class="space-y-3">
							{#each conversations as conversation (conversation.id)}
								<Sidebar.MenuItem class="">
									<Sidebar.MenuButton
										isActive={page.params.conversation_id === conversation.id}
										onclick={() =>
											goto(
												resolve('/app/chat/[conversation_id]', {
													conversation_id: conversation.id
												})
											)}
										class="flex items-center px-3 py-5 text-foreground/80"
									>
										<span>{conversation.title}</span>
									</Sidebar.MenuButton>
									<DropdownMenu.Root>
										<DropdownMenu.Trigger>
											{#snippet child({ props })}
												<Sidebar.MenuAction {...props} showOnHover disabled={isSaving} aria-label={`Conversation actions for ${conversation.title}`} class="top-2 right-2 size-6">
													<Ellipsis class="size-4" />
												</Sidebar.MenuAction>
											{/snippet}
										</DropdownMenu.Trigger>
										<DropdownMenu.Content side="bottom" align="start" sideOffset={6} class="w-44 rounded-lg p-1.5" onCloseAutoFocus={(event) => { if (dialogOpen) event.preventDefault(); }}>
											<DropdownMenu.Item onclick={() => openConversationAction(conversation, 'rename')} class="rounded-md px-3 py-2.5">
												<PencilLine class="size-4" /> Rename
											</DropdownMenu.Item>
											<DropdownMenu.Separator class="my-1" />
											<DropdownMenu.Item variant="destructive" onclick={() => openConversationAction(conversation, 'delete')} class="rounded-md px-3 py-2.5">
												<Trash2 class="size-4" /> Delete
											</DropdownMenu.Item>
										</DropdownMenu.Content>
									</DropdownMenu.Root>
								</Sidebar.MenuItem>
							{/each}
						</Sidebar.Menu>
					</Sidebar.GroupContent>
				</Collapsible.Content>
			</Sidebar.Group>
		</Collapsible.Root>
	</Sidebar.Content>
	<Sidebar.Footer>
		<div class="mx-2 mb-2 rounded-lg border border-sidebar-border px-3 py-3 group-data-[collapsible=icon]:hidden" aria-live="polite">
			{#if queryUsage.data?.unlimited}
				<p class="text-xs font-medium text-sidebar-foreground">Unlimited queries</p>
			{:else if queryUsage.data}
				<div class="flex items-center justify-between gap-2 text-xs">
					<p class="font-medium text-sidebar-foreground">Daily queries</p>
					<span class="text-muted-foreground">{queryUsage.data.remaining} / {queryUsage.data.limit} left</span>
				</div>
				<div class="mt-2 flex gap-1" aria-hidden="true">
					{#each Array(queryUsage.data.limit ?? 6) as querySlot, index}
						<span class="h-1 flex-1 rounded-full {index < (queryUsage.data.remaining ?? 0) ? 'bg-primary' : 'bg-sidebar-accent'}"></span>
					{/each}
				</div>
				<p class="mt-2 text-[11px] text-muted-foreground">Resets at midnight · Lagos time</p>
			{:else}
				<p class="text-xs text-muted-foreground">{queryUsage.isError ? 'Daily usage unavailable' : 'Loading daily usage…'}</p>
			{/if}
		</div>
		<NavUser {user} />
	</Sidebar.Footer>
	<Sidebar.Rail />
</Sidebar.Root>

<Dialog.Root bind:open={dialogOpen}>
	{#if dialogOpen && selectedConversation}
		<Dialog.Content showCloseButton={!isSaving} onEscapeKeydown={(event) => { if (isSaving) event.preventDefault(); }} onInteractOutside={(event) => { if (isSaving) event.preventDefault(); }}>
			<Dialog.Header>
				<Dialog.Title>{action === 'rename' ? 'Rename conversation' : 'Delete conversation?'}</Dialog.Title>
				<Dialog.Description>
					{#if action === 'rename'}Choose a name that is easy to find in Recents.{:else}This permanently deletes “{selectedConversation.title}”, its messages, documents, and sources. This cannot be undone.{/if}
				</Dialog.Description>
			</Dialog.Header>
			{#if action === 'rename'}
				<form onsubmit={saveRename} class="space-y-5">
					<div class="space-y-2">
						<label for="conversation-title" class="text-sm font-medium">Conversation name</label>
						<Input id="conversation-title" bind:value={titleDraft} maxlength={200} required disabled={isSaving} aria-invalid={!!actionError} aria-describedby={actionError ? 'conversation-action-error' : undefined} />
						{#if actionError}<p id="conversation-action-error" role="alert" class="text-sm text-destructive">{actionError}</p>{/if}
					</div>
					<Dialog.Footer>
						<Button variant="outline" onclick={() => dialogOpen = false} disabled={isSaving}>Cancel</Button>
						<Button type="submit" disabled={isSaving || !titleDraft.trim() || titleDraft.trim() === selectedConversation.title}>{isSaving ? 'Saving…' : 'Save'}</Button>
					</Dialog.Footer>
				</form>
			{:else}
				{#if actionError}<p role="alert" class="text-sm text-destructive">{actionError}</p>{/if}
				<Dialog.Footer>
					<Button variant="outline" onclick={() => dialogOpen = false} disabled={isSaving}>Cancel</Button>
					<Button variant="destructive" onclick={confirmDelete} disabled={isSaving}>{isSaving ? 'Deleting…' : 'Delete conversation'}</Button>
				</Dialog.Footer>
			{/if}
		</Dialog.Content>
	{/if}
</Dialog.Root>
