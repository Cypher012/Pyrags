const DB_NAME = 'pyrags';
const DB_VERSION = 1;
const STORE_NAME = 'documents';

export type StoredDocumentType = 'pdf' | 'docx';

export type StoredDocument = {
	id: string;
	name: string;
	type: StoredDocumentType;
	size: number;
	file: File;
};

function getDocumentType(file: File): StoredDocumentType {
	const name = file.name.toLowerCase();

	if (file.type === 'application/pdf' || name.endsWith('.pdf')) {
		return 'pdf';
	}

	if (
		file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
		name.endsWith('.docx')
	) {
		return 'docx';
	}

	throw new Error('Unsupported document type');
}

function openDatabase(): Promise<IDBDatabase> {
	return new Promise((resolve, reject) => {
		const request = indexedDB.open(DB_NAME, DB_VERSION);

		request.onupgradeneeded = () => {
			const db = request.result;

			if (!db.objectStoreNames.contains(STORE_NAME)) {
				db.createObjectStore(STORE_NAME, {
					keyPath: 'id'
				});
			}
		};

		request.onsuccess = () => {
			resolve(request.result);
		};

		request.onerror = () => {
			reject(request.error);
		};
	});
}

export async function saveDocument(file: File): Promise<StoredDocument> {
	const db = await openDatabase();

	const document: StoredDocument = {
		id: crypto.randomUUID(),
		name: file.name,
		type: getDocumentType(file),
		size: file.size,
		file
	};

	return new Promise((resolve, reject) => {
		const transaction = db.transaction(STORE_NAME, 'readwrite');
		const store = transaction.objectStore(STORE_NAME);

		const request = store.add(document);

		request.onsuccess = () => {
			resolve(document);
		};

		request.onerror = () => {
			reject(request.error);
		};
	});
}

export async function getDocuments(): Promise<StoredDocument[]> {
	const db = await openDatabase();

	return new Promise((resolve, reject) => {
		const transaction = db.transaction(STORE_NAME, 'readonly');
		const store = transaction.objectStore(STORE_NAME);

		const request = store.getAll();

		request.onsuccess = () => {
			resolve(request.result as StoredDocument[]);
		};

		request.onerror = () => {
			reject(request.error);
		};
	});
}

export async function deleteDocument(id: string): Promise<void> {
	const db = await openDatabase();

	return new Promise((resolve, reject) => {
		const transaction = db.transaction(STORE_NAME, 'readwrite');
		const store = transaction.objectStore(STORE_NAME);

		const request = store.delete(id);

		request.onsuccess = () => {
			resolve();
		};

		request.onerror = () => {
			reject(request.error);
		};
	});
}

export async function clearDocuments(): Promise<void> {
	const db = await openDatabase();

	return new Promise((resolve, reject) => {
		const transaction = db.transaction(STORE_NAME, 'readwrite');
		const store = transaction.objectStore(STORE_NAME);

		const request = store.clear();

		request.onsuccess = () => {
			resolve();
		};

		request.onerror = () => {
			reject(request.error);
		};
	});
}
