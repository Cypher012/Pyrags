function redact(message: string): string {
	if (/failed query:|\b(select|insert into|update|delete from)\b/i.test(message)) {
		return 'Database query failed; inspect the nested cause below.';
	}
	return message
		.replace(/(?:https?|postgres(?:ql)?):\/\/[^\s]+/gi, '[redacted URL]')
		.replace(/"[^"\n]*"|'[^'\n]*'|\x60[^\x60\n]*\x60/g, '[redacted value]')
		.replace(
			/\b(?:secret|password|token|code|state|cookie|authorization)\s*[:=]\s*\S+/gi,
			'[redacted credential]'
		)
		.replace(/[\w.+-]+@[\w.-]+/g, '[redacted email]')
		.replace(/[a-zA-Z0-9_+/=-]{32,}/g, '[redacted token]')
		.slice(0, 1500);
}

function describeError(error: Error, depth = 0): Record<string, unknown> {
	const diagnostic: Record<string, unknown> = {
		name: redact(error.name),
		message: redact(error.message)
	};
	if ('code' in error && typeof error.code === 'string' && /^[A-Z0-9_]{1,40}$/.test(error.code)) {
		diagnostic.code = error.code;
	}
	if (error.cause instanceof Error && depth < 5) {
		diagnostic.cause = describeError(error.cause, depth + 1);
	}
	return diagnostic;
}

export const authLogger = {
	level: 'warn' as const,
	log(level: 'debug' | 'info' | 'warn' | 'error', message: string, ...args: unknown[]) {
		const entry = {
			source: 'better-auth',
			message: redact(message),
			errors: args
				.filter((argument): argument is Error => argument instanceof Error)
				.map((error) => describeError(error))
		};
		if (level === 'error') console.error(JSON.stringify(entry));
		else if (level === 'warn') console.warn(JSON.stringify(entry));
		else console.info(JSON.stringify(entry));
	}
};
