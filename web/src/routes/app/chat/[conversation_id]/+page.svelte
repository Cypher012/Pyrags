<script lang="ts">
	import type { PageData } from './$types';
	import Conversation from './conversation.svelte';

	let { data }: { data: PageData } = $props();
</script>

{#key data.conversation.id}
	<Conversation conversation={data.conversation} messages={data.messages} />
{/key}
