import jobModelExample from './examples/ingestion_job.py?raw';
import retrievalExample from './examples/document_chunk_repository.py?raw';
import jobsExample from './examples/jobs.py?raw';
import clientExample from './examples/inngest_client.py?raw';
import receiptExample from './examples/receipt.py?raw';
import prepareWorkflowExample from './examples/prepare_workflow.py?raw';
import workflowExample from './examples/document_ingestion.py?raw';
import mainExample from './examples/main.py?raw';
import routerExample from './examples/router.py?raw';
import retryExample from './examples/retry_probe.py?raw';
import retryWorkflowExample from './examples/retry_test.py?raw';
import retrySetupExample from './examples/retry_setup.sql?raw';
import type { TutorialCode, TutorialLesson } from '$lib/tutorials/inngest-types';
import main from '../../../../../server/main.py?raw';
import router from '../../../../../server/app/embeddings/router.py?raw';
import processor from '../../../../../server/app/embeddings/processor.py?raw';
import service from '../../../../../server/app/embeddings/service.py?raw';
import document from '../../../../../server/app/model/document.py?raw';
import chunk from '../../../../../server/app/model/document_chunk.py?raw';
import database from '../../../../../server/app/core/database.py?raw';
import config from '../../../../../server/app/core/config.py?raw';
import progress from '../../../../../server/app/embeddings/schemas.py?raw';
import alembic from '../../../../../server/alembic/env.py?raw';
import retrieval from '../../../../../server/app/repository/document_chunk.py?raw';
import frontendProgress from '../../hooks/use-upload-progress.svelte.ts?raw';
import apiRoutes from '../../api_routes.ts?raw';

function existing(
	path: string,
	source: string,
	start?: string,
	end?: string,
	language: TutorialCode['language'] = 'python'
): TutorialCode {
	const startIndex = start ? source.indexOf(start) : 0;
	const endIndex = end ? source.indexOf(end, startIndex + 1) : source.length;
	if (startIndex < 0 || endIndex < 0) {
		return {
			path,
			kind: 'Existing code',
			language,
			code: source.trim(),
			note: 'The original excerpt has changed as you edit. Showing the current file instead; this lesson describes the starting architecture.'
		};
	}
	return { path, kind: 'Existing code', language, code: source.slice(startIndex, endIndex).trim() };
}


function command(path: string, code: string): TutorialCode {
	return { path, kind: 'Command', language: 'bash', code: code.trim() };
}

function reference(path: string, code: string, language: TutorialCode['language'] = 'python'): TutorialCode {
	return { path, kind: 'Reference example', language, code: code.trim() };
}

const docs = 'https://www.inngest.com/docs/';
const modelPath = 'server/app/model/ingestion_job.py';
const jobsPath = 'server/app/embeddings/jobs.py';
const workflowPath = 'server/app/workflows/document_ingestion.py';
const clientPath = 'server/app/core/inngest.py';

export const lessons: TutorialLesson[] = [
	{
		id: 'what-we-build',
		title: 'A durable document pipeline',
		group: 'Understand',
		summary: 'Keep Pyrags. Replace the fragile handoff, not your application.',
		concepts: [
			'Pyrags uploads PDF/DOCX files, splits extracted text, creates OpenAI embeddings, and uses PostgreSQL + pgvector for document-grounded chat. Better Auth has its own database in the SvelteKit application.',
			'Complete reference implementations are provided for you to apply and understand. This workbook only renders examples and remembers your learning progress; it does not install packages, execute snippets, run migrations, or call an AI provider.',
			'Our chosen durable input is extracted, page-preserving text in PostgreSQL. Extraction stays inside the upload request. After the transaction commits, a small event starts chunking and embedding. Original file bytes are not retained in this first version.'
		],
		why: 'A Python process restart currently loses pending uploads and their progress queues. A saved job plus an Inngest workflow can survive that restart.',
		context: [existing('server/app/model/document.py', document, 'class DocumentStatus', 'class DocumentCreate')],
		files: ['server/app/embeddings/router.py', modelPath, workflowPath],
		tasks: [
			'Read the diagram and identify which box holds your application data and which box schedules work.',
			'Use a disposable local database and a tiny, non-sensitive document while learning.',
			'Keep the current upload response and frontend navigation. Do not remove the old worker until the new path passes the verification lessons.'
		],
		verify: ['Explain the flow aloud: upload → extract → commit job → publish event → durable steps → READY.', 'Confirm you understand that the examples below are proposed changes, not already-installed backend code.'],
		expected: 'A working ingestion workflow you understand, using your existing ORM, API and UI. No Redis and no second toy project.',
		diagram: 'architecture',
		references: [{ label: 'Python SDK quick start', url: docs + 'durable-execution/quick-start/python-quick-start' }],
		checkpoint: { question: 'Can Inngest re-extract the original PDF after your API restarts in this design?', answer: 'No. The original bytes are not saved. It resumes from the extracted text stored in PostgreSQL. Durable extraction would require saving those bytes somewhere first.' }
	},
	{
		id: 'current-architecture',
		title: 'Trace the code you have',
		group: 'Understand',
		summary: 'Follow one upload from the Svelte composer to pgvector.',
		concepts: [
			'The frontend upload hook sends multipart data to /embeddings/upload-file using the authenticated API client. The API returns a job_id. useUploadProgress opens an authenticated fetch-based SSE stream, and file-upload.svelte navigates to the new conversation after completion.',
			'The router stores queues and owners in process-local dictionaries and starts asyncio.create_task. processor.py extracts pages, chunks each page (1,000 characters with 200 overlap), embeds everything, then creates the conversation, document and chunks in one final transaction.',
			'No document/job row exists during most processing. The catch-all exception writes an error to the queue instead of raising. Queues are removed on terminal delivery or roughly five minutes after the worker finishes. Neither jobs nor progress survive a process restart.'
		],
		why: 'Wrapping run_embeddings_job unchanged would preserve the memory dependency and swallow exceptions that Inngest needs to retry.',
		context: [
			existing('server/app/embeddings/router.py', router, 'job_queues:', 'class UploadResponse'),
			existing('server/app/embeddings/router.py', router, '    job_id = str(uuid4())', 'async def get_job_queue'),
			existing('web/src/lib/api_routes.ts', apiRoutes, undefined, undefined, 'typescript'),
			existing('server/app/embeddings/processor.py', processor, '    except Exception as exc:')
		],
		files: ['web/src/lib/hooks/use-file-upload.svelte.ts', 'web/src/lib/hooks/use-upload-progress.svelte.ts', 'web/src/routes/app/file-upload.svelte', 'server/app/embeddings/processor.py'],
		tasks: [
			'Open those four files in your editor and trace the job_id and conversation_id.',
			'Find create_conversation and create_document inside the final transaction. Notice how late persistence starts.',
			'Separate reusable text/embedding functions from the queue-specific orchestration. Keep the former.'
		],
		verify: ['Search the backend for job_queues, job_owners and asyncio.create_task.', 'Identify why a second FastAPI instance cannot read the first instance’s queue.'],
		expected: 'You can locate the upload entrypoint, pure transformations, paid embedding call, database writes and UI status consumer.',
		references: [{ label: 'How durable workflows run', url: docs + 'durable-execution/durable-workflows' }]
	},
	{
		id: 'why-inngest',
		title: 'Who runs the function?',
		group: 'Understand',
		summary: 'Inngest schedules work. Your FastAPI host executes Python.',
		concepts: [
			'An event is a named message, not the job itself. We will send pyrags/document.uploaded with only a job_id. A function subscribed to that name handles it.',
			'The Python SDK registers an HTTP endpoint on FastAPI. Inngest calls that endpoint to invoke your code and coordinate steps. It is not a separate Python worker process you must keep alive beside FastAPI.',
			'Each successful step has a recorded result in Inngest. On replay, the handler runs again, but recorded steps return their saved results instead of redoing their bodies. Side effects outside steps can repeat.'
		],
		why: 'The durable boundary is a completed step, not an arbitrary line of Python. You choose small, meaningful checkpoints.',
		context: [existing('server/main.py', main)],
		files: ['server/main.py', workflowPath],
		tasks: ['Use the simulation to advance through an upload.', 'At the embedding failure, predict which work runs again before selecting retry.', 'Distinguish the network arrows: API → Inngest publishes; Inngest → API executes.'],
		verify: ['Explain why Inngest Cloud still needs a reachable, running FastAPI deployment.', 'Explain why a successful chunk step is reused after an embedding failure.'],
		expected: 'A failed embedding attempt does not force successful chunk preparation to run again in the same workflow run.',
		diagram: 'simulation',
		references: [{ label: 'Serving functions', url: docs + 'durable-execution/deploying-functions/serve' }, { label: 'Durable execution', url: docs + 'durable-execution' }]
	},
	{
		id: 'postgres-not-redis',
		title: 'What is persisted where?',
		group: 'Understand',
		summary: 'PostgreSQL is your source of truth. Inngest keeps workflow history.',
		concepts: [
			'In production, pyrags_app stores conversations, documents, source text, prepared chunks, progress and final 1,024-dimensional vectors. pyrags_auth remains the frontend’s Better Auth database. Your local Compose databases are both named pyrags, on separate ports: API 5433, auth 5432. The job table belongs to the API database, not to Drizzle auth migrations.',
			'Inngest stores accepted events, run/step history and serialized step results. Keep those results small: identifiers and counts, not extracted PDFs, SQLModel objects or giant vector arrays.',
			'Request bytes and temporary embedding arrays can live briefly in Python memory. They are not recovery inputs. Redis is unnecessary here because PostgreSQL already stores business state and Inngest coordinates execution. PostgreSQL is not secretly replacing the Inngest scheduler.'
		],
		why: 'A durable event pointing to missing or memory-only input cannot recover. Commit the actual recovery input before publishing.',
		context: [existing('server/app/core/database.py', database, 'engine =', 'SessionDep'), existing('server/app/model/document_chunk.py', chunk, 'class DocumentChunk')],
		files: [modelPath],
		tasks: ['Write down the lifetime of original bytes, extracted text, vectors and event data.', 'Keep page numbers when serializing source_parts. DOCX has no reliable per-paragraph page mapping in the current extractor.'],
		verify: ['Would restarting FastAPI erase source text after your planned commit? It should not.', 'Would clearing localStorage erase a backend job? It must not.'],
		expected: 'PostgreSQL owns the job’s recoverable input and public state; Inngest owns scheduling and step history; localStorage only owns workbook progress.',
		references: [{ label: 'Step results and limits', url: docs + 'durable-execution/limits' }, { label: 'pgvector', url: 'https://github.com/pgvector/pgvector' }],
		checkpoint: { question: 'Why not send every extracted page and every vector in the event?', answer: 'That copies sensitive, potentially large data into the orchestration service. A job ID lets steps load the authoritative data from PostgreSQL, and keeps event and step payloads bounded.' }
	},
	{
		id: 'install-configure',
		title: 'Install and configure',
		group: 'Implement',
		summary: 'Add one Python dependency, not a new queue stack.',
		concepts: [
			'Use uv in server/, where your FastAPI dependencies already live. The workbook does not run this command for you. Keep uv.lock updated when you install.',
			'Your Settings loads server/.env and ignores unknown fields. That does not export INNGEST_* values into os.environ. Add explicit fields and pass them to the SDK client; also launch the local API with INNGEST_DEV=1.',
			'Local development needs no cloud event/signing keys. Production needs two different secrets: an event key for sending messages and a signing key to validate Inngest’s callbacks.'
		],
		why: 'Explicit configuration prevents the build/runtime environment confusion you hit when deploying the frontend.',
		context: [existing('server/app/core/config.py', config, 'class Settings', '    @model_validator')],
		files: ['server/pyproject.toml', 'server/uv.lock', 'server/app/core/config.py', 'server/.env'],
		tasks: ['Run uv add inngest from server/.', 'Add the two Settings fields below. Keep APP_ENV, selected database URL and existing SSL handling unchanged.', 'Do not put real keys in snippets, git, the Svelte app or public environment variables.'],
		exercise: [
			command('Terminal · repository root', 'cd server\nuv add inngest\nuv run python -c "import inngest; print(\'Inngest SDK installed\')"'),
			reference('server/app/core/config.py · inside Settings; keep existing Self/model_validator imports', `INNGEST_EVENT_KEY: str = ""
INNGEST_SIGNING_KEY: str = ""

@model_validator(mode="after")
def validate_inngest_keys(self) -> Self:
    if self.APP_ENV == "production":
        if not self.INNGEST_EVENT_KEY.strip():
            raise ValueError("INNGEST_EVENT_KEY is required in production")
        if not self.INNGEST_SIGNING_KEY.strip():
            raise ValueError("INNGEST_SIGNING_KEY is required in production")
    return self`),
			reference('server/.env · local values only', 'APP_ENV=development\nENABLE_MOCK_API=false\n# Keep your existing LOCAL_DATABASE_URL and OPENAI_API_KEY.\n# INNGEST_DEV=1 will be set on the launch command.', 'bash')
		],
		verify: ['The import check succeeds without starting a workflow.', 'uv.lock includes inngest. Your .env remains untracked.', 'Do not install Redis or change the existing database engine.'],
		expected: 'The SDK is available in the same uv environment as FastAPI. Existing development still works.',
		references: [{ label: 'Python SDK', url: docs + 'reference/python' }, { label: 'SDK environment variables', url: docs + 'reference/python/overview/env-vars' }]
	},
	{
		id: 'create-client',
		title: 'Create your Inngest client',
		group: 'Implement',
		summary: 'One stable application identity, explicit keys and mode.',
		concepts: [
			'Create a small core module alongside database.py. The client publishes events and provides the function decorator. It is not a database connection.',
			'Use a stable app_id, pyrags-app. APP_ENV selects production mode in this project. INNGEST_DEV=1 on the local process makes local routing explicit.',
			'Passing config values directly avoids relying on the SDK to discover variables that Pydantic only read into its Settings object.'
		],
		why: 'Keeping the client in one module avoids imports from main.py and circular references when the router and workflows both need it.',
		context: [existing('server/app/core/config.py', config, '    model_config')],
		files: [clientPath],
		tasks: ['Create app/core/inngest.py and import the SDK and existing config.', 'Use the complete client below; keep its name consistent across imports.', 'Pass empty local keys as None; pass your real secret values only from Settings.'],
		hint: { explanation: 'The app ID is not a hostname. It identifies this backend’s functions across deploys.', code: reference(clientPath + ' · constructor fields', 'app_id="pyrags-app",\nis_production=config.APP_ENV == "production",') },
		verify: ['From server/, run the import command below with your existing local .env.', 'Never print the client’s keys or your entire Settings object.'],
		exercise: [
			reference(clientPath, clientExample),
			command('Terminal · server/', 'INNGEST_DEV=1 uv run python -c "from app.core.inngest import inngest_client; print(\'Client import OK\')"')
		],
		expected: 'Client import OK, with no cloud API request and no secret output.',
		references: [{ label: 'Client constructor', url: docs + 'reference/python/client/overview' }]
	},
	{
		id: 'create-function',
		title: 'Register a first function',
		group: 'Implement',
		summary: 'Prove the event-to-function connection before adding paid work.',
		concepts: [
			'Start with a harmless receipt function in app/workflows/document_ingestion.py. Later you will replace its body with durable ingestion steps.',
			'The trigger’s event name must exactly match the publisher. fn_id identifies this function and should remain stable. A job_id is your database key; a run ID is Inngest’s execution identity.',
			'This first body intentionally performs no embedding, chunking or database write. Returning a small JSON-compatible value makes registration easy to test.'
		],
		why: 'Debug wiring separately from file extraction and AI billing. Small milestones are easier to reason about.',
		context: [existing('server/app/embeddings/router.py', router, 'class UploadResponse', '@router.post')],
		files: ['server/app/workflows/__init__.py', workflowPath],
		tasks: ['Create the workflows package with an empty __init__.py.', 'Choose fn_id="process-document" and the event name used throughout this workbook.', 'Validate/read the event’s job_id and return it as a string. Do not call the existing run_embeddings_job.'],
		exercise: [reference(workflowPath, receiptExample)],
		hint: { explanation: 'This receipt validates the input type before UUID parsing; the full ingestion workflow comes later.', code: reference(workflowPath + ' · event parsing', receiptExample) },
		verify: ['Import process_document successfully using the complete decorator below.', 'Keep a malformed UUID out of your normal test event. No payment/provider call should happen.'],
		expected: 'One registered function with an event trigger and a small receipt result. You will run it in the local-development lesson.',
		references: [{ label: 'Python function configuration', url: docs + 'reference/python/functions/create' }]
	},
	{
		id: 'serve-fastapi',
		title: 'Connect it to FastAPI',
		group: 'Implement',
		summary: 'Register /api/inngest on the app you already have.',
		concepts: [
			'Import inngest.fast_api, your client and your function in server/main.py. After app creation, call serve with the existing app and the function list.',
			'The SDK handles registration and execution requests at /api/inngest. Your user-facing upload and status endpoints keep CurrentUserDep. Inngest callbacks use SDK signing verification, not a browser Better Auth token.',
			'Do not create a second FastAPI app, attach the SDK endpoint to the upload router’s JWT dependencies, or manually replace the SDK’s security implementation.'
		],
		why: 'Inngest must be able to invoke the function without impersonating one of your frontend users.',
		context: [existing('server/main.py', main)],
		files: ['server/main.py'],
		tasks: ['Add the three imports without removing CORS or app.include_router(router).', 'Register process_document in the serve list as shown below.', 'Use the local API and Dev Server commands in lesson 14 to verify discovery.'],
		exercise: [reference('server/main.py', mainExample)],
		verify: ['Start FastAPI with INNGEST_DEV=1 and GET http://127.0.0.1:8000/api/inngest.', 'Confirm the Dev Server can see process-document, not just an empty function list.'],
		expected: 'The SDK endpoint exists on port 8000. The Inngest dashboard is a different server on port 8288.',
		references: [{ label: 'FastAPI integration example', url: docs + 'durable-execution/quick-start/python-quick-start' }]
	},
	{
		id: 'persist-publish',
		title: 'Commit before you publish',
		group: 'Implement',
		summary: 'Give the event a real, recoverable input to point to.',
		concepts: [
			'Before replacing create_task, add an IngestionJob SQLModel table in pyrags_app. Use UUID id, document_id foreign key, user_id, source_parts JSONB, prepared_chunks JSONB defaulting to an empty list, stage/message/progress, and Timestamp. The document relationship provides conversation_id; do not trust it from the event.',
			'Persist source_parts as [{"page_number": 1, "text": "..."}]. Retain blank PDF pages and their one-based numbers. DOCX page_number is null; reuse extract_docx_page_count for optional document metadata, not as invented text-page mappings.',
			'Create a jobs.py service helper named save_upload_job. It takes bytes, filename and authenticated user_id; extracts using asyncio.to_thread, rejects empty text, then commits conversation + PROCESSING document + job in one transaction. Return a UUID job_id, not a live ORM object. The complete service below includes helpers explained in subsequent lessons.',
			'Only after that helper commits, await send. For this initial version, a failed publish should return 503 and log the saved job ID for operator recovery. The committed job is still recoverable; do not pretend PostgreSQL and Inngest share an atomic transaction. A crash between commit and send remains possible; lesson 17 addresses it.'
		],
		why: 'Publishing first risks a worker querying a row that does not exist yet. Keeping bytes in create_task risks losing the only input.',
		context: [
			existing('server/app/embeddings/processor.py', processor, 'FileType =', 'def split_text_into_chunks'),
			existing('server/alembic/env.py', alembic, 'from app.model.conversation', 'config = context.config')
		],
		files: [modelPath, jobsPath, 'server/alembic/env.py', 'server/app/embeddings/router.py'],
		tasks: [
			'Create the table using SQLModel Field + SQLAlchemy Column(JSONB). Choose table name ingestion_jobs. Keep stage compatible with JobProgress, clamp progress 0–100, and update updated_at whenever state changes.',
			'Import IngestionJob in alembic/env.py so autogenerate sees it. Generate, read and apply the migration against your LOCAL pyrags_app database only.',
			'Implement save_upload_job; reuse create_conversation, create_document and the current extraction/page-count functions. Preserve file validation and CurrentUserDep in upload_file.',
			'Replace only the queue/create_task handoff with the publisher below after the persistence helper works. Keep UploadResponse(job_id=str(job_id), filename=filename). The complete router includes database-backed status; lesson 13 explains that part.'
		],
		exercise: [
			reference(modelPath, jobModelExample),
			reference(jobsPath, jobsExample),
			reference('server/app/embeddings/router.py', routerExample),
			reference('server/alembic/env.py · add alongside existing model imports', 'from app.model.ingestion_job import IngestionJob'),
			command('Terminal · server/ · local database only', 'APP_ENV=development uv run alembic revision --autogenerate -m "add ingestion jobs"\n# Read the generated migration before applying it.\nAPP_ENV=development uv run alembic upgrade head')
		],
		hint: { explanation: 'JSONB needs explicit serialization. For PreparedChunk later, use model_dump(mode="json"). For extraction now, transform each (page_number, text) tuple into an object. Use default_factory=list, not a mutable shared list.' },
		verify: ['Send a tiny real upload using the signed-in UI. At this stage, test the POST in browser Network; the new router serves persisted status; the receipt-only workflow stays PROCESSING.', 'Confirm a PROCESSING document and ingestion_jobs row with source_parts exist before the receipt function runs.', 'Stop the Dev Server and try publishing: the API must not report a successfully dispatched workflow. Find the saved job for manual recovery.'],
		expected: 'The event contains a database job ID, not raw file data. A receipt run is not READY yet. The router includes persisted status, explained in lesson 13.',
		references: [{ label: 'Python send events', url: docs + 'reference/python/client/send' }, { label: 'Alembic autogenerate', url: 'https://alembic.sqlalchemy.org/en/latest/autogenerate.html' }]
	},
	{
		id: 'durable-steps',
		title: 'Create a durable checkpoint',
		group: 'Implement',
		summary: 'Use step.run with a callable and a small result.',
		concepts: [
			'Define prepare_chunks(job_id: str) in jobs.py. Load job + document in a fresh session, reconstruct SourcePart tuples, call chunk_document off the event loop, and persist PreparedChunk dictionaries in job.prepared_chunks. Return {"chunk_count": N, "batch_count": ceil(N / 32)}.',
			'Make preparation idempotent: return the saved manifest if already prepared; reject missing/failed jobs and textless results. Keep prepared_chunks immutable once embedding starts. Do not insert DocumentChunk yet: its embedding column cannot be null.',
			'await ctx.step.run("prepare-chunks", prepare_chunks, str(job_id)) passes the function and its argument. Calling prepare_chunks(job_id) first is the wrong shape. Keep the same step ID on replay and return JSON-safe primitives.'
		],
		why: 'The checkpoint records a tiny manifest in Inngest while the bulk chunk text remains in PostgreSQL.',
		context: [existing('server/app/embeddings/processor.py', processor, 'def split_text_into_chunks', 'async def run_embeddings_job')],
		files: [jobsPath, workflowPath],
		tasks: ['Implement prepare_chunks using the existing chunk_document. Serialize with model_dump(mode="json"), and reconstruct with PreparedChunk.model_validate when loading later.', 'Ensure session/transaction lifetimes are bounded. Never share a request session across workflow callbacks.', 'Replace the receipt body with one step and its manifest result. Imports of your helpers come from app.embeddings.jobs.'],
		exercise: [reference(workflowPath, prepareWorkflowExample)],
		hint: { explanation: 'A complete single-step call makes the API shape easier to see.', code: reference(workflowPath + ' · single step', 'manifest = await ctx.step.run("prepare-chunks", prepare_chunks, str(job_id))\nreturn manifest') },
		verify: ['Send an event for a saved job and inspect prepare-chunks in the dashboard.', 'The step result contains only counts; job.prepared_chunks contains content and metadata.', 'Run preparation a second time and compare stored chunk indexes. They should not change.'],
		expected: 'One completed checkpoint, a deterministic chunk manifest, and no embedding bill yet.',
		references: [{ label: 'Python step.run', url: docs + 'reference/python/steps/run' }, { label: 'Step design', url: docs + 'durable-execution/primitives' }]
	},
	{
		id: 'retries-failure',
		title: 'Retry work, not side effects',
		group: 'Implement',
		summary: 'A transient error is not a permanently failed document.',
		concepts: [
			'Let step errors propagate. The current processor’s catch-and-queue block would turn failures into successful function returns, so do not reuse that orchestration. Keep documents PROCESSING during transient retries.',
			'Use an async on_failure handler when retries are exhausted. Its context contains a failure system event, whose data.event is the original triggering event. Read job_id from that nested event, not directly from the failure event.',
			'Create mark_failed(job_id: str) in jobs.py: in a short transaction, update the job to stage error with a safe public message and DocumentStatus.FAILED. Never downgrade an already READY/completed document. Log diagnostic details privately. Make the handler’s update safe to repeat.'
		],
		why: 'A successful database write and an Inngest checkpoint acknowledgement are separate operations. A handler may run again after the write, so database changes must tolerate replay.',
		context: [existing('server/app/embeddings/processor.py', processor, '    except Exception as exc:'), existing('server/app/model/document.py', document, 'class DocumentStatus', 'class DocumentBase')],
		files: [workflowPath, jobsPath],
		tasks: ['Implement mark_failed and define ingestion_failed before the decorator references it.', 'Add on_failure=ingestion_failed to process_document’s existing decorator. Keep retries=4 for this exercise.', 'Use the local failure injection exercise in lesson 15. Do not mark FAILED on the first retryable embedding error.'],
		exercise: [reference(workflowPath, workflowExample)],
		hint: { explanation: 'The async failure callback uses the same step API. It is a separate recovery function, so it can also fail; monitor it.', code: reference(workflowPath + ' · final state update', 'await ctx.step.run("mark-failed", mark_failed, job_id)') },
		verify: ['Force one transient error: document stays PROCESSING while the step retries.', 'Force every attempt to fail: after retry exhaustion, the failure handler records FAILED/error.', 'Call mark_failed for a completed job and confirm it remains READY.'],
		expected: 'Retries are visible in Inngest; only final failure becomes a terminal error in your application.',
		references: [{ label: 'Failure handlers', url: docs + 'durable-execution/guides-and-advanced/error-handling/failure-handlers' }, { label: 'Failure event payload', url: docs + 'reference/system-events/inngest-function-failed' }]
	},
	{
		id: 'pipeline-batches',
		title: 'Connect your embedding pipeline',
		group: 'Implement',
		summary: 'Reuse the real 1,024-dimensional embedding service in bounded batches.',
		concepts: [
			'Implement embed_and_store_batch(job_id: str, batch_index: int) and finish_job(job_id: str) in jobs.py. Batch size 32 is a starting choice, not a provider or platform limit. Use stable IDs embed-store-0, embed-store-1, and so on.',
			'For each batch, load its PreparedChunks from the immutable manifest, release the read session, call the existing synchronous generate_embeddings via asyncio.to_thread, then save vectors in a short transaction. Return only {"stored": N}. Validate vector lengths against VECTOR(1024).',
			'Use PostgreSQL ON CONFLICT on (document_id, chunk_index). Check whether the entire expected batch is already stored before making a paid call; that covers a commit followed by a lost checkpoint acknowledgement. Do not hold database locks while waiting for OpenAI.',
			'Keep only one active ingestion run per job: stable event IDs help within Inngest’s 24-hour dedup window, but are not a permanent database invariant. Duplicate executions must still use conditional terminal-state guards and idempotent writes. Concurrent manual replay can duplicate provider charges; avoid it in the MVP.',
			'finish_job verifies every expected chunk exists before atomically writing READY and completed/100 with the conversation ID. It must not claim success from the loop count alone. A crash before a vector commit can still repeat a paid call; we do not promise exactly-once AI billing.',
			'Moving conversation creation earlier makes it appear in Recents before ingestion finishes. search_document_chunks currently filters only by conversation, not READY status. Add a readiness guard before reserve_query in chat/router.py, and restrict retrieval to READY documents so incomplete/failed batches cannot ground a chat answer.'
		],
		why: 'Returning an entire embedding array as a step result couples large application data to workflow payload limits. Embedding and saving a batch inside one step keeps those arrays temporary.',
		context: [existing('server/app/embeddings/service.py', service, 'def get_embedding_model', 'def generate_query_embedding'), existing('server/app/embeddings/service.py', service, 'def generate_embeddings'), existing('server/app/model/document_chunk.py', chunk, '    __table_args__', '    id: UUID'), existing('server/app/repository/document_chunk.py', retrieval, '    stmt =', '    result =')],
		files: [jobsPath, workflowPath, 'server/app/repository/document_chunk.py', 'server/app/chat/router.py'],
		tasks: ['Implement the two helpers with fresh sessions and clear contracts above. Reuse get_embedding_model/generate_embeddings unchanged.', 'Use sqlalchemy.dialects.postgresql.insert(DocumentChunk).on_conflict_do_update or do_nothing deliberately. Include id/document_id/content/page/index/vector values and the existing unique constraint.', 'Add sequential batch steps after prepare-chunks and a finish step last. Preserve the decorator and failure handler.', 'Add Document.status == DocumentStatus.READY to retrieval. In query_chatbot, after ownership validation and before reserve_query, reject conversations with no ready document (for example HTTP 409). This prevents partial answers and consuming a query allowance while ingestion is unfinished.'],
		exercise: [reference(workflowPath, workflowExample), reference(jobsPath, jobsExample), reference('server/app/repository/document_chunk.py', retrievalExample), reference('server/app/chat/router.py · import and call inside query_chatbot after ownership validation, before reserve_query', 'from app.embeddings.jobs import require_ready_document\n\nawait require_ready_document(session, conversation_id)')],
		hint: { explanation: 'An async wrapper keeps the existing synchronous embedding service off the API event loop. batch must already be loaded and validated.', code: reference(jobsPath + ' · inside embed_and_store_batch', jobsExample) },
		verify: ['With a tiny real file and your own OPENAI_API_KEY, inspect the batch steps. This test makes a paid provider call.', 'Check pgvector dimensions, stored page numbers and uniqueness. Retry a batch after commit and confirm no additional rows appear.', 'The final document becomes READY only when the expected count matches. Verify existing chat retrieval can use it.', 'Open the early conversation while processing: querying must be rejected before reserving daily usage. FAILED documents must not contribute partial chunks.'],
		expected: 'Your existing embedding model and HNSW index remain compatible. The final database rows are the same shape as before.',
		references: [{ label: 'SQLAlchemy PostgreSQL upsert', url: 'https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert' }, { label: 'pgvector indexes and dimensions', url: 'https://github.com/pgvector/pgvector' }]
	},
	{
		id: 'postgres-status',
		title: 'Keep the UI contract',
		group: 'Implement',
		summary: 'Read durable status instead of consuming an in-memory queue.',
		concepts: [
			'Implement read_job_progress(job_id, user_id) in jobs.py. Query by both identifiers, return 404 for missing/other-owner jobs, and construct JobProgress from the saved state and linked conversation. Do not send source text, prepared chunks or vectors to the browser.',
			'Replace get_job_queue and upload_status with a database-backed SSE generator. Resolve an owner-scoped lookup dependency before streaming starts so missing/unauthorized jobs return HTTP 404, not an error after 200 headers have been sent. Each poll then uses a fresh session, yields changed snapshots, and exits on terminal state or disconnect.',
			'Job progress is a snapshot, not a full event history. Reconnecting gets the current state, including a terminal state. Do not delete the job on delivery. The frontend already knows how to render these fields, but its current stream reader treats interruption as an error rather than reconnecting.',
			'Add bounded reconnect/backoff to useUploadProgress as a separate learner task. A broken connection is not a FAILED document. Refresh the auth token on reconnect and stop retries on abort, unauthenticated responses or terminal state.'
		],
		why: 'Multiple browser tabs and multiple FastAPI instances can all read a PostgreSQL snapshot; none should consume another tab’s only update.',
		context: [
			existing('server/app/embeddings/schemas.py', progress),
			existing('server/app/embeddings/router.py', router, '@router.get("/upload-status'),
			existing('web/src/lib/hooks/use-upload-progress.svelte.ts', frontendProgress, '\tfunction handleEvent', '\tfunction fail', 'typescript')
		],
		files: [jobsPath, 'server/app/embeddings/router.py', 'web/src/lib/hooks/use-upload-progress.svelte.ts'],
		tasks: ['Write persisted progress during preparation, each stored batch, completion and final failure. Progress should not move backwards on a retry.', 'Replace the queue dependency with the owner-scoped lookup below and retain CurrentUserDep. Use Request.is_disconnected and per-poll sessions; do not keep a transaction open during the sleep.', 'Remove job_queues/job_owners/process_job/discard_job and the unused worker import only after this replacement works.', 'Ensure the frontend still receives conversation_id on completed, because it navigates to /app/chat/{id}.'],
		exercise: [reference('server/app/embeddings/router.py', routerExample)],
		verify: ['Upload from the existing UI: progress updates and completion navigates to the correct conversation.', 'Reconnect to a completed job and receive completed/100 immediately.', 'Two tabs observe the same job. Another user gets 404. Restart FastAPI and reopen the stream without losing ownership.'],
		expected: 'The UI looks familiar, but its status now reflects database state across process restarts.',
		references: [{ label: 'FastAPI SSE', url: 'https://fastapi.tiangolo.com/tutorial/server-sent-events/' }]
	},
	{
		id: 'local-development',
		title: 'Run the whole loop locally',
		group: 'Run & ship',
		summary: 'Three terminals: API, Inngest Dev Server, SvelteKit.',
		concepts: [
			'Start your existing local PostgreSQL databases first and use APP_ENV=development. Keep your working .env files: the API needs LOCAL_DATABASE_URL (normally port 5433), FRONTEND_URL and OPENAI_API_KEY for real embeddings; web needs its selected LOCAL_DATABASE_URL (normally port 5432), ORIGIN, BETTER_AUTH_SECRET, OAuth credentials and PUBLIC_BASE_URL. Real uploads require signing in.',
			'The API endpoint is http://127.0.0.1:8000/api/inngest. The Dev Server dashboard is http://127.0.0.1:8288. The CLI connects to the API, not to the Svelte route.',
			'Use npx for the Inngest CLI even though your frontend uses Bun: the official local-development guide recommends npm/npx for the CLI binary’s installation scripts. This does not add a frontend dependency. Python commands still use uv.',
			'First send a receipt test before adding database steps. After lesson 9, use a real saved job UUID from an authenticated upload; the illustrative UUID below is not an existing database row.'
		],
		why: 'The Dev Server reproduces the event/step HTTP loop without cloud keys. A visible registration is your first debugging checkpoint.',
		context: [existing('web/src/lib/api_routes.ts', apiRoutes, undefined, undefined, 'typescript')],
		files: ['server/.env', 'web/.env', 'server/main.py'],
		tasks: ['Install the SDK first (lesson 5). Start the API and CLI in separate terminals.', 'Open the dashboard, confirm the app/functions are synced, and inspect an event’s run.', 'Send the test event below during the receipt-only stage, or replace its job_id with a saved job UUID for the full pipeline.', 'For an actual upload, enable the real API (ENABLE_MOCK_API=false), sign into SvelteKit, and upload a small PDF/DOCX.'],
		exercise: [
			command('Setup terminal · repository root · existing Compose services', '(cd server && docker compose up -d api-db)\n(cd web && docker compose up -d db)\n# Use existing local env credentials; do not overwrite either .env.'),
			command('Terminal 1 · server/', 'APP_ENV=development INNGEST_DEV=1 uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000'),
			command('Terminal 2 · repository root', 'npx --ignore-scripts=false --allow-scripts=inngest-cli inngest-cli@latest dev --no-discovery -u http://127.0.0.1:8000/api/inngest'),
			command('Terminal 3 · web/', 'bun run dev'),
			command('Terminal · inspect SDK endpoint', 'curl -i http://127.0.0.1:8000/api/inngest'),
			command('Terminal · receipt test or replace job_id with a saved job', `curl -X POST http://127.0.0.1:8288/e/local-test \\
  -H 'Content-Type: application/json' \\
  -d '{"name":"pyrags/document.uploaded","data":{"job_id":"00000000-0000-4000-8000-000000000001"}}'`)
		],
		verify: ['http://127.0.0.1:8288 shows your app and process-document function.', 'The receipt test returns a job ID without an AI call. The real workflow shows prepare-chunks, batch steps and finish-document.', 'If functions are missing, check the serve list, endpoint URL, API logs and INNGEST_DEV on the API process before debugging embeddings.'],
		expected: 'You can see registration → event → run → individual steps in the local dashboard, and the app reflects the saved state.',
		references: [{ label: 'Local development (CLI installation notes)', url: docs + 'local-development' }, { label: 'Inngest CLI', url: docs + 'cli' }]
	},
	{
		id: 'test-workflow',
		title: 'Break it deliberately',
		group: 'Run & ship',
		summary: 'Test restart, replay, ownership and final failure—not just the happy path.',
		concepts: [
			'The local retry example fails once before calling the real embedding helper. Subsequent attempts can incur OpenAI charges; use a tiny document. No testing framework is currently configured in this repository; these are manual exercises, not a new test stack.',
			'Inject a one-time failure using saved database state, not a Python global or an environment flag that always fails. Persist the injection marker before raising, outside the transaction that will roll back on the exception.',
			'A checkpoint acknowledged by Inngest is reused within the same run. A new run has new step history, so your database idempotency guards matter. Event ID deduplication does not last forever.'
		],
		why: 'A background job is only useful if recovery works when the API, network or provider misbehaves.',
		context: [existing('server/app/model/document_chunk.py', chunk, '    __table_args__', '    id: UUID')],
		files: [jobsPath, workflowPath],
		tasks: [
			'Create the local test files below, register test_document_retry alongside process_document in main.py, seed a saved job with the SQL, and send pyrags/document.retry-test with its job_id. Stop normal ingestion during this isolated test.',
			'Restart FastAPI between successful chunking and embedding. Keep the Dev Server running and resume the same run.',
			'Inject an error after a vector commit but before the step returns. Confirm the already-stored batch check avoids duplicate rows and another embedding call.',
			'Force persistent failure until on_failure runs. Verify FAILED/error and safe UI messaging.',
			'Try a textless/corrupt document, a missing job ID, another user’s status URL and two observers. Remove all injection code before shipping.'
		],
		exercise: [
			reference('SQL console · local API database · after ingestion', `SELECT document_id, chunk_index, count(*)
FROM document_chunks
GROUP BY document_id, chunk_index
HAVING count(*) > 1;

SELECT id, status, page_count, size_bytes FROM documents;
SELECT id, stage, progress, updated_at FROM ingestion_jobs;`, 'sql'),
			reference('server/app/workflows/retry_probe.py · local test helper', retryExample), reference('server/app/workflows/retry_test.py · local test function', retryWorkflowExample), reference('SQL console · local API database only', retrySetupExample, 'sql')
		],
		verify: ['The duplicate query returns zero rows.', 'The same run reuses its successful checkpoints. A separate run reuses database work through your guards.', 'A terminal job has coherent document status, job stage and conversation ID. No test branch remains in production code.'],
		expected: 'You have evidence for recovery, not just a green happy-path run.',
		references: [{ label: 'Retries and error handling', url: docs + 'durable-execution/guides-and-advanced/error-handling' }, { label: 'Event idempotency', url: docs + 'durable-execution/guides-and-advanced/idempotency' }]
	},
	{
		id: 'production',
		title: 'Configure production safely',
		group: 'Run & ship',
		summary: 'Cloudflare hosts SvelteKit. Your Python host serves Inngest callbacks.',
		concepts: [
			'On the FastAPI host, set APP_ENV=production, the pyrags_app NEON_DATABASE_URL, FRONTEND_URL=https://pyrags.cipher-dev.cv, OPENAI_API_KEY, INNGEST_EVENT_KEY and INNGEST_SIGNING_KEY. Keep ENABLE_MOCK_API=false. Do not set INNGEST_DEV in production.',
			'Deploy Python with the client, registered functions and migrated ingestion_jobs table. Register/sync its public HTTPS /api/inngest endpoint in Inngest Cloud. Set the signing key on the API host so callbacks are authenticated. Event and signing keys are not interchangeable.',
			'The SvelteKit Worker retains its existing Better Auth/pyrags_auth configuration. Point its BASE_URL/PUBLIC_BASE_URL at your real HTTPS API URL. Keep provider and Inngest secrets out of public variables and the browser.',
			'Inngest does not remove host request/time limits. Extraction still happens during upload, and each embedding batch still runs on your Python host. Verify CPU, memory, upload and request-duration limits for the actual deployment. Reduce batch sizes if needed.',
			'Source text in PostgreSQL can be sensitive. Enforce ownership, retention and deletion policies. Cascade job deletion with document deletion, restrict operator access, and monitor stalled dispatches, exhausted runs and failure-handler errors.'
		],
		why: 'Durability needs both persisted data and reachable execution infrastructure. A successfully deployed frontend alone cannot process documents.',
		context: [existing('server/app/core/database.py', database, 'engine =', 'SessionDep')],
		files: ['server/app/core/config.py', 'server/main.py', 'web/.env · deployment settings only'],
		tasks: ['Set runtime secrets on the Python host, not in the tutorial code.', 'Validate selected production credentials and SDK mode at startup without printing secrets.', 'Run Alembic on pyrags_app after reviewing the migration on a development database. Do not run this model through Drizzle.', 'Sync the HTTPS SDK endpoint and test one authorized small upload end-to-end before enabling normal traffic.'],
		exercise: [reference('FastAPI host · variable names, not secret values', 'APP_ENV\nNEON_DATABASE_URL\nFRONTEND_URL\nOPENAI_API_KEY\nINNGEST_EVENT_KEY\nINNGEST_SIGNING_KEY\nENABLE_MOCK_API', 'text')],
		verify: ['The cloud dashboard discovers the correct functions and signed calls succeed.', 'The browser talks to HTTPS URLs, not localhost, and unauthorized status reads return 404.', 'One completed upload survives a FastAPI restart and can be queried with citations.'],
		expected: 'A production API connected to Inngest Cloud and Neon, with the existing Cloudflare frontend unchanged apart from API configuration.',
		references: [{ label: 'Python production mode', url: docs + 'reference/python/overview/prod-mode' }, { label: 'Deployment and serving', url: docs + 'durable-execution/deploying-functions/serve' }]
	},
	{
		id: 'final-architecture',
		title: 'Close the delivery gap',
		group: 'Run & ship',
		summary: 'Finish the MVP, then learn the transactional outbox.',
		concepts: [
			'The initial pipeline commits a recoverable job and then sends an event. If the API dies between those operations, a job may be saved but never dispatched. Manual republishing by job ID is recovery, not an automatic durability guarantee.',
			'Production hardening: insert an outbox row in the same transaction as the job. A separate scheduled dispatcher claims pending rows with short PostgreSQL transactions, publishes outside the lock, then marks them sent. An expiring lease makes abandoned claims available again.',
			'FOR UPDATE SKIP LOCKED helps multiple dispatchers claim different rows. It is not required for normal ingestion steps and does not by itself deliver anything. Run the dispatcher independently (for example, your host’s scheduled endpoint or a dedicated scheduled function), so recovery does not depend on the very event that was never sent.',
			'Publishing can succeed while marking the outbox sent fails. Re-send with a stable event ID; enforce database idempotency too. A robust outbox delivers at least once, not a magical exactly-once cross-service transaction.',
			'Your final boundary: FastAPI validates/extracts and persists; PostgreSQL stores recovery input, progress and vectors; Inngest coordinates retries and checkpoints; SvelteKit observes and navigates. No Redis is required for this design.'
		],
		why: 'Durable workflow execution begins after event acceptance. A transactional outbox makes the earlier delivery intent durable too.',
		context: [existing('server/app/embeddings/schemas.py', progress)],
		files: ['Optional: server/app/model/outbox_event.py', 'Optional: server/app/workflows/dispatch_outbox.py'],
		tasks: ['First confirm all MVP verification exercises pass. Do not add an outbox just to avoid understanding the basic send flow.', 'For hardening, design outbox id, job_id, event name/data, state, available_at, lease expiry, attempts and sent_at.', 'Implement the claim/publish/ack pattern with a scheduled independent dispatcher. Never hold a PostgreSQL row lock across HTTP send.', 'Transfer exercise: design another workflow (for example, refreshing a document summary). Identify its recovery input, event, durable boundaries, terminal state and idempotency key.'],
		exercise: [reference('Optional outbox · claim query shape (proposed schema)', `SELECT id
FROM outbox_events
WHERE state = 'pending'
   OR (state = 'sending' AND lease_expires_at < now())
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 20;

-- In the SAME short transaction: set state='sending' and lease_expires_at.
-- Commit, publish outside the lock, then acknowledge in a new transaction.
-- A real implementation also needs backoff/available_at and lease ownership. `, 'sql')],
		verify: ['Explain what survives an API restart, what Inngest replays and what can still duplicate.', 'For an outbox implementation, kill the dispatcher after claim and after publish. Both cases must eventually recover.', 'Describe how you would implement a second workflow without copying this one blindly.'],
		expected: 'You understand the system’s guarantees and its remaining tradeoffs. You can implement another workflow with deliberate persistence and retry boundaries.',
		diagram: 'architecture',
		references: [{ label: 'PostgreSQL row locking / SKIP LOCKED', url: 'https://www.postgresql.org/docs/current/sql-select.html' }, { label: 'Event publishing reference', url: docs + 'reference/python/client/send' }],
		checkpoint: { question: 'Does a PostgreSQL commit prove Inngest accepted the event?', answer: 'No. They are separate systems. An outbox saves the intention to publish atomically with your job; an independent dispatcher retries delivery until it is acknowledged.' }
	}
];
