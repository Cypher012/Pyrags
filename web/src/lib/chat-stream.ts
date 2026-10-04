import type { SourceDocument } from '$lib/types/source-document';

export async function readChatStream(
	stream: ReadableStream<Uint8Array>,
	onUpdate: (content: string) => void,
	format: 'sse' | 'ndjson' = 'sse'
) {
	const reader = stream.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	let content = '';
	let sourceDocuments: SourceDocument[] = [];
	let eventData: string[] = [];
	let eventType = '';
	let finished = false;

	function appendToken(data: string) {
		if (format === 'sse' && data.trim() === '[DONE]') {
			finished = true;
			return;
		}
		let token = data;
		let chunk: unknown;
		if (format === 'ndjson') {
			chunk = JSON.parse(data);
		} else {
			try {
				chunk = JSON.parse(data);
			} catch {
				chunk = undefined;
			}
		}
		if (typeof chunk === 'object' && chunk !== null && 'source_documents' in chunk) {
			if (
				!Array.isArray(chunk.source_documents) ||
				chunk.source_documents.some(
					(source) =>
						typeof source?.content !== 'string' ||
						typeof source.metadata !== 'object' ||
						source.metadata === null
				)
			) {
				throw new Error('Invalid chat source documents');
			}
			sourceDocuments = chunk.source_documents as SourceDocument[];
		}
		if (
			typeof chunk === 'object' &&
			chunk !== null &&
			('response' in chunk || 'conversation_id' in chunk)
		) {
			if (
				!('response' in chunk) ||
				typeof chunk.response !== 'string' ||
				!('conversation_id' in chunk) ||
				typeof chunk.conversation_id !== 'string' ||
				!chunk.conversation_id ||
				!('source_documents' in chunk)
			) {
				throw new Error('Invalid chat stream completion');
			}
			content = chunk.response;
			onUpdate(content);
			finished = true;
			return;
		}
		if (
			typeof chunk === 'object' &&
			chunk !== null &&
			'source_documents' in chunk &&
			!('token' in chunk)
		) {
			return;
		}
		if (typeof chunk === 'object' && chunk !== null && 'token' in chunk) {
			if (typeof chunk.token !== 'string') throw new Error('Invalid chat stream token');
			token = chunk.token;
		} else if (format === 'ndjson') {
			throw new Error('Invalid chat stream token');
		}
		if (token) {
			content += token;
			onUpdate(content);
		}
	}

	function readLine(line: string) {
		if (format === 'ndjson') {
			if (line.trim()) appendToken(line);
			return;
		}
		if (line === '') {
			if (eventType === 'error') throw new Error('The server reported a chat stream error');
			if (eventData.length) appendToken(eventData.join('\n'));
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

	try {
		while (true) {
			const { value, done } = await reader.read();
			buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
			while (!finished) {
				const lineEnd = buffer.search(/[\r\n]/);
				if (lineEnd === -1) break;
				if (!done && buffer[lineEnd] === '\r' && lineEnd === buffer.length - 1) break;
				const separatorLength = buffer.slice(lineEnd, lineEnd + 2) === '\r\n' ? 2 : 1;
				readLine(buffer.slice(0, lineEnd));
				buffer = buffer.slice(lineEnd + separatorLength);
			}
			if (finished) {
				await reader.cancel().catch(() => {});
				break;
			}
			if (done) break;
		}
		if (format === 'ndjson' && !finished) readLine(buffer);
		if (!finished) throw new Error('Chat stream ended before completion');
		if (!content) throw new Error('No chat reply received');
		return { content, source_documents: sourceDocuments };
	} catch (error) {
		await reader.cancel().catch(() => {});
		throw error;
	} finally {
		reader.releaseLock();
	}
}
