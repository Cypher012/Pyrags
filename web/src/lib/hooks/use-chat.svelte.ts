import { browser } from '$app/environment';
import { invalidate } from '$app/navigation';
import { api } from '$lib/api';
import API_ROUTES from '$lib/api_routes';
import { authClient } from '$lib/auth-client';
import { readChatStream } from '$lib/chat-stream';
import type { Message } from '$lib/types/message';
import type { SourceDocument } from '$lib/types/source-document';
import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
import { SvelteDate } from 'svelte/reactivity';
import { toast } from 'svelte-sonner';
import type { AxiosRequestConfig } from 'axios';
import { isAxiosError } from 'axios';
import { queryUsageKey } from '$lib/hooks/use-query-usage.svelte';
import type { QueryUsage } from '$lib/types/query-usage';

export type ChatOptions = { model: string; isStream: boolean };

type SendRequest = { message: ChatMessage; options: ChatOptions };

type ChatMessage = Message & { pending?: boolean; awaitingReply?: boolean };

type ChatResponse = {
	conversation_id: string;
	response: string;
	source_documents?: SourceDocument[];
};

class DailyQueryLimitError extends Error {}

export function useChat(conversationId: string, initialMessages: Message[]) {
	const queryClient = useQueryClient();
	const queryKey = ['conversation-messages', conversationId] as const;
	const messages = createQuery<ChatMessage[]>(() => ({
		queryKey,
		queryFn: async () => {
			const response = await api.get<Message[]>(API_ROUTES.conversation_messages(conversationId));
			return response.data;
		},
		initialData: initialMessages,
		staleTime: Infinity,
		enabled: browser
	}));

	function markMessageSent(message: ChatMessage) {
		queryClient.setQueryData<ChatMessage[]>(queryKey, (current = []) =>
			current.map((currentMessage) =>
				currentMessage.id === message.id && currentMessage.pending
					? { ...currentMessage, pending: false, awaitingReply: true }
					: currentMessage
			)
		);
	}

	function updateReply(message: ChatMessage, content: string, sources?: SourceDocument[]) {
		const replyId = `reply-${message.id}`;
		const timestamp = new SvelteDate().toISOString();
		queryClient.setQueryData<ChatMessage[]>(queryKey, (current = []) => {
			const updated = current.map((currentMessage) => {
				if (currentMessage.id === message.id) {
					return { ...currentMessage, pending: false, awaitingReply: false };
				}
				if (currentMessage.id === replyId) {
					return {
						...currentMessage,
						content,
						source_documents: sources ?? currentMessage.source_documents
					};
				}
				return currentMessage;
			});
			if (updated.some((currentMessage) => currentMessage.id === replyId)) return updated;
			return [
				...updated,
				{
					id: replyId,
					conversation_id: conversationId,
					role: 'assistant',
					content,
					source_documents: sources,
					created_at: timestamp,
					updated_at: timestamp
				}
			];
		});
	}

	const send = createMutation(() => ({
		mutationFn: async ({ message, options }: SendRequest) => {
			const body = {
				message: message.content,
				is_stream: options.isStream,
				model_provider: 'openai',
				model_options: { model: options.model, temperature: 0 }
			};
			const config: AxiosRequestConfig = {
				onUploadProgress: ({ progress }) => {
					if (progress !== 1) return;
					markMessageSent(message);
				}
			};
			if (options.isStream) {
				const { data, error } = await authClient.token();
				if (error || !data?.token) throw new Error('Not authenticated');
				const response = await fetch(
					api.getUri({ url: API_ROUTES.query_chatbot(conversationId) }),
					{
						method: 'POST',
						headers: {
							'Content-Type': 'application/json',
							Accept: 'text/event-stream, application/x-ndjson',
							Authorization: `Bearer ${data.token}`
						},
						body: JSON.stringify(body)
					}
				);
				if (!response.ok) {
					if (response.status === 429) {
						const payload = (await response.json()) as {
							detail?: { message?: string; usage?: QueryUsage };
						};
						if (payload.detail?.usage)
							queryClient.setQueryData<QueryUsage>(queryUsageKey, payload.detail.usage);
						throw new DailyQueryLimitError(
							payload.detail?.message ??
								'Daily query limit reached. Try again after midnight (Lagos time).'
						);
					}
					throw new Error(`Chat request failed (${response.status})`);
				}
				if (!response.body) throw new Error('No chat response body');
				markMessageSent(message);
				const format = response.headers.get('Content-Type')?.includes('application/x-ndjson')
					? 'ndjson'
					: 'sse';
				const result = await readChatStream(
					response.body,
					(content) => updateReply(message, content),
					format
				);
				return {
					conversation_id: conversationId,
					response: result.content,
					source_documents: result.source_documents
				};
			}
			const response = await api.post<ChatResponse>(
				API_ROUTES.query_chatbot(conversationId),
				body,
				config
			);
			return response.data;
		},
		retry: false,
		onMutate: async ({ message }) => {
			await queryClient.cancelQueries({ queryKey });
			const previousMessages = queryClient.getQueryData<ChatMessage[]>(queryKey) ?? [];
			queryClient.setQueryData<ChatMessage[]>(queryKey, [...previousMessages, message]);
			return { previousMessages };
		},
		onSuccess: async (response, { message }) => {
			updateReply(message, response.response, response.source_documents ?? []);
			const refreshResults = await Promise.allSettled([
				queryClient.invalidateQueries({ queryKey }),
				invalidate('app:conversations')
			]);
			for (const result of refreshResults) {
				if (result.status === 'rejected')
					console.error('Could not refresh conversation:', result.reason);
			}
		},
		onError: (error, _message, context) => {
			console.error('Chat request failed:', error.message);
			if (context) {
				queryClient.setQueryData(queryKey, context.previousMessages);
			}
			if (isAxiosError(error) && error.response?.status === 429) {
				const detail = error.response.data?.detail;
				if (detail?.usage) queryClient.setQueryData<QueryUsage>(queryUsageKey, detail.usage);
				toast.error(
					detail?.message ?? 'Daily query limit reached. Try again after midnight (Lagos time).'
				);
			} else {
				toast.error(
					error instanceof DailyQueryLimitError
						? error.message
						: 'Could not send your message. Please try again.'
				);
			}
		},
		onSettled: async () => {
			await queryClient.invalidateQueries({ queryKey: queryUsageKey });
		}
	}));

	return {
		get messages() {
			return messages.data;
		},
		get isSending() {
			return send.isPending;
		},
		get isThinking() {
			return messages.data.some((message) => message.awaitingReply);
		},
		sendMessage(content: string, options: ChatOptions) {
			const timestamp = new SvelteDate().toISOString();
			return send.mutateAsync({
				message: {
					id: crypto.randomUUID(),
					conversation_id: conversationId,
					role: 'user',
					content,
					created_at: timestamp,
					updated_at: timestamp,
					pending: true
				},
				options: { ...options }
			});
		}
	};
}
