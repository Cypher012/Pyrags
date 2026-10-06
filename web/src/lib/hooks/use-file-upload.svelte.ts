import { api } from '$lib/api';
import API_ROUTES from '$lib/api_routes';
import {
	clearDocuments,
	deleteDocument,
	getDocuments,
	saveDocuments,
	type StoredDocument
} from '$lib/indexed-db/documents';
import { toast } from 'svelte-sonner';
import { isAxiosError } from 'axios';

type FileError = {
	code: string;
	message: string;
};

type FileRejection = {
	file: File;
	errors: FileError[];
};

export type DropDetail = {
	acceptedFiles: File[];
	fileRejections: FileRejection[];
};

export type UploadFileResponse = {
	job_id: string;
	filename: string;
};

export const MAX_DOCUMENTS = 3;
export const MAX_DOCUMENT_BYTES = 10 * 1024 * 1024;

export type BatchUploadResponse = {
	conversation_id: string;
	jobs: { job_id: string; document_id: string; filename: string }[];
};

export function formatFileSize(size: number) {
	return size >= 1024 * 1024
		? `${(size / 1024 / 1024).toFixed(1)} MB`
		: `${(size / 1024).toFixed(1)} KB`;
}

export function useFileUpload() {
	let documents = $state<StoredDocument[]>([]);
	let uploadedData = $state<BatchUploadResponse | null>(null);
	let isDragging = $state(false);
	let isSaving = $state(false);

	async function restoreDocuments() {
		try {
			documents = await getDocuments();
		} catch (error) {
			console.error('Failed to restore documents:', error);
			toast.error('Could not restore saved documents.');
		}
	}

	async function uploadFiles(files: File[]): Promise<BatchUploadResponse> {
		const formData = new FormData();

		for (const file of files) formData.append('files', file);

		const response = await api.post<BatchUploadResponse>(API_ROUTES.upload_files, formData);

		return response.data;
	}

	async function handleFilesSelect(event: CustomEvent<DropDetail>) {
		if (isSaving) return;
		const { acceptedFiles, fileRejections } = event.detail;

		for (const rejection of fileRejections) {
			const isTooLarge = rejection.errors.some((error) => error.code === 'file-too-large');

			toast.error(
				isTooLarge ? 'Each file must be smaller than 10 MiB.' : 'Only PDF and DOCX files are allowed.'
			);
		}

		if (!acceptedFiles.length) {
			isDragging = false;
			return;
		}

		if (documents.length + acceptedFiles.length > MAX_DOCUMENTS) {
			toast.error('You can select at most three documents. Remove one before adding more.');
			isDragging = false;
			return;
		}
		if (acceptedFiles.some((file) => file.size === 0 || file.size >= MAX_DOCUMENT_BYTES)) {
			toast.error('Each document must be non-empty and smaller than 10 MiB.');
			isDragging = false;
			return;
		}

		try {
			isSaving = true;
			const storedDocuments = await saveDocuments(acceptedFiles);
			documents = [...documents, ...storedDocuments];
			uploadedData = null;
		} catch (error) {
			console.error('Failed to save document:', error);
			toast.error('Could not save the document.');
		} finally {
			isDragging = false;
			isSaving = false;
		}
	}

	async function handleFileRemoval(id: string) {
		const previousDocuments = documents;

		documents = documents.filter((document) => document.id !== id);
		uploadedData = null;

		try {
			await deleteDocument(id);
		} catch (error) {
			documents = previousDocuments;

			console.error('Failed to delete document:', error);
			toast.error('Failed to delete document.');
		}
	}

	async function handleUploadDocument() {
		if (isSaving) {
			toast.error('Wait until your selected documents have been saved.');
			throw new Error('Document selection is still being saved');
		}
		if (!documents.length || documents.length > MAX_DOCUMENTS) {
			toast.error('Select a document first.');
			throw new Error('Select a document first');
		}
		if (documents.some((document) => document.size === 0 || document.size >= MAX_DOCUMENT_BYTES)) {
			toast.error('Each document must be non-empty and smaller than 10 MiB.');
			throw new Error('Invalid document size');
		}

		uploadedData = null;
		try {
			uploadedData = await uploadFiles(documents.map((document) => document.file));

			toast.success('Documents uploaded. Processing has started.');
		} catch (error) {
			console.error('Failed to upload document:', error);
			const detail = isAxiosError(error) ? error.response?.data?.detail : undefined;
			toast.error(typeof detail === 'string' ? detail : 'Could not upload the documents.');
			throw error;
		}
	}

	async function clearStoredDocuments() {
		await clearDocuments();
		uploadedData = null;
	}

	return {
		get documents() {
			return documents;
		},

		get uploadedData() {
			return uploadedData;
		},

		get isDragging() {
			return isDragging;
		},

		get isSaving() {
			return isSaving;
		},

		restoreDocuments,
		handleFilesSelect,
		handleFileRemoval,
		handleUploadDocument,
		clearStoredDocuments,

		handleDragEnter: () => {
			isDragging = true;
		},

		handleDragLeave: () => {
			isDragging = false;
		}
	};
}
