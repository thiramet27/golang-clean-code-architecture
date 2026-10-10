# Load tests (k6)

| Script | What it checks |
|---|---|
| `login-storm.js` | 30 users logging in non-stop; does a trivial endpoint stay fast? (bcrypt must not block the event loop) |
| `read-heavy.js` | authenticated reads of `/data/users` at a fixed rate (`RATE`, default 200/s) for 60 s |

Run on the server, against the API container (bypasses the nginx rate limit on purpose):

```bash
./loadtest/run.sh login-storm.js
RATE=500 ./loadtest/run.sh read-heavy.js
```

Both scripts create `loadtest@example.com` if it doesn't exist. Results are in the main README.
