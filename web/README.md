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

## Scripts

| Command                                          | Purpose                              |
| ------------------------------------------------ | ------------------------------------ |
| `bun run dev`                                    | Vite dev server                      |
| `bun run check`                                  | Type + Svelte diagnostics            |
| `bun run lint`                                   | Prettier check + ESLint              |
| `bun run format`                                 | Prettier write                       |
| `bun run db:push` / `db:generate` / `db:migrate` | Drizzle schema workflows             |
| `bun run build`                                  | Production build (Cloudflare Worker) |
