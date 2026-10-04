# Pyrags backend

The real API persists conversations, documents, pgvector chunks, messages, and citations in Postgres. See [BACKEND_API_HANDOFF.md](BACKEND_API_HANDOFF.md) for its authenticated API contract.

## Local setup

```bash
cp .env.example .env
uv sync --locked
docker compose up -d api-db
uv run alembic upgrade head
uv run uvicorn main:app --reload
```

Set `OPENAI_API_KEY` and keep the `DATABASE_URL` password consistent with `API_DB_PASSWORD`. `DATABASE_URL` is required and must use `postgresql+asyncpg`. The backend database listens on host port `5433`. Apply migrations before calling real or mock database-backed routes.

Keep `FRONTEND_URL` equal to the frontend's `ORIGIN`; the API fetches its JWKS from that origin. Real upload and conversation routes require a bearer JWT and check ownership. SQL logging follows `DEBUG`, which defaults to `false`.

New real uploads store `size_bytes` and `page_count` on each document. PDF page counts include blank pages. DOCX uses the saved `Pages` property when available; this is not a fresh rendered page count. Missing DOCX page metadata stays null. These fields, the upload date, and an extracted preview are returned in the conversation header's `documents` array. Older uploads retain null values because original files are not kept; re-upload them to record their metadata.

## Frontend mock API

Set `ENABLE_MOCK_API=true` in `server/.env` and start the server with `uv run uvicorn main:app --reload`. Set it to `false` when the mock routes should be unavailable. Mock routes do not require a bearer token. They now use the configured database; the mock query also calls the selected LLM provider and incurs API usage.

Set the frontend API base URL to `http://127.0.0.1:8000/mock` while building against the mock API, then change it back to `http://127.0.0.1:8000` for the real API. The route suffixes are identical:

| Real route | Mock route |
| --- | --- |
| `POST /embeddings/upload-file` | `POST /mock/embeddings/upload-file` |
| `GET /embeddings/upload-status/{job_id}` | `GET /mock/embeddings/upload-status/{job_id}` |
| `POST /chat/conversations/{conversation_id}/query` | `POST /mock/chat/conversations/{conversation_id}/query` |
| `GET /chat/conversations?limit=10` | `GET /mock/chat/conversations?limit=10` |
| `GET /chat/conversations/{conversation_id}` | `GET /mock/chat/conversations/{conversation_id}` |
| `GET /chat/conversations/{conversation_id}/messages` | `GET /mock/chat/conversations/{conversation_id}/messages` |

Send the same multipart `file` field and chat JSON body as the real routes. The upload response gives a `job_id`; the status SSE stream ends with a `completed` event containing `conversation_id`. Use that ID for chat. Chat returns the normal `ChatResponse`, or newline-delimited token chunks followed by a completion object when `is_stream` is `true`.

Mock jobs live only in server memory. Mock conversations and messages are stored in the database under the placeholder user ID `mock-user` and survive restarts. The uploaded file is not processed. Set `ENABLE_MOCK_API=false` and remove `/mock` from the frontend paths to use the real routes.

## Request and response schemas

Authenticated `GET /chat/usage` returns `{limit, used, remaining, unlimited, resets_at}`. The daily limit is six queries across all conversations and models, resetting at midnight Lagos time (`Africa/Lagos`). The signed-in email `ayoojoade@gmail.com` has `unlimited: true`, with `limit` and `remaining` set to `null`. JSON and streaming requests reserve usage atomically before model invocation; failures are refunded. Exhausted requests return `429` with `{detail: {message, usage}}` and `Retry-After`. Usage persists independently of conversations. Apply `alembic upgrade head` to create and initialize today's usage counters. Mock chat queries also require a bearer token and consume the same quota.

These TypeScript shapes match the fields returned by the current Python API. UUIDs are represented as strings in JSON.

```ts
type UUID = string;
type FileType = "pdf" | "docx";
type JobStage =
  | "upload"
  | "extracting"
  | "chunking"
  | "embedding"
  | "storing"
  | "completed"
  | "error";

interface UploadResponse {
  job_id: string;
  filename: string;
}

interface JobProgress {
  job_id: string;
  stage: JobStage;
  message: string;
  progress: number;
  conversation_id: UUID | null;
}

interface ChatRequest {
  message: string;
  is_stream?: boolean;
  model_provider?: "openai" | "gemini";
  model_options?: {
    model?: string | null;
    temperature?: number;
  };
}

interface DocumentMetadata {
  file_name: string | null;
  file_type: FileType | null;
  page_number: number | null;
  chunk_index: number;
}

interface SourceDocument {
  content: string;
  metadata: DocumentMetadata;
}

interface ChatResponse {
  conversation_id: UUID;
  response: string;
  source_documents: SourceDocument[];
}

interface ChatStreamChunk {
  token: string;
}

interface Conversation {
  id: UUID;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface ConversationHeader {
  id: UUID;
  title: string;
  document_count: number;
}

interface Message {
  id: UUID;
  conversation_id: UUID;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  updated_at: string;
  source_documents: SourceDocument[];
}
```

`message` must be nonempty. `is_stream` defaults to `false`, `model_provider` defaults to `"openai"`, and `model_options.temperature` defaults to `0` with an allowed range of `0` to `2`. The mock query calls that provider directly with only the current message; it does not retrieve documents or pass chat history.

If testing through Swagger UI, do not send `"model": "string"`: that is a placeholder, not a model name. Omit `model_options` to use the provider default (`gpt-5-nano` for OpenAI), or set `model` to a model available to your API key. The API rejects the placeholder with `422` before calling the provider.

## Upload and progress

Send `POST /mock/embeddings/upload-file` as `multipart/form-data` with one field named `file`. Its filename must end in `.pdf` or `.docx`; the mock does not inspect or process its contents.

```bash
curl -F 'file=@./sample.pdf' http://127.0.0.1:8000/mock/embeddings/upload-file
```

Example `200` response:

```json
{"job_id":"08dc9320-a2d4-4da7-a5a2-cd998286dc03","filename":"sample.pdf"}
```

The UUIDs in the examples below are illustrative; use the IDs returned by your own upload and status stream.

The mock upload starts a background task after returning its `job_id`. That task queues six progress updates even if no status client is connected yet. Connect to `GET /mock/embeddings/upload-status/{job_id}` as an SSE stream (`Content-Type: text/event-stream`) to receive them. Each `data:` line is a JSON `JobProgress` object with the `job_id` added. The first event is immediate; the other five arrive 1.5 seconds apart by default, so the progress UI stays visible for about 7.5 seconds:

| Stage | Progress | Message |
| --- | ---: | --- |
| `upload` | 10 | `Document Uploaded` |
| `extracting` | 30 | `Extracting text from document` |
| `chunking` | 50 | `Document prepared for embedding` |
| `embedding` | 70 | `Generating embeddings` |
| `storing` | 90 | `Storing vectors` |
| `completed` | 100 | `Document processing completed` |

```bash
curl -N http://127.0.0.1:8000/mock/embeddings/upload-status/08dc9320-a2d4-4da7-a5a2-cd998286dc03
```

Example final SSE event (`conversation_id` is `null` on earlier events):

```text
data: {"job_id":"08dc9320-a2d4-4da7-a5a2-cd998286dc03","stage":"completed","message":"Document processing completed","progress":100,"conversation_id":"5a6179e2-03dd-4b85-8fea-75c0a8399550"}

```

Use the `conversation_id` from this final event for chat. The mock does not emit an `error` stage, although the real progress schema allows one.

## Conversation query

Send `POST /mock/chat/conversations/{conversation_id}/query` with `Content-Type: application/json`. Use an ID from the mock conversation list or a mock upload. This calls the selected LLM with only the current question, without chat history or document retrieval.

```bash
curl -H 'Content-Type: application/json' \
  -d '{"message":"What is 2 + 2?"}' \
  http://127.0.0.1:8000/mock/chat/conversations/5a6179e2-03dd-4b85-8fea-75c0a8399550/query
```

Example `200` JSON response (wording may vary by model):

```json
{
  "conversation_id": "5a6179e2-03dd-4b85-8fea-75c0a8399550",
  "response": "4",
  "source_documents": [
    {
      "content": "Sample citation content for frontend testing; no document was retrieved.",
      "metadata": {
        "file_name": "sample.pdf",
        "file_type": "pdf",
        "page_number": 1,
        "chunk_index": 0
      }
    }
  ]
}
```

Set `is_stream` to `true` in the same request to receive `application/x-ndjson` instead. Each line is a separate JSON object, not one JSON document, so Swagger may show "can't parse JSON" while displaying the raw stream. Append each `token` to display the answer. The final line has an empty `token` plus `conversation_id`, the complete `response`, and `source_documents`; existing token-only consumers can ignore the extra fields.

```bash
curl -N -H 'Content-Type: application/json' \
  -d '{"message":"What is 2 + 2?","is_stream":true}' \
  http://127.0.0.1:8000/mock/chat/conversations/5a6179e2-03dd-4b85-8fea-75c0a8399550/query
```

Example NDJSON output (token boundaries depend on the model):

```jsonl
{"token":"4"}
{"token":"","conversation_id":"5a6179e2-03dd-4b85-8fea-75c0a8399550","response":"4","source_documents":[{"content":"Sample citation content for frontend testing; no document was retrieved.","metadata":{"file_name":"sample.pdf","file_type":"pdf","page_number":1,"chunk_index":0}}]}
```

## Conversation list and message history

`GET /mock/chat/conversations` starts with 20 seeded conversations, so the list UI has data before any upload. Uploaded documents add more conversations. Results are ordered by `updated_at` from newest to oldest, and each mock conversation has `"mock-user"` as its placeholder `user_id`. The seeded filenames and shared message content are defined in `app/mock/data.py`.

Conversation `title` values omit the file extension. The original filename, including `.pdf` or `.docx`, remains in source-document metadata.

Both the mock and real list routes accept `?limit=N`. The default is `10`; allowed values are `1` through `100`. For example, `?limit=5` returns five conversations, while `?limit=20` returns all 20 seeded conversations before any uploads. The response remains a JSON array.

```bash
curl 'http://127.0.0.1:8000/mock/chat/conversations?limit=1'
```

Example response for `?limit=1` after uploading `sample.pdf`:

```json
[
  {
    "user_id": "mock-user",
    "title": "sample",
    "created_at": "2026-10-03T10:00:00Z",
    "updated_at": "2026-10-03T10:00:00Z",
    "id": "5a6179e2-03dd-4b85-8fea-75c0a8399550"
  }
]
```

`GET /mock/chat/conversations/{conversation_id}` returns the same `ConversationHeader` shape as the real route. Seeded conversations have different fixed `document_count` values defined in `app/mock/data.py`; newly uploaded mock conversations cycle through counts from 2 to 8. The count stays the same for a given conversation ID. An unknown ID returns `404`.

```bash
curl http://127.0.0.1:8000/mock/chat/conversations/5a6179e2-03dd-4b85-8fea-75c0a8399550
```

Example response for a mock upload named `sample.pdf`:

```json
{
  "id": "5a6179e2-03dd-4b85-8fea-75c0a8399550",
  "title": "sample",
  "document_count": 2
}
```

`GET /mock/chat/conversations/{conversation_id}/messages` returns 12 fixed seeded messages, oldest first, for each seeded conversation. Newly uploaded conversations start empty. Mock queries append the user's message and the LLM answer to the database, so subsequent reads show them. Every assistant message includes the same static mock `source_documents` sample for citation UI testing; user messages have an empty array. These citations are generated for the mock response, not retrieved or stored as part of the message. An unknown ID returns `404`.

```bash
curl http://127.0.0.1:8000/mock/chat/conversations/5a6179e2-03dd-4b85-8fea-75c0a8399550/messages
```

The first two items of a response are shown here; the full response contains 12 messages:

```json
[
  {
    "content": "Can you summarize this document?",
    "role": "user",
    "conversation_id": "5a6179e2-03dd-4b85-8fea-75c0a8399550",
    "created_at": "2026-10-03T10:01:00Z",
    "updated_at": "2026-10-03T10:01:00Z",
    "id": "e9befa4c-d321-4538-9e58-448dbcc2b674",
    "source_documents": []
  },
  {
    "content": "This is a sample summary for the mock conversation.",
    "role": "assistant",
    "conversation_id": "5a6179e2-03dd-4b85-8fea-75c0a8399550",
    "created_at": "2026-10-03T10:01:01Z",
    "updated_at": "2026-10-03T10:01:01Z",
    "id": "9841b5f6-ae26-4455-8dd5-f6b5a81cc3b1",
    "source_documents": [
      {
        "content": "Sample citation content for frontend testing; no document was retrieved.",
        "metadata": {
          "file_name": "sample.pdf",
          "file_type": "pdf",
          "page_number": 1,
          "chunk_index": 0
        }
      }
    ]
  }
]
```

## Errors and differences

The mock returns `400` for a missing filename or unsupported extension, `404` for an unknown job or conversation ID, and FastAPI validation errors (`422`) for invalid request data. These errors use FastAPI's normal `{"detail": ...}` response shape.

Mock routes do not require a bearer token. Real routes do. Mock uploads do not save file contents, but conversations and messages are persisted. Mock answers come from the LLM without document context; `source_documents` contains a static sample citation for UI testing, not evidence used to generate the answer. Do not expose the unauthenticated mock routes outside a trusted development environment.

## Adjusting mock delays

Set these values in `server/.env` and restart the server. They must be non-negative numbers in seconds:

```dotenv
MOCK_UPLOAD_DELAY_SECONDS=0.5
MOCK_STATUS_DELAY_SECONDS=1.5
MOCK_CHAT_DELAY_SECONDS=0.75
```

`MOCK_STATUS_DELAY_SECONDS` controls the pause between progress events in the background task. The GET route reads queued events; connecting later does not restart the job. Set a delay to `0` for fast local checks.

Uploaded mock filenames and document counts are process-local metadata. After a restart, uploaded mock conversations/messages still exist, but their source filename falls back to `mock-source.pdf` and their count falls back to 2. Seeded metadata is recreated on startup.
