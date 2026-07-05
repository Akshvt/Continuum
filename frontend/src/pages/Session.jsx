import { useEffect, useRef, useState, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import {
  tutoringQuestion,
  tutoringAnswer,
  getDashboard,
  getTimeline,
  getStatus,
} from '../lib/api.js'
import './Session.css'

// ─────────────────────────────────────────────
// Curriculum concepts (mirrors backend CURRICULUM_LADDER order)
// ─────────────────────────────────────────────

const CONCEPTS = [
  { id: 'literals_and_values',  label: 'Literals & Values' },
  { id: 'variables',            label: 'Variables' },
  { id: 'data_types',           label: 'Data Types' },
  { id: 'print_and_input',      label: 'Print & Input' },
  { id: 'operators',            label: 'Operators' },
  { id: 'strings',              label: 'Strings' },
  { id: 'boolean_logic',        label: 'Boolean Logic' },
  { id: 'conditionals',         label: 'Conditionals' },
  { id: 'lists',                label: 'Lists' },
  { id: 'loops',                label: 'Loops' },
  { id: 'functions',            label: 'Functions' },
  { id: 'dictionaries',         label: 'Dictionaries' },
]

const conceptLabel = (id) => CONCEPTS.find((c) => c.id === id)?.label ?? id

const masteryLevel = (pct) => (pct >= 70 ? 'good' : pct >= 40 ? 'warn' : 'bad')

const nowStamp = () =>
  new Date().toLocaleTimeString('en-GB', { hour12: false })

const shortTime = () =>
  new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })

// ─────────────────────────────────────────────
// SVG Icons
// ─────────────────────────────────────────────

function PanelToggleIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="4" width="18" height="16" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <path d="M15 4v16" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function PaperclipIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M17.5 8.5 9.7 16.3a3.2 3.2 0 0 1-4.5-4.5l8.1-8.1a2.2 2.2 0 0 1 3.1 3.1l-7.8 7.8a1.1 1.1 0 0 1-1.6-1.6l6.9-6.9"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function HintIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.5.36.8.95.8 1.6v.5h5.4v-.5c0-.65.3-1.24.8-1.6A6 6 0 0 0 12 3Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 19V5M12 5l-6 6M12 5l6 6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function CopyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="8" y="8" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  )
}

function ChevronIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="chevron">
      <path
        d="m6 9 6 6 6-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function RetryIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M3 12a9 9 0 1 1 2.6 6.3M3 12V6m0 6h6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function LogoutIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="m16 17 5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

// ─────────────────────────────────────────────
// Session page
// ─────────────────────────────────────────────

function Session() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  // ── Concept selection ─────────────────────
  const [concept, setConcept] = useState(CONCEPTS[0].id)
  const [conceptPending, setConceptPending] = useState(CONCEPTS[0].id)
  const [selectingConcept, setSelectingConcept] = useState(false)

  // ── Chat ─────────────────────────────────
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [currentStrategy, setCurrentStrategy] = useState('')

  // ── Progression tracking (per session, resets on concept switch) ─
  // correctStreak: consecutive correct answers on the current concept
  const correctStreakRef = useRef(0)

  // ── Dashboard panels ──────────────────────
  const [mastery, setMastery] = useState([])
  const [misconceptions, setMisconceptions] = useState([])
  const [log, setLog] = useState([])
  const [counters, setCounters] = useState({ recall: 0, remember: 0, improve: 0, forget: 0 })
  const [chatHistory, setChatHistory] = useState([])

  // ── UI ───────────────────────────────────
  const [dashboardOpen, setDashboardOpen] = useState(
    () => !window.matchMedia('(max-width: 880px)').matches,
  )
  const [apiError, setApiError] = useState('')
  const [pendingWrites, setPendingWrites] = useState(false)

  const transcriptRef = useRef(null)

  // Auto-scroll on new message
  useEffect(() => {
    const el = transcriptRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  // ── Helpers ───────────────────────────────

  const pushLog = useCallback((fn, text) => {
    setLog((prev) => [...prev, { time: nowStamp(), fn, text }])
    setCounters((prev) => ({ ...prev, [fn]: (prev[fn] ?? 0) + 1 }))
  }, [])

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, { id: `msg-${Date.now()}-${Math.random()}`, ...msg }])
  }, [])

  // ── Data loading ──────────────────────────

  const loadDashboard = useCallback(async () => {
    try {
      const data = await getDashboard(auth.student_id)
      if (data.concepts?.length) {
        // Only extract entries that actually have a mastery_level value.
        // If the filtered list is empty it means Cognee recall is still
        // catching up after a background remember() — keep last known
        // good state rather than blanking the panel.
        const withMastery = data.concepts
          .filter((c) => c.mastery_level != null)
          .map((c) => ({
            name: conceptLabel(c.concept),
            pct: Math.round((c.mastery_level ?? 0) * 100),
          }))
        if (withMastery.length > 0) {
          setMastery(withMastery)
        }
        // empty withMastery → leave mastery state untouched
      }
    } catch {
      // Non-fatal — dashboard shows empty state
    }
  }, [auth.student_id])

  const loadTimeline = useCallback(async () => {
    try {
      const data = await getTimeline(auth.student_id)
      if (data.events?.length) {
        // Surface misconception events to the panel
        const miscons = data.events
          .filter((e) => e.detail?.misconception)
          .map((e) => ({
            text: e.detail.misconception,
            status: data.events.some(
              (fe) => fe.operation === 'forget' && fe.detail?.misconception === e.detail.misconception,
            )
              ? 'resolved'
              : 'active',
          }))
        const unique = miscons.filter(
          (m, i, arr) => arr.findIndex((x) => x.text === m.text) === i,
        )
        setMisconceptions(unique)

        // Build chat history from remember events grouped by date
        const sessionDays = {}
        data.events
          .filter((e) => e.operation === 'remember')
          .forEach((e) => {
            const day = e.timestamp?.slice(0, 10) ?? 'Unknown'
            if (!sessionDays[day]) sessionDays[day] = 0
            sessionDays[day]++
          })
        setChatHistory(
          Object.entries(sessionDays).map(([day, count], i) => ({
            id: i,
            title: `Session ${i + 1} — ${day}`,
            date: day,
          })),
        )

        // Lifecycle log
        const logEntries = data.events.slice(-20).map((e) => ({
          time: e.timestamp?.slice(11, 19) ?? '—',
          fn: e.operation,
          text: e.detail?.concept ?? e.detail?.query ?? e.detail?.trigger ?? '',
        }))
        setLog(logEntries)

        // Counters
        const ops = ['recall', 'remember', 'improve', 'forget']
        const counts = {}
        ops.forEach((op) => {
          counts[op] = data.events.filter((e) => e.operation === op).length
        })
        setCounters(counts)
      }
    } catch {
      // Non-fatal
    }
  }, [auth.student_id])

  const loadQuestion = useCallback(async (conceptId, signal) => {
    setIsThinking(true)
    setApiError('')
    try {
      pushLog('recall', `loading first question for ${conceptId}`)
      const data = await tutoringQuestion({
        student_id: auth.student_id,
        current_concept: conceptId,
      }, signal)
      const strategy = data.strategy ?? 'default'
      setCurrentQuestion(data.question)
      setCurrentStrategy(strategy)
      addMessage({
        kind: 'toast',
        fn: 'recall',
        text: `retrieved student history — using ${strategy} strategy`,
      })
      addMessage({
        kind: 'tutor',
        tag: `Tutor · ${strategy}`,
        text: data.question,
      })
    } catch (err) {
      if (err.name === 'AbortError') return
      setApiError(`Could not load question: ${err.message}`)
      addMessage({
        kind: 'tutor',
        text: `⚠ Backend unavailable — ${err.message}`,
      })
    } finally {
      if (!signal?.aborted) {
        setIsThinking(false)
      }
    }
  }, [auth.student_id, addMessage, pushLog])

  // On mount and concept change: load everything in parallel
  useEffect(() => {
    const controller = new AbortController()
    correctStreakRef.current = 0   // reset streak on any concept change
    setMessages([])
    loadDashboard()
    loadTimeline()
    loadQuestion(concept, controller.signal)
    
    return () => {
      controller.abort()
    }
  }, [concept]) // eslint-disable-line react-hooks/exhaustive-deps

  // Background polling for dashboard/timeline/status
  useEffect(() => {
    if (!auth?.student_id) return
    const interval = setInterval(async () => {
      try {
        const statusRes = await getStatus(auth.student_id)
        setPendingWrites(statusRes.has_pending_writes)
        // If there are no pending writes or it transitioned, load data.
        // Even if there are pending writes, it doesn't hurt to update the dashboard
        // with any that have just finished.
        loadDashboard()
        loadTimeline()
      } catch (err) {
        // Silently ignore polling errors
      }
    }, 20000) // Poll every 20 seconds
    return () => clearInterval(interval)
  }, [auth.student_id, loadDashboard, loadTimeline])

  // ── Send answer ───────────────────────────

  const handleSend = async () => {
    const text = input.trim()
    if (!text || isThinking) return

    addMessage({ kind: 'student', text, time: shortTime() })
    setInput('')
    setIsThinking(true)
    setApiError('')

    try {
      const result = await tutoringAnswer({
        student_id: auth.student_id,
        concept,
        question: currentQuestion,
        student_answer: text,
        strategy_used: currentStrategy,
      })

      // Toast for memory op (remember always fires)
      const memOp = result.grading_unavailable ? 'recall' : 'remember'
      const toastText = result.grading_unavailable
        ? 'grading unavailable — answer not logged'
        : `logged answer — mastery delta ${result.mastery_delta > 0 ? '+' : ''}${(result.mastery_delta * 100).toFixed(0)}%`
      addMessage({ kind: 'toast', fn: memOp, text: toastText })
      pushLog(memOp, toastText)

      // Auto-trigger toasts
      if (result.triggers_fired?.length) {
        result.triggers_fired.forEach((t) => {
          const op = t.startsWith('forget') ? 'forget' : 'improve'
          addMessage({ kind: 'toast', fn: op, text: t })
          pushLog(op, t)
        })
      }

      // Tutor reply with feedback
      addMessage({
        kind: 'tutor',
        text: result.feedback,
        masteryGain: result.mastery_delta > 0 ? Math.round(result.mastery_delta * 100) : null,
        misconception: result.misconception ?? null,
      })

      // Update mastery panel immediately from the local delta (authoritative,
      // no Cognee round-trip lag). This is the value the poll must NOT overwrite
      // with an empty result (handled in loadDashboard).
      if (!result.grading_unavailable) {
        setMastery((prev) => {
          const label = conceptLabel(concept)
          const existing = prev.find((m) => m.name === label)
          const delta = Math.round((result.mastery_delta ?? 0) * 100)
          if (existing) {
            return prev.map((m) =>
              m.name === label
                ? { ...m, pct: Math.max(0, Math.min(100, m.pct + delta)) }
                : m,
            )
          }
          return [...prev, { name: label, pct: Math.max(0, 50 + delta) }]
        })
      }

      // Track new misconceptions
      if (result.misconception) {
        setMisconceptions((prev) => {
          if (prev.find((m) => m.text === result.misconception)) return prev
          return [{ text: result.misconception, status: 'active' }, ...prev]
        })
      }

      // Resolve misconceptions that were just forgotten
      if (result.triggers_fired?.some((t) => t.startsWith('forget'))) {
        setMisconceptions((prev) =>
          prev.map((m) => ({ ...m, status: 'resolved' })),
        )
      }

      // ── Concept progression ──────────────────────────────────────────
      // Track consecutive correct answers on this concept (not counting
      // unavailable grades). Advance to the next concept in the curriculum
      // ladder after 2 correct answers in a row, so the student never
      // keeps seeing verbatim-similar questions on the same topic.
      let nextConceptId = concept
      if (!result.grading_unavailable) {
        if (result.is_correct) {
          correctStreakRef.current += 1
          const ADVANCE_AFTER = 2
          if (correctStreakRef.current >= ADVANCE_AFTER) {
            correctStreakRef.current = 0
            const idx = CONCEPTS.findIndex((c) => c.id === concept)
            if (idx !== -1 && idx < CONCEPTS.length - 1) {
              nextConceptId = CONCEPTS[idx + 1].id
              addMessage({
                kind: 'toast',
                fn: 'improve',
                text: `mastered ${conceptLabel(concept)} — advancing to ${conceptLabel(nextConceptId)}`,
              })
              setConcept(nextConceptId)
              setConceptPending(nextConceptId)
            }
          }
        } else {
          // Wrong answer resets the streak
          correctStreakRef.current = 0
        }
      }

      // Load next question (short delay for readability).
      // If concept advanced, setConcept triggers the useEffect which calls
      // loadQuestion automatically — so we only need to fetch here when
      // staying on the same concept.
      if (nextConceptId === concept) {
        window.setTimeout(async () => {
          try {
            const next = await tutoringQuestion({
              student_id: auth.student_id,
              current_concept: concept,
            })
            setCurrentQuestion(next.question)
            setCurrentStrategy(next.strategy ?? currentStrategy)
            addMessage({ kind: 'tutor', text: next.question })
          } catch {
            // Silently skip next question fetch
          }
          setIsThinking(false)
        }, 800)
      } else {
        // concept changed — useEffect will fire loadQuestion, just unblock input
        setIsThinking(false)
      }
    } catch (err) {
      setApiError(`Could not submit answer: ${err.message}`)
      addMessage({ kind: 'tutor', text: `⚠ ${err.message}` })
      setIsThinking(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  const copyText = (text) => navigator.clipboard?.writeText(text)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // ── Concept switcher ──────────────────────

  const applyConceptSwitch = () => {
    setConcept(conceptPending)
    setSelectingConcept(false)
  }

  // ─────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────

  return (
    <div className="session-page">
      {/* Top bar */}
      <div className="topbar">
        <Link to="/" className="brand">continuum</Link>

        {selectingConcept ? (
          <div className="concept-picker">
            <select
              value={conceptPending}
              onChange={(e) => setConceptPending(e.target.value)}
              className="concept-select"
            >
              {CONCEPTS.map((c) => (
                <option key={c.id} value={c.id}>{c.label}</option>
              ))}
            </select>
            <button type="button" className="btn-sm" onClick={applyConceptSwitch}>
              Switch
            </button>
            <button type="button" className="btn-sm ghost" onClick={() => setSelectingConcept(false)}>
              Cancel
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="ctx-item ctx-clickable"
            onClick={() => { setConceptPending(concept); setSelectingConcept(true) }}
            title="Change concept"
          >
            Concept <strong>{conceptLabel(concept)}</strong>
          </button>
        )}

        {currentStrategy && (
          <span className="badge">◆ {currentStrategy}</span>
        )}

        <div className="ctx-item">
          <span className="user-email">{auth?.email}</span>
        </div>

        <div className="memory-live">
          {pendingWrites ? (
            <>
              <span className="pulse-dot spin" style={{ backgroundColor: '#f5a623', boxShadow: '0 0 8px #f5a623' }} /> Still updating your progress...
            </>
          ) : (
            <>
              <span className="pulse-dot" /> Memory active
            </>
          )}
        </div>

        <button
          type="button"
          className="icon-btn"
          onClick={handleLogout}
          aria-label="Sign out"
          title="Sign out"
        >
          <LogoutIcon />
        </button>

        <button
          type="button"
          className="icon-btn dash-toggle"
          onClick={() => setDashboardOpen((open) => !open)}
          aria-label={dashboardOpen ? 'Hide knowledge map' : 'Show knowledge map'}
          aria-pressed={dashboardOpen}
        >
          <PanelToggleIcon />
        </button>
      </div>

      {/* API error banner */}
      {apiError && (
        <div className="api-error-banner" role="alert">
          {apiError}
          <button type="button" onClick={() => setApiError('')}>✕</button>
        </div>
      )}

      <div className={`workspace ${dashboardOpen ? '' : 'dash-hidden'}`}>
        {/* Chat column */}
        <div className="chat-col">
          <div className="transcript" ref={transcriptRef}>
            {messages.length === 0 && !isThinking && (
              <div className="transcript-empty">Loading your first question…</div>
            )}

            {messages.map((msg) => {
              if (msg.kind === 'toast') {
                return (
                  <div key={msg.id} className="status-line">
                    <span className="status-dot" />
                    <span className="fn">{msg.fn}()</span> {msg.text}
                  </div>
                )
              }

              if (msg.kind === 'student') {
                return (
                  <div key={msg.id} className="msg student">
                    <div className="bubble">{msg.text}</div>
                    <span className="msg-time">{msg.time}</span>
                  </div>
                )
              }

              return (
                <div key={msg.id} className="msg tutor">
                  {msg.tag && <span className="msg-tag">{msg.tag}</span>}
                  <div className="tutor-text">{msg.text}</div>
                  {msg.masteryGain && (
                    <span className="mastery-gain">
                      ▲ +{msg.masteryGain}% mastery — {conceptLabel(concept)}
                    </span>
                  )}
                  {msg.misconception && (
                    <div className="misconception-chip">
                      <b>Misconception</b>
                      <span>{msg.misconception}</span>
                    </div>
                  )}
                  <div className="msg-toolbar">
                    <button
                      type="button"
                      className="icon-btn"
                      onClick={() => copyText(msg.text)}
                      aria-label="Copy message"
                    >
                      <CopyIcon />
                    </button>
                    <button
                      type="button"
                      className="icon-btn"
                      aria-label="Retry"
                      onClick={() => loadQuestion(concept)}
                    >
                      <RetryIcon />
                    </button>
                  </div>
                </div>
              )
            })}

            {isThinking && (
              <div className="status-line">
                <span className="status-dot spin" />
                Thinking about the concept…
              </div>
            )}
          </div>

          <div className="composer">
            <div className="composer-bar">
              <button type="button" className="icon-btn ghost" aria-label="Attach">
                <PaperclipIcon />
              </button>
              <textarea
                placeholder="Type your answer…"
                rows="1"
                value={input}
                disabled={isThinking}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
              />
              <button type="button" className="icon-btn ghost" aria-label="Hint">
                <HintIcon />
              </button>
              <button
                type="button"
                className="send-circle"
                onClick={handleSend}
                disabled={isThinking || !input.trim()}
                aria-label="Send"
              >
                <SendIcon />
              </button>
            </div>
          </div>
        </div>

        {dashboardOpen && (
          <div className="dash-backdrop" onClick={() => setDashboardOpen(false)} />
        )}

        {/* Dashboard column */}
        <div className={`dash-col ${dashboardOpen ? '' : 'dash-closed'}`}>
          <div className="dash-panel">

            {/* Chat / session history */}
            <details className="panel">
              <summary>
                <h2>Session History</h2>
                <ChevronIcon />
              </summary>
              <div className="panel-body">
                {chatHistory.length === 0 ? (
                  <p className="panel-empty">No sessions yet.</p>
                ) : (
                  chatHistory.map((item) => (
                    <div className="history-item" key={item.id}>
                      <span>{item.title}</span>
                      <span className="history-date">{item.date}</span>
                    </div>
                  ))
                )}
              </div>
            </details>

            {/* Mastery map */}
            <details className="panel" open>
              <summary>
                <h2>Mastery Map</h2>
                <ChevronIcon />
              </summary>
              <div className="panel-body">
                {mastery.length === 0 ? (
                  <p className="panel-empty">No mastery data yet — answer a question to start tracking.</p>
                ) : (
                  mastery.map((m) => (
                    <div className="mastery-row" key={m.name}>
                      <span className="label">{m.name}</span>
                      <div className="mastery-track">
                        <div
                          className={`mastery-fill ${masteryLevel(m.pct)}`}
                          style={{ width: `${m.pct}%` }}
                        />
                      </div>
                      <span className="mastery-pct">{m.pct}%</span>
                    </div>
                  ))
                )}
              </div>
            </details>

            {/* Misconceptions */}
            <details className="panel" open>
              <summary>
                <h2>Misconceptions</h2>
                <ChevronIcon />
              </summary>
              <div className="panel-body">
                {misconceptions.length === 0 ? (
                  <p className="panel-empty">None detected yet.</p>
                ) : (
                  misconceptions.map((m) => (
                    <div className={`miscon-item ${m.status}`} key={m.text}>
                      <span>{m.text}</span>
                      <span className="miscon-status">{m.status}</span>
                    </div>
                  ))
                )}
              </div>
            </details>

            {/* Memory lifecycle log */}
            <details className="panel" open>
              <summary>
                <h2>Memory Lifecycle Log</h2>
                <ChevronIcon />
              </summary>
              <div className="panel-body">
                {log.length === 0 ? (
                  <p className="panel-empty">No events yet.</p>
                ) : (
                  log.map((entry, index) => (
                    <div className="log-item" key={`${entry.time}-${index}`}>
                      <span className="log-time">{entry.time}</span>
                      <span className={`log-fn ${entry.fn}`}>{entry.fn}()</span>
                      <span>{entry.text}</span>
                    </div>
                  ))
                )}
              </div>
            </details>

            {/* Dev counters */}
            <details className="panel dev-panel">
              <summary>
                <span className="dev-label">Dev — memory op counters</span>
                <ChevronIcon />
              </summary>
              <div className="panel-body">
                <div className="dev-counters">
                  {Object.entries(counters).map(([fn, count]) => (
                    <div className="dev-counter" key={fn}>
                      <div className="n">{count}</div>
                      <div className="l">{fn}</div>
                    </div>
                  ))}
                </div>
              </div>
            </details>

          </div>
        </div>
      </div>
    </div>
  )
}

export default Session
