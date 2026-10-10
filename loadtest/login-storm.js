// While 30 users log in non-stop, how fast does a trivial endpoint stay?
// Password hashing is CPU-heavy; if it runs on the event loop, every request waits behind it.
import http from 'k6/http'
import { check } from 'k6'

const BASE = __ENV.BASE_URL || 'http://localhost:8700'
const USER = { email: 'loadtest@example.com', password: 'loadtest-password' }
const json = { headers: { 'Content-Type': 'application/json' } }

export const options = {
  scenarios: {
    logins: { executor: 'constant-vus', vus: 30, duration: '30s', exec: 'login' },
    probe: { executor: 'constant-arrival-rate', rate: 20, timeUnit: '1s', duration: '30s',
               preAllocatedVUs: 50, exec: 'probe' },
  },
  thresholds: {
    'http_req_duration{scenario:probe}': ['p(95)<500'],
  },
  summaryTrendStats: ['avg', 'p(50)', 'p(95)', 'p(99)', 'max'],
}

export function setup() {
  http.post(`${BASE}/api/v1/users/register`, JSON.stringify({ ...USER, first_name: 'Load', last_name: 'Test' }), json)
  const res = http.post(`${BASE}/api/v1/users/login`, JSON.stringify(USER), json)
  return { token: res.json('token.access') }
}

export function login() {
  const res = http.post(`${BASE}/api/v1/users/login`, JSON.stringify(USER), json)
  check(res, { 'login 200': (r) => r.status === 200 })
}

export function probe() {
  // Health endpoint: no DB, no hashing. It should answer in a few ms no matter what logins are doing.
  const res = http.get(`${BASE}/api/v1/`)
  check(res, { 'health 200': (r) => r.status === 200 })
}
