/**
 * Typed API client.
 *
 * Every fetch call reads VITE_API_URL from the environment so the base URL
 * is never hard-coded.  All functions throw on non-2xx responses — callers
 * should catch and handle errors themselves.
 */

const BASE = import.meta.env.VITE_API_URL || ''

// ─────────────────────────────────────────────
// Internal helper
// ─────────────────────────────────────────────

async function request(method, path, body) {
  const init = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }

  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText)
    throw new Error(`API ${method} ${path} → ${res.status}: ${detail}`)
  }
  return res.json()
}

const get  = (path)       => request('GET',  path)
const post = (path, body) => request('POST', path, body)

// ─────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────

/** @returns {{ student_id: string, email: string }} */
export const authLogin  = (email) => post('/api/auth/login',  { email })

/** @returns {{ student_id: string, email: string }} */
export const authSignup = (email) => post('/api/auth/signup', { email })

/** @returns {{ student_id: string, email: string }} */
export const authMe = (studentId) => get(`/api/auth/me?student_id=${encodeURIComponent(studentId)}`)

// ─────────────────────────────────────────────
// Tutoring
// ─────────────────────────────────────────────

/**
 * Fetch the next tutoring question for a student on a concept.
 * @param {{ student_id: string, current_concept: string }} params
 * @returns {{ question: string, strategy: string, context: string }}
 */
export const tutoringQuestion = (params) => post('/api/tutoring/question', params)

/**
 * Submit a student answer for grading and memory logging.
 * @param {{ student_id: string, concept: string, question: string,
 *           student_answer: string, strategy_used: string }} params
 * @returns {{ is_correct: boolean, feedback: string, misconception: string|null,
 *             mastery_delta: number, triggers_fired: string[],
 *             grading_unavailable: boolean }}
 */
export const tutoringAnswer = (params) => post('/api/tutoring/answer', params)

// ─────────────────────────────────────────────
// Dashboard
// ─────────────────────────────────────────────

/**
 * Fetch aggregated mastery and strategy data for a student.
 * @param {string} studentId
 * @returns {{ student_id: string, concepts: Array, recall_available: boolean }}
 */
export const getDashboard = (studentId) => get(`/api/dashboard/${encodeURIComponent(studentId)}`)

// ─────────────────────────────────────────────
// Timeline
// ─────────────────────────────────────────────

/**
 * Fetch chronological memory lifecycle events for a student.
 * @param {string} studentId
 * @returns {{ student_id: string, event_count: number, events: Array }}
 */
export const getTimeline = (studentId) => get(`/api/timeline/${encodeURIComponent(studentId)}`)

// ─────────────────────────────────────────────
// Health
// ─────────────────────────────────────────────

export const healthCheck = () => get('/health')

// ─────────────────────────────────────────────
// Status
// ─────────────────────────────────────────────

/**
 * Fetch whether the student has pending background memory writes.
 * @param {string} studentId
 * @returns {{ has_pending_writes: boolean }}
 */
export const getStatus = (studentId) => get(`/api/status/${encodeURIComponent(studentId)}`)

