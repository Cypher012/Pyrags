import API_ROUTES from '$lib/api_routes';

export type UploadStage =
	'queued' | 'upload' | 'extracting' | 'chunking' | 'embedding' | 'storing' | 'completed' | 'error';

export type UploadProgress = {
	stage: UploadStage;
	message: string;
	progress: number;
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
	let source: EventSource | null = null;
	let isTracking = $state(false);

	function resetProgress() {
		progress = 0;
		message = '';
		stage = 'queued';
	}

	function stopTracking() {
		source?.close();
		source = null;
		isTracking = false;
	}

	function startTracking(jobId: string) {
		stopTracking();

		progress = 0;
		message = 'Waiting for processing to start';
		stage = 'queued';

		source = new EventSource(API_ROUTES.upload_status(jobId));
		isTracking = true;

		source.onmessage = (event) => {
			const data = JSON.parse(event.data) as UploadProgress;

			progress = Math.max(0, Math.min(100, data.progress));
			message = data.message;
			stage = data.stage;

			callbacks.onProgress?.(data);

			if (data.stage === 'completed') {
				progress = 100;

				callbacks.onCompleted?.(data);
				stopTracking();
			}

			if (data.stage === 'error') {
				callbacks.onError?.(data.message);
				stopTracking();
			}
		};

		source.onerror = () => {
			const errorMessage = 'Connection interrupted while tracking processing';

			message = errorMessage;
			stage = 'error';

			callbacks.onError?.(errorMessage);
			stopTracking();
		};
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
