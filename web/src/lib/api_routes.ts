import { env } from '$env/dynamic/public';

const BASE_URL = env.PUBLIC_BASE_URL || 'http://localhost:8000';

const API_ROUTES = {
	query_usage: '/chat/usage',
	upload_file: `/embeddings/upload-file`,
	upload_status(jobId: string) {
		return `${BASE_URL}/embeddings/upload-status/${jobId}`;
	},
	query_chatbot(conversationId: string) {
		return `/chat/conversations/${conversationId}/query`;
	},
	conversation(conversationId: string) {
		return `/chat/conversations/${conversationId}`;
	},
	conversation_list: `/chat/conversations`,
	conversation_messages(conversationId: string) {
		return `/chat/conversations/${conversationId}/messages`;
	}
};

export default API_ROUTES;
