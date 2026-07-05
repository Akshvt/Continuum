import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import './MemoryLifecycle.css'

const NODES = {
  anchor: { cx: 150, cy: 750, r: 130 },
  hub: { cx: 480, cy: 500, r: 130 },
  upA: { cx: 750, cy: 300, r: 75 },
  upB: { cx: 1010, cy: 150, r: 60 },
  downA: { cx: 700, cy: 700, r: 65 },
  downB: { cx: 960, cy: 770, r: 50 },
}

const LINKS = [
  ['anchor', 'hub'],
  ['hub', 'upA'],
  ['upA', 'upB'],
  ['hub', 'downA'],
  ['downA', 'downB'],
]

function MemoryLifecycle() {
  const bgRef = useRef(null)

  useEffect(() => {
    const reduceMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches
    if (reduceMotion) return

    const ctx = gsap.context(() => {
      // Animate the SVG circles' cx/cy attributes directly rather than a
      // CSS transform — a CSS transform (or will-change) promotes each
      // shape to its own compositing layer, and the goo filter on the
      // parent fails to re-blend separately-composited layers in
      // hardware-accelerated browsers. Attribute animation changes the
      // actual geometry instead, so there's nothing to (mis)composite.
      Object.entries(NODES).forEach(([key, node], i) => {
        gsap.to(`.memory-node-${key}`, {
          attr: {
            cx: node.cx + gsap.utils.random(-10, 10),
            cy: node.cy + gsap.utils.random(-8, 8),
          },
          duration: gsap.utils.random(12, 20),
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
          delay: i * 0.5,
        })
      })
    }, bgRef)

    return () => ctx.revert()
  }, [])

  return (
    <section className="memory-lifecycle" id="memory-lifecycle">
      <svg
        className="memory-lifecycle-bg"
        ref={bgRef}
        viewBox="0 0 1338 900"
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      >
        <defs>
          <filter
            id="memory-goo"
            x="-50%"
            y="-50%"
            width="200%"
            height="200%"
          >
            <feGaussianBlur in="SourceGraphic" stdDeviation="18" result="blur" />
            <feColorMatrix
              in="blur"
              type="matrix"
              values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -10"
              result="goo"
            />
          </filter>
        </defs>
        <g filter="url(#memory-goo)">
          {LINKS.map(([a, b]) => (
            <line
              key={`${a}-${b}`}
              className={`memory-link memory-link-${a} memory-link-${b}`}
              x1={NODES[a].cx}
              y1={NODES[a].cy}
              x2={NODES[b].cx}
              y2={NODES[b].cy}
              strokeWidth={34}
              strokeLinecap="round"
            />
          ))}
          {Object.entries(NODES).map(([key, node]) => (
            <circle
              key={key}
              className={`memory-blob memory-node-${key}`}
              cx={node.cx}
              cy={node.cy}
              r={node.r}
            />
          ))}
        </g>
      </svg>

      <div className="memory-lifecycle-content">
        <p className="memory-eyebrow">How Continuum remembers</p>
        <h2 className="memory-heading">
          Recall what mattered.
          <br />
          Forget what didn&apos;t.
        </h2>
        <p className="memory-copy">
          Every session moves through the same memory lifecycle — recalled,
          questioned, remembered, improved, and eventually retired once
          it&apos;s no longer useful. Nothing lingers longer than it should.
        </p>
      </div>

      <div className="memory-side-notes">
        <p className="memory-side-note">
          No two students follow the same path — but every memory still moves
          through recall, review, and release.
        </p>
        <p className="memory-side-note">
          Recall isn&apos;t guesswork — it&apos;s a running model that
          updates with every answer.
        </p>
      </div>
    </section>
  )
}

export default MemoryLifecycle
