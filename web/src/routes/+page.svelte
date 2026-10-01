<script>
	import { api } from '$lib/api';
	import Button from '$lib/components/ui/button/button.svelte';

	let status = $state('');

	async function testApi() {
		const res = await api.get('/');
		status = res.data;
	}
</script>

<h1>Test backend health endpoint</h1>
<Button onclick={testApi}>test</Button>
<pre>{JSON.stringify(status, null, 2)}</pre>
