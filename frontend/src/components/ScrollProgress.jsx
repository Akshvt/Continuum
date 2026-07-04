import { useEffect, useRef } from 'react'
import { getLenis } from '../lib/smoothScroll'
import './ScrollProgress.css'

const HIDE_NEAR_BOTTOM_THRESHOLD = 0.97
const IDLE_DELAY = 900

function ScrollProgress() {
  const rootRef = useRef(null)
  const trackRef = useRef(null)
  const thumbRef = useRef(null)

  useEffect(() => {
    let idleTimer

    const updateThumb = (progress) => {
      const root = rootRef.current
      const track = trackRef.current
      const thumb = thumbRef.current
      if (!root || !track || !thumb) return

      const trackHeight = track.clientHeight
      const scrollHeight = document.documentElement.scrollHeight
      const rawHeight = (window.innerHeight / scrollHeight) * trackHeight
      const thumbHeight = Math.min(110, Math.max(36, rawHeight * 0.45))
      const maxTop = trackHeight - thumbHeight

      thumb.style.height = `${thumbHeight}px`
      thumb.style.top = `${progress * maxTop}px`
      root.classList.toggle(
        'is-hidden',
        progress >= HIDE_NEAR_BOTTOM_THRESHOLD,
      )

      // Only visible while actively scrolling — reset the idle fade-out
      // timer on every update instead of letting it sit on screen at rest.
      root.classList.remove('is-idle')
      clearTimeout(idleTimer)
      idleTimer = setTimeout(() => root.classList.add('is-idle'), IDLE_DELAY)
    }

    const onScroll = (lenis) => updateThumb(lenis.progress)
    const onResize = () => {
      const lenis = getLenis()
      updateThumb(lenis ? lenis.progress : 0)
    }

    // App's own effect wires up Lenis in the same mount pass, so it may not
    // exist yet on this component's first render — poll a couple of frames
    // until it does, then bind the real listener.
    let lenis = null
    let cancelled = false
    let raf
    const bind = () => {
      lenis = getLenis()
      if (lenis) {
        lenis.on('scroll', onScroll)
        updateThumb(lenis.progress)
      } else if (!cancelled) {
        raf = requestAnimationFrame(bind)
      }
    }
    bind()

    window.addEventListener('resize', onResize)

    return () => {
      cancelled = true
      if (raf) cancelAnimationFrame(raf)
      clearTimeout(idleTimer)
      if (lenis) lenis.off('scroll', onScroll)
      window.removeEventListener('resize', onResize)
    }
  }, [])

  return (
    <div className="scroll-progress" ref={rootRef} aria-hidden="true">
      <div className="scroll-progress-track" ref={trackRef}>
        <div className="scroll-progress-thumb" ref={thumbRef} />
      </div>
    </div>
  )
}

export default ScrollProgress
