import './TechSystem.css'

const ITEMS = [
  {
    number: '01',
    title: 'Persistent memory',
    copy: 'Every session is folded into a structured model of what a student knows — not just stored as a transcript.',
  },
  {
    number: '02',
    title: 'Adaptive pacing',
    copy: 'The tutor notices which explanations land and quietly adjusts tone, pacing, and examples in response.',
  },
  {
    number: '03',
    title: 'Signal over noise',
    copy: 'Hesitations, faster answers, and repeated mistakes all feed the model — the parts that matter, not the chat log.',
  },
  {
    number: '04',
    title: 'Graceful forgetting',
    copy: 'Once a misconception is resolved, Continuum retires it — nothing lingers longer than it should.',
  },
]

function TechSystem() {
  return (
    <section className="tech-system" id="tech-system">
      <p className="tech-system-eyebrow">The technology behind it</p>

      <div className="tech-system-content">
        <h2 className="tech-system-heading">
          A lasting understanding isn&apos;t luck —<br />
          it&apos;s a memory system.
        </h2>

        <div className="tech-system-grid">
          {ITEMS.map((item) => (
            <div className="tech-system-item" key={item.number}>
              <div className="tech-system-item-icon" aria-hidden="true">
                <svg width="28" height="18" viewBox="0 0 28 18" fill="none">
                  <circle cx="9" cy="9" r="8" stroke="currentColor" />
                  <circle cx="19" cy="9" r="8" stroke="currentColor" />
                </svg>
              </div>
              <div className="tech-system-item-heading">
                <span className="tech-system-item-title">{item.title}</span>
                <span className="tech-system-item-number">{item.number}</span>
              </div>
              <p className="tech-system-item-copy">{item.copy}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default TechSystem
