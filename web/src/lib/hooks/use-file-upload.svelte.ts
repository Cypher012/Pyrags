import { api } from '$lib/api';
import API_ROUTES from '$lib/api_routes';
import {
	clearDocuments,
	deleteDocument,
	getDocuments,
	saveDocument,
	type StoredDocument
} from '$lib/indexed-db/documents';
import { toast } from 'svelte-sonner';

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

export function formatFileSize(size: number) {
	return size >= 1024 * 1024
		? `${(size / 1024 / 1024).toFixed(1)} MB`
		: `${(size / 1024).toFixed(1)} KB`;
}

export function useFileUpload() {
	let documents = $state<StoredDocument[]>([]);
	let uploadedData = $state<UploadFileResponse | null>(null);
	let isDragging = $state(false);

	async function restoreDocuments() {
		try {
			documents = await getDocuments();
		} catch (error) {
			console.error('Failed to restore documents:', error);
			toast.error('Could not restore saved documents.');
		}
	}

	async function uploadFile(file: File): Promise<UploadFileResponse> {
		const formData = new FormData();

		formData.append('file', file);

		const response = await api.post<UploadFileResponse>(API_ROUTES.upload_file, formData);

		return response.data;
	}

	async function handleFilesSelect(event: CustomEvent<DropDetail>) {
		const { acceptedFiles, fileRejections } = event.detail;

		for (const rejection of fileRejections) {
			const isTooLarge = rejection.errors.some((error) => error.code === 'file-too-large');

			toast.error(
				isTooLarge ? 'File must be smaller than 5 MB.' : 'Only PDF and DOCX files are allowed.'
			);
		}

		const file = acceptedFiles[0];

		if (!file) {
			isDragging = false;
			return;
		}

		try {
			// Only one document is supported for now.
			await clearDocuments();

			const storedDocument = await saveDocument(file);

			documents = [storedDocument];
			uploadedData = null;
		} catch (error) {
			console.error('Failed to save document:', error);
			toast.error('Could not save the document.');
		} finally {
			isDragging = false;
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
		const document = documents[0];

		if (!document) {
			toast.error('Select a document first.');
			throw new Error('Select a document first');
		}

		uploadedData = null;
		try {
			uploadedData = await uploadFile(document.file);

			toast.success('Document uploaded successfully.');
		} catch (error) {
			console.error('Failed to upload document:', error);
			toast.error('Could not upload the document.');
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
