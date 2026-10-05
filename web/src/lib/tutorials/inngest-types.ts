export type TutorialCode = {
	path: string;
	kind: 'Existing code' | 'Reference example' | 'Command' | 'Expected output';
	language: 'python' | 'typescript' | 'bash' | 'sql' | 'json' | 'text';
	code: string;
	note?: string;
};

export type TutorialLesson = {
	id: string;
	title: string;
	group: 'Understand' | 'Implement' | 'Run & ship';
	summary: string;
	concepts: string[];
	why: string;
	context: TutorialCode[];
	files: string[];
	tasks: string[];
	exercise?: TutorialCode[];
	hint?: { explanation: string; code?: TutorialCode };
	verify: string[];
	expected: string;
	references: { label: string; url: string }[];
	diagram?: 'architecture' | 'simulation';
	checkpoint?: { question: string; answer: string };
};
