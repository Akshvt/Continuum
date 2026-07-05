import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import gsap from 'gsap'
import { SplitText } from 'gsap/SplitText'
import './Hero.css'

gsap.registerPlugin(SplitText)

function Hero() {
  const heroRef = useRef(null)
  const headlineLeftRef = useRef(null)
  const headlineRightRef = useRef(null)

  useEffect(() => {
    const reduceMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches

    let ctx
    let cancelled = false

    const run = () => {
      if (cancelled) return

      ctx = gsap.context(() => {
        if (reduceMotion) return

        const splitLeft = new SplitText(headlineLeftRef.current, {
          type: 'lines, words',
          mask: 'lines',
        })
        const splitRight = new SplitText(headlineRightRef.current, {
          type: 'lines, words',
          mask: 'lines',
        })

        gsap.set([splitLeft.words, splitRight.words], {
          filter: 'blur(18px)',
          opacity: 0,
          yPercent: 40,
        })
        gsap.set(['.hero-badge', '.hero-copy', '.hero-figure-img', '.hero-actions'], {
          opacity: 0,
          y: 16,
        })

        gsap
          .timeline({ defaults: { ease: 'power3.out' } })
          .to('.hero-badge', { opacity: 1, y: 0, duration: 0.6 })
          .to(
            splitLeft.words,
            { filter: 'blur(0px)', opacity: 1, yPercent: 0, duration: 0.9, stagger: 0.05 },
            '-=0.3',
          )
          .to('.hero-copy', { opacity: 1, y: 0, duration: 0.6 }, '-=0.5')
          .to('.hero-figure-img', { opacity: 1, y: 0, duration: 1 }, '-=0.8')
          .to(
            splitRight.words,
            { filter: 'blur(0px)', opacity: 1, yPercent: 0, duration: 0.9, stagger: 0.05 },
            '-=0.7',
          )
          .to('.hero-actions', { opacity: 1, y: 0, duration: 0.6 }, '-=0.4')
      }, heroRef)
    }

    // Wait for web fonts to finish loading before measuring/splitting the
    // headline — otherwise SplitText sizes the reveal masks using the
    // fallback font's metrics, and the real font's descenders get clipped.
    if (document.fonts?.ready) {
      document.fonts.ready.then(run)
    } else {
      run()
    }

    return () => {
      cancelled = true
      ctx && ctx.revert()
    }
  }, [])

  return (
    <section className="hero" id="top" ref={heroRef}>
      <div className="hero-inner">
        <div className="hero-texture" aria-hidden="true" />

        <div className="hero-col hero-col-left">
          <span className="hero-badge">
            <span className="hero-badge-tag">Beta</span>
            Continuum Memory Engine
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
              <path
                d="M2.5 9.5L9.5 2.5M9.5 2.5H4M9.5 2.5V8"
                stroke="currentColor"
                strokeWidth="1.3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>

          <h1 className="hero-headline" ref={headlineLeftRef}>
            A tutor that never forgets
          </h1>
        </div>

        <p className="hero-copy">
          Continuum remembers every session, adapts its teaching style to how
          each student learns, and quietly cleans up misconceptions once
          they&apos;re resolved — so nothing is ever explained twice.
        </p>

        <div className="hero-figure">
          <img
            src="/images/main-screen-model-white.png"
            alt="Silhouette of a head with a glowing neural network representing Continuum's memory engine"
            className="hero-figure-img"
          />
        </div>

        <div className="hero-col hero-col-right">
          <h2 className="hero-headline hero-headline-right" ref={headlineRightRef}>
            with memory built in.
          </h2>

          <div className="hero-actions">
            <Link to="/signup" className="btn btn-primary">
              Let&apos;s Get Started
            </Link>
            <a href="#how-it-adapts" className="btn btn-outline">
              See How It Works
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Hero
