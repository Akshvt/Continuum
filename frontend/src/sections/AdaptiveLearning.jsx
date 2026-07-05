import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SplitText } from 'gsap/SplitText'
import './AdaptiveLearning.css'

gsap.registerPlugin(ScrollTrigger, SplitText)

function AdaptiveLearning() {
  const sectionRef = useRef(null)

  useEffect(() => {
    const reduceMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches

    // Below 1000px the CSS drops the pinned/absolute layout for a plain
    // stacked one (see AdaptiveLearning.css) — every column is already
    // visible in normal flow, so the scroll-jacking pin has nothing to
    // reveal and would only fight the page's natural scroll.
    const isMobile = window.matchMedia('(max-width: 1000px)').matches

    // Reduced motion still needs the pin to work (it's the only way to reach
    // col-3/col-4's content), so instead of skipping setup we collapse every
    // tween to near-zero duration rather than removing the phase logic.
    const dur = reduceMotion ? 0.01 : 0.75
    const swapDelay = reduceMotion ? 0 : 0.5

    let ctx
    let cancelled = false

    const run = () => {
      if (cancelled || isMobile) return

      ctx = gsap.context(() => {
        const textElements = gsap.utils.toArray(
          '.adaptive-col-3 h1, .adaptive-col-3 p',
        )
        textElements.forEach((el) => {
          const split = new SplitText(el, {
            type: 'lines',
            linesClass: 'adaptive-line',
          })
          split.lines.forEach((line) => {
            line.innerHTML = `<span>${line.textContent}</span>`
          })
        })

        gsap.set(
          '.adaptive-col-3 .adaptive-col-content-wrapper .adaptive-line span',
          { y: '0%' },
        )
        gsap.set(
          '.adaptive-col-3 .adaptive-col-content-wrapper-2 .adaptive-line span',
          { y: '-125%' },
        )

        let currentPhase = 0

        ScrollTrigger.create({
          trigger: sectionRef.current,
          start: 'top top',
          end: () => `+=${window.innerHeight * 5}`,
          pin: true,
          pinSpacing: true,
          onUpdate: (self) => {
            const progress = self.progress

            // forward: rest -> phase 1 (crossing 25%)
            if (progress >= 0.25 && currentPhase === 0) {
              currentPhase = 1
              gsap.to('.adaptive-col-1', { opacity: 0, scale: 0.75, duration: dur })
              gsap.to('.adaptive-col-2', { x: '0%', duration: dur })
              gsap.to('.adaptive-col-3', { y: '0%', duration: dur })

              gsap.to('.adaptive-col-img-1 img', { scale: 1.25, duration: dur })
              gsap.to('.adaptive-col-img-2', {
                clipPath: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)',
                duration: dur,
              })
              gsap.to('.adaptive-col-img-2 img', { scale: 1, duration: dur })
            }

            // forward: phase 1 -> phase 2 (crossing 50%)
            if (progress >= 0.5 && currentPhase === 1) {
              currentPhase = 2
              gsap.to('.adaptive-col-2', { opacity: 0, scale: 0.75, duration: dur })
              gsap.to('.adaptive-col-3', { x: '0%', duration: dur })
              gsap.to('.adaptive-col-4', { y: '0%', duration: dur })

              gsap.to(
                '.adaptive-col-3 .adaptive-col-content-wrapper .adaptive-line span',
                { y: '-125%', duration: dur },
              )
              gsap.to(
                '.adaptive-col-3 .adaptive-col-content-wrapper-2 .adaptive-line span',
                { y: '0%', duration: dur, delay: swapDelay },
              )
            }

            // backward: phase >=1 -> rest (dropping below 25%)
            if (progress < 0.25 && currentPhase >= 1) {
              currentPhase = 0
              gsap.to('.adaptive-col-1', { opacity: 1, scale: 1, duration: dur })
              gsap.to('.adaptive-col-2', { x: '100%', duration: dur })
              gsap.to('.adaptive-col-3', { y: '100%', duration: dur })

              gsap.to('.adaptive-col-img-1 img', { scale: 1, duration: dur })
              gsap.to('.adaptive-col-img-2', {
                clipPath: 'polygon(0% 0%, 100% 0%, 100% 0%, 0% 0%)',
                duration: dur,
              })
              gsap.to('.adaptive-col-img-2 img', { scale: 1.25, duration: dur })
            }

            // backward: phase 2 -> phase 1 (dropping below 50%)
            if (progress < 0.5 && currentPhase === 2) {
              currentPhase = 1
              gsap.to('.adaptive-col-2', { opacity: 1, scale: 1, duration: dur })
              gsap.to('.adaptive-col-3', { x: '100%', duration: dur })
              gsap.to('.adaptive-col-4', { y: '100%', duration: dur })

              gsap.to(
                '.adaptive-col-3 .adaptive-col-content-wrapper .adaptive-line span',
                { y: '0%', duration: dur, delay: swapDelay },
              )
              gsap.to(
                '.adaptive-col-3 .adaptive-col-content-wrapper-2 .adaptive-line span',
                { y: '-125%', duration: dur },
              )
            }
          },
        })
      }, sectionRef)
    }

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
    <section className="adaptive" id="adaptive-learning" ref={sectionRef}>
      <div className="adaptive-wrapper">
        <div className="adaptive-wrapper">
          <div className="adaptive-col adaptive-col-1">
            <div className="adaptive-col-content">
              <div className="adaptive-col-content-wrapper">
                <h1>Watch every session build on the one before it</h1>
                <p>
                  Continuum keeps a running model of what a student knows, so
                  each lesson picks up exactly where the last one left off.
                </p>
              </div>
            </div>
          </div>

          <div className="adaptive-col adaptive-col-2">
            <div className="adaptive-col-img adaptive-col-img-1">
              <div className="adaptive-col-img-wrapper">
                <img
                  src="/images/claude.jpg"
                  alt="Dithered abstract texture of dark clouds, representing a student's early, still-forming understanding"
                />
              </div>
            </div>
            <div className="adaptive-col-img adaptive-col-img-2">
              <div className="adaptive-col-img-wrapper">
                <img
                  src="/images/gelly-fish.jpg"
                  alt="Textured jellyfish illustration, representing a student's understanding once it has taken shape"
                />
              </div>
            </div>
          </div>

          <div className="adaptive-col adaptive-col-3">
            <div className="adaptive-col-content-wrapper">
              <h1>It notices what&apos;s changed</h1>
              <p>
                A faster answer, a hesitation, a concept that finally clicks —
                Continuum tracks the signal most tutors miss.
              </p>
            </div>
            <div className="adaptive-col-content-wrapper-2">
              <h1>Then quietly updates the model</h1>
              <p>
                No repeated quizzes, no flashcards to grind through — just a
                picture of the student that sharpens with every exchange.
              </p>
            </div>
          </div>

          <div className="adaptive-col adaptive-col-4">
            <div className="adaptive-col-img">
              <div className="adaptive-col-img-wrapper">
                <img
                  src="/images/grass.jpg"
                  alt="Textured illustration of grass, representing the quiet, natural signal Continuum isolates from a session"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default AdaptiveLearning
