declare module '*.svg?component' {
	import type { Component } from 'svelte';
	const content: Component;
	export default content;
}
