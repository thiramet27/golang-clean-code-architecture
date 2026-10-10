// Sustained reads of the generic data API (auth + Postgres query + schema) for one minute.
import http from 'k6/http'
import { check } from 'k6'

const BASE = __ENV.BASE_URL || 'http://localhost:8700'
const USER = { email: 'loadtest@example.com', password: 'loadtest-password' }
const json = { headers: { 'Content-Type': 'application/json' } }

export const options = {
  scenarios: {
    reads: { executor: 'constant-arrival-rate', rate: Number(__ENV.RATE || 200), timeUnit: '1s', duration: '60s',
             preAllocatedVUs: 100, maxVUs: 300 },
  },
  thresholds: { http_req_failed: ['rate<0.01'], http_req_duration: ['p(95)<300'] },
  summaryTrendStats: ['avg', 'p(50)', 'p(95)', 'p(99)', 'max'],
}

export function setup() {
  http.post(`${BASE}/api/v1/users/register`, JSON.stringify({ ...USER, first_name: 'Load', last_name: 'Test' }), json)
  return { token: http.post(`${BASE}/api/v1/users/login`, JSON.stringify(USER), json).json('token.access') }
}

export default function (data) {
  const res = http.get(`${BASE}/api/v1/data/users/?_pageSize=20`, {
    headers: { Authorization: `Bearer ${data.token}` },
  })
  check(res, { 'list 200': (r) => r.status === 200 })
}
