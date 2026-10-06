import API_ROUTES from '$lib/api_routes';
import { authClient } from '$lib/auth-client';

export type UploadStage =
	'queued' | 'upload' | 'extracting' | 'chunking' | 'embedding' | 'storing' | 'completed' | 'error';

export type UploadProgress = {
	stage: UploadStage;
	message: string;
	progress: number;
	conversation_id?: string | null;
};

type UploadProgressCallbacks = {
	onProgress?: (data: UploadProgress) => void;
	onCompleted?: (data: UploadProgress) => void;
	onError?: (message: string) => void;
};

export function useUploadProgress(callbacks: UploadProgressCallbacks = {}) {
	let progress = $state(0);
	let message = $state('');
	let stage = $state<UploadStage>('queued');
	let isTracking = $state(false);
	let controller: AbortController | null = null;

	function resetProgress() {
		progress = 0;
		message = '';
		stage = 'queued';
	}

	function stopTracking() {
		controller?.abort();
		controller = null;
		isTracking = false;
	}

	function handleEvent(data: UploadProgress) {
		if (data.stage === 'completed' && !data.conversation_id) {
			fail('Processing completed without a conversation. Please try again.');
			return true;
		}
		progress = Math.max(0, Math.min(100, data.progress));
		message = data.message;
		stage = data.stage;

		callbacks.onProgress?.(data);

		if (data.stage === 'completed') {
			progress = 100;
			callbacks.onCompleted?.(data);
			stopTracking();
			return true;
		}

		if (data.stage === 'error') {
			callbacks.onError?.(data.message);
			stopTracking();
			return true;
		}
		return false;
	}

	function fail(errorMessage: string) {
		message = errorMessage;
		stage = 'error';
		callbacks.onError?.(errorMessage);
		stopTracking();
	}

	async function startTracking(jobId: string) {
		stopTracking();

		progress = 0;
		message = 'Waiting for processing to start';
		stage = 'queued';

		const current = new AbortController();
		controller = current;
		isTracking = true;
		for (let attempt = 0; attempt <= 5 && !current.signal.aborted; attempt++) {
			let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;

			try {
				const { data, error } = await authClient.token();
				if (current.signal.aborted) return;
				if (error || !data?.token) {
					fail('You need to be signed in to track processing');
					return;
				}

				const response = await fetch(API_ROUTES.upload_status(jobId), {
					headers: {
						Authorization: `Bearer ${data.token}`,
						Accept: 'text/event-stream'
					},
					signal: current.signal
				});

				if ([401, 403, 404].includes(response.status)) {
					fail(response.status === 404 ? 'Processing job is no longer available' : 'Sign in again to track processing');
					return;
				}
				if (!response.ok || !response.body) {
					throw new Error(`Status stream failed (${response.status})`);
				}

				reader = response.body.getReader();
				const decoder = new TextDecoder();
				let buffer = '';
				let eventData: string[] = [];
				let eventType = '';
				let terminal = false;

				function readLine(line: string) {
					if (!line) {
						if (eventType === 'error') throw new Error('The server reported a processing error');
						if (eventData.length) {
							const update = JSON.parse(eventData.join('\n')) as UploadProgress;
							if (
								typeof update?.message !== 'string' ||
								typeof update.stage !== 'string' ||
								!Number.isFinite(update.progress)
							) {
								throw new Error('Invalid processing update');
							}
							terminal = handleEvent(update);
						}
						eventData = [];
						eventType = '';
						return;
					}
					const separator = line.indexOf(':');
					const field = separator === -1 ? line : line.slice(0, separator);
					let value = separator === -1 ? '' : line.slice(separator + 1);
					if (value.startsWith(' ')) value = value.slice(1);
					if (field === 'data') eventData.push(value);
					if (field === 'event') eventType = value;
				}

				while (true) {
					const { value, done } = await reader.read();
					if (current.signal.aborted) return;
					buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
					while (!terminal) {
						const lineEnd = buffer.search(/[\r\n]/);
						if (lineEnd === -1) break;
						if (!done && buffer[lineEnd] === '\r' && lineEnd === buffer.length - 1) break;
						const separatorLength = buffer.slice(lineEnd, lineEnd + 2) === '\r\n' ? 2 : 1;
						readLine(buffer.slice(0, lineEnd));
						buffer = buffer.slice(lineEnd + separatorLength);
					}
					if (terminal) return;
					if (done) throw new Error('Processing stream ended before completion');
				}
			} catch (trackingError) {
				if (current.signal.aborted) return;

				console.error('Upload progress tracking failed:', trackingError);
				if (attempt === 5) {
					fail('Connection interrupted. Your document may still be processing; check Recents.');
					return;
				}
				message = 'Reconnecting to document processing';
				await new Promise<void>((resolve) => {
					const finish = () => {
						clearTimeout(timer);
						current.signal.removeEventListener('abort', finish);
						resolve();
					};
					const timer = setTimeout(finish, Math.min(1000 * 2 ** attempt, 10000));
					current.signal.addEventListener('abort', finish, { once: true });
					if (current.signal.aborted) finish();
				});
			} finally {
				if (reader) {
					await reader.cancel().catch(() => {});
					reader.releaseLock();
				}
			}
		}
		if (controller === current) stopTracking();
	}

	return {
		get progress() {
			return progress;
		},

		get message() {
			return message;
		},

		get stage() {
			return stage;
		},

		get isTracking() {
			return isTracking;
		},

		startTracking,
		stopTracking,
		resetProgress
	};
}
