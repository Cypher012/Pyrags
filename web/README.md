# Pyrags Web

The SvelteKit frontend for Pyrags — document-grounded question answering with cited sources. See the [root README](../README.md) for the full project overview and setup.

## Stack

SvelteKit 2 · Svelte 5 (runes) · TypeScript · Tailwind CSS 4 · shadcn-svelte · TanStack Query · Better Auth (Google + GitHub OAuth) · Drizzle ORM · Cloudflare Workers adapter

## Develop

```bash
bun install
cp .env.example .env   # fill in values
bun run db:start       # Postgres for auth (Docker)
bun run db:push        # apply the auth schema
bun run dev
```

Requires the FastAPI backend (`../server`) running on `PUBLIC_BASE_URL` (default `http://localhost:8000`).

## Inngest workbook

Run `bun run dev` and open [localhost:5173/tutorials/inngest](http://localhost:5173/tutorials/inngest).
The 17-lesson workbook follows Pyrags' existing document pipeline with source excerpts,
complete backend reference examples, a retry simulation and browser-local progress.
It does not install Inngest, run code, call an AI provider or change the backend.

The route is development-only and returns 404 in production. Normal frontend auth environment
variables and the auth database are still prerequisites because the existing application hook
runs on every route. FastAPI and the Inngest Dev Server are needed for the exercises, not for
reading the workbook. Use a disposable local API database while learning (the existing
Compose default is `pyrags` on port 5433; production uses `pyrags_app`).

## Scripts

| Command                                          | Purpose                              |
| ------------------------------------------------ | ------------------------------------ |
| `bun run dev`                                    | Vite dev server                      |
| `bun run check`                                  | Type + Svelte diagnostics            |
| `bun run lint`                                   | Prettier check + ESLint              |
| `bun run format`                                 | Prettier write                       |
| `bun run db:push` / `db:generate` / `db:migrate` | Drizzle schema workflows             |
| `bun run build`                                  | Production build (Cloudflare Worker) |
