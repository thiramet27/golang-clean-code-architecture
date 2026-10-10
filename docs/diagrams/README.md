# Diagrams

| File | Shows |
|---|---|
| `clean-architecture.drawio` | layers of `backend/src/app` and the dependency rule |
| `go-vs-python.drawio` | imports in the Go template (violations in red) vs the Python rewrite |
| `request-lifecycle.drawio` | path of a request and which layer returns each error |
| `deployment.drawio` | Cloudflare Tunnel → nginx → FastAPI → Postgres / Atlas |

Edit the `.drawio` files in [diagrams.net](https://app.diagrams.net) or the draw.io desktop app, then export PNG
(scale 2, border 16). Headless export:

```bash
docker run --rm --shm-size=1g -v "$PWD:/data" rlespinasse/drawio-desktop-headless \
  -x -f png -s 2 -b 16 -o /data/deployment.png /data/deployment.drawio
```

Icons are embedded in the files: [Devicon](https://devicon.dev) (MIT) and [Simple Icons](https://simpleicons.org) (CC0).
