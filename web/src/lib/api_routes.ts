import { env } from '$env/dynamic/public';

const API_ROUTES = {
	base_url: env.PUBLIC_BASE_URL,
	chat_query: `/chat/query`,
	upload_file: `/embeddings/upload-file`,
	upload_status(jobId: string) {
		return `${this.base_url}/embeddings/upload-status/${jobId}`;
	}
};

export default API_ROUTES;
