import axios from 'axios';
import { authClient } from './auth-client';
import { env } from '$env/dynamic/public';

export const api = axios.create({
	baseURL: env.PUBLIC_BASE_URL || 'http://localhost:8000',
	fetchOptions: { cache: 'no-store' }
});

api.interceptors.request.use(async (config) => {
	if (typeof window === 'undefined') {
		return config;
	}

	const { data, error } = await authClient.token();

	if (error || !data?.token) {
		throw new Error('Not authenticated');
	}

	config.headers.Authorization = `Bearer ${data.token}`;

	return config;
});
