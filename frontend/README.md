# Khaojai frontend

A small React client for the FastAPI backend in `../backend-python`. It covers auth (register, login, profile, logout) and a data browser that builds its table from the API's schema.

Stack: Vite, React 19, TypeScript (strict), React Router and plain CSS. No UI or state libraries.

## Running it

Requirements: Node 22+ and pnpm. The backend must be running on port 3000. Its CORS config allows `http://localhost:5173`.

```bash
cp .env.example .env.local   # optional; this is the default value
pnpm install
pnpm dev                     # http://localhost:5173
```

| Variable       | Default                        | Purpose              |
| -------------- | ------------------------------ | -------------------- |
| `VITE_API_URL` | `http://localhost:3000/api/v1` | Base URL of the API  |

## Pages

| Route       | Auth | What it does                                                                                       |
| ----------- | ---- | -------------------------------------------------------------------------------------------------- |
| `/login`    | no   | Email/password login. The API's error `message` shows inline.                                      |
| `/register` | no   | Creates an account, then logs in automatically.                                                    |
| `/profile`  | yes  | Shows the current user. The logout button revokes the refresh token.                              |
| `/data`     | yes  | Pick a model (`users`, `user-permissions`, `products`) to browse its records.                      |

The data browser calls `GET /data/{slug}/describe` and builds the table columns from `fields`. Each cell is formatted by its field type (datetimes in your locale, booleans as ✓/–). You can page through results, change the page size and add exact-match filters, which are sent as `?field=value`. Clicking a row opens `GET /data/{slug}/{id}` in a side panel. A 403 (non-admin on `user-permissions`), a 404 (`products` without MongoDB) or a 400 (bad filter value) shows as an inline message.

## Layout

```
src/
  api/
    client.ts      fetch wrapper, ApiError, token refresh
    tokens.ts      token storage (memory + localStorage)
    endpoints.ts   typed functions for each endpoint
    types.ts       response and request types
  auth/            AuthProvider / useAuth, RequireAuth route guard
  features/data/   table, filters, pagination, record detail, value formatting
  pages/           Login, Register, Profile, Data
  hooks.ts         useAsync: loads data and discards stale responses
```

## Token refresh

All of this lives in `src/api/client.ts`.

- Requests made with `auth: true` send `Authorization: Bearer <access>`.
- When one of them gets a 401, the client calls `/users/refresh-token` and retries the original request once.
- The backend rotates both tokens, so the old refresh token stops working. To avoid spending it twice, concurrent 401s share a single refresh promise. If another request already refreshed the token while this one was in flight, the client just retries with the new token.
- If the refresh fails, or the retried request still gets a 401, the client clears the tokens and calls the session-expired handler. `AuthProvider` registers that handler, which sends the user back to `/login`.

Tokens live in memory and are mirrored to `localStorage`, so a session survives a reload. Every storage access is wrapped in try/catch, so blocked storage still works and only the persistence is lost.

## Scripts

```bash
pnpm test    # vitest run: API client refresh logic, Login and Data pages, formatters
pnpm lint    # tsc --noEmit + eslint
pnpm build   # type-check + production build into dist/
```

The tests mock `fetch` (see `src/test/fetchMock.ts`), so they don't need a running backend.
