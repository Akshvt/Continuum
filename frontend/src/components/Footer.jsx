import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SplitText } from 'gsap/SplitText'
import './Footer.css'

gsap.registerPlugin(ScrollTrigger, SplitText)

const ASCII_CHARS = ' .:-=+*#%@'
const FONT_SIZE = 27
const CELL_SIZE = 20
const ASCII_COLUMNS = 100
const DPR = 2

const CHAR_COLOR = '#1a1a1a'
const HOVER_COLOR = '#0a0a0a'
const HOVER_CHAR_COLOR = '#ffffff'

const HOVER_RADIUS = 8
const CLUSTER_SIZE = 10
const HIGHLIGHT_LIFETIME = 300

const PARALLAX_STRENGTH = 20
const PARALLAX_EASE = 0.05

// Our source images are soft illustrations with a near-white background
// (~0.95-0.97 brightness) but a lot of lit skin tone that's still fairly
// bright (up to ~0.85-0.90) — a naive "background = lightest chars in the
// ramp" cutoff dropped most of the hand along with the real background.
// Threshold on actual sampled brightness instead so only the true
// background gets skipped.
const BACKGROUND_BRIGHTNESS_THRESHOLD = 0.9

function Footer() {
  const footerRef = useRef(null)

  useEffect(() => {
    const footer = footerRef.current
    if (!footer) return undefined

    const reduceMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches

    let cancelled = false
    const handRafIds = []
    let parallaxRafId = null

    // ---- ASCII-art rendering: sample each hand image down to a small
    // brightness grid, map brightness to a character ramp, and skip the
    // lightest ("background") cells so only the hand silhouette prints. ----
    const sampleImagePixels = (image, gridRows) => {
      const canvas = document.createElement('canvas')
      canvas.width = ASCII_COLUMNS
      canvas.height = gridRows
      const sampleCtx = canvas.getContext('2d')
      sampleCtx.drawImage(image, 0, 0, ASCII_COLUMNS, gridRows)
      return sampleCtx.getImageData(0, 0, ASCII_COLUMNS, gridRows).data
    }

    const pixelBrightness = (pixels, pixelOffset) =>
      (pixels[pixelOffset] * 0.299 +
        pixels[pixelOffset + 1] * 0.587 +
        pixels[pixelOffset + 2] * 0.114) /
      255

    const brightnessToCharIndex = (brightness) =>
      Math.min(
        ASCII_CHARS.length - 1,
        Math.floor((1 - brightness) * ASCII_CHARS.length),
      )

    const buildCells = (image) => {
      const rows = Math.round(
        ASCII_COLUMNS / (image.naturalWidth / image.naturalHeight),
      )
      const pixels = sampleImagePixels(image, rows)
      const cells = new Map()

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < ASCII_COLUMNS; col++) {
          const brightness = pixelBrightness(
            pixels,
            (row * ASCII_COLUMNS + col) * 4,
          )
          if (brightness >= BACKGROUND_BRIGHTNESS_THRESHOLD) continue

          cells.set(`${col},${row}`, {
            col,
            row,
            char: ASCII_CHARS[brightnessToCharIndex(brightness)],
            highlightEndTime: 0,
          })
        }
      }

      return { rows, cells }
    }

    const setupHand = (image) => {
      const { rows, cells } = buildCells(image)
      const cellList = [...cells.values()]

      const canvas = image.closest('.footer-hand-img').querySelector('canvas')
      canvas.width = ASCII_COLUMNS * CELL_SIZE * DPR
      canvas.height = rows * CELL_SIZE * DPR

      const handCtx = canvas.getContext('2d')
      handCtx.setTransform(DPR, 0, 0, DPR, 0, 0)
      handCtx.font = `${FONT_SIZE}px monospace`
      handCtx.textAlign = 'center'
      handCtx.textBaseline = 'alphabetic'

      const metrics = handCtx.measureText('X')
      const glyphHeight =
        metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent
      const baselineOffset =
        CELL_SIZE / 2 + glyphHeight / 2 - metrics.actualBoundingBoxDescent

      const canvasWidth = ASCII_COLUMNS * CELL_SIZE
      const canvasHeight = rows * CELL_SIZE

      const render = () => {
        if (cancelled) return
        const now = Date.now()
        handCtx.clearRect(0, 0, canvasWidth, canvasHeight)

        for (const cell of cellList) {
          const x = cell.col * CELL_SIZE
          const y = cell.row * CELL_SIZE
          const isHighlighted = cell.highlightEndTime > now

          if (isHighlighted) {
            handCtx.fillStyle = HOVER_COLOR
            handCtx.fillRect(x, y, CELL_SIZE, CELL_SIZE)
          }

          handCtx.fillStyle = isHighlighted ? HOVER_CHAR_COLOR : CHAR_COLOR
          handCtx.fillText(cell.char, x + CELL_SIZE / 2, y + baselineOffset)
        }

        handRafIds.push(requestAnimationFrame(render))
      }
      render()

      return { canvas, cells, cellList, rows }
    }

    // ---- Hover "ember" effect: light up a random-walk cluster of cells
    // around the closest one to the cursor, each fading out on its own
    // staggered timer. ----
    const highlightCluster = (cells, startCell) => {
      const now = Date.now()
      startCell.highlightEndTime = now + HIGHLIGHT_LIFETIME

      const steps = Math.floor(Math.random() * CLUSTER_SIZE) + 1
      const litCells = [startCell]
      let current = startCell

      for (let step = 0; step < steps; step++) {
        const neighbours = []
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            if (dx === 0 && dy === 0) continue
            const neighbour = cells.get(
              `${current.col + dx},${current.row + dy}`,
            )
            if (neighbour && !litCells.includes(neighbour)) {
              neighbours.push(neighbour)
            }
          }
        }
        if (neighbours.length === 0) break

        const next = neighbours[Math.floor(Math.random() * neighbours.length)]
        next.highlightEndTime = now + HIGHLIGHT_LIFETIME + step * 10
        litCells.push(next)
        current = next
      }
    }

    const hands = []

    const hoverHand = (hand, clientX, clientY) => {
      const rect = hand.canvas.getBoundingClientRect()
      const mouseCol = ((clientX - rect.left) / rect.width) * ASCII_COLUMNS
      const mouseRow = ((clientY - rect.top) / rect.height) * hand.rows

      let closest = null
      let closestDist = Infinity
      for (const cell of hand.cellList) {
        const dx = mouseCol - cell.col
        const dy = mouseRow - cell.row
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < closestDist) {
          closestDist = dist
          closest = cell
        }
      }

      if (closest && closestDist <= HOVER_RADIUS) {
        highlightCluster(hand.cells, closest)
      }
    }

    const onHandsMouseMove = (event) => {
      hands.forEach((hand) => hoverHand(hand, event.clientX, event.clientY))
    }
    window.addEventListener('mousemove', onHandsMouseMove)

    const createdCanvases = []
    const imageLoadListeners = []

    footer.querySelectorAll('img.ascii-hand').forEach((image) => {
      const canvas = document.createElement('canvas')
      image.closest('.footer-hand-img').appendChild(canvas)
      createdCanvases.push(canvas)

      const start = () => {
        if (cancelled) return
        hands.push(setupHand(image))
      }
      if (image.complete && image.naturalWidth) {
        start()
      } else {
        image.addEventListener('load', start)
        imageLoadListeners.push({ image, start })
      }
    })

    // ---- Parallax drift: mouse position relative to the footer eases
    // toward a drift value, applied as opposing translate+scale on each
    // hand wrapper. `reveal.left/right` is also folded into this same
    // transform so the scroll-triggered slide-in/out (below) and the
    // parallax offset compose into one transform per frame. ----
    const handWrappers = [...footer.querySelectorAll('.footer-hand-img')]
    const parallaxScale = 1 + (PARALLAX_STRENGTH * 2) / 200
    const pointer = { x: 0, y: 0 }
    const drift = { x: 0, y: 0 }
    const reveal = { left: -125, right: 125 }

    const setPointerTarget = (clientX, clientY) => {
      const rect = footer.getBoundingClientRect()
      pointer.x =
        ((clientX - rect.left) / rect.width - 0.5) * PARALLAX_STRENGTH * 2
      pointer.y =
        ((clientY - rect.top) / rect.height - 0.5) * PARALLAX_STRENGTH * 2
    }

    const renderParallax = () => {
      if (cancelled) return
      drift.x += (pointer.x - drift.x) * PARALLAX_EASE
      drift.y += (pointer.y - drift.y) * PARALLAX_EASE

      handWrappers.forEach((wrapper, i) => {
        const direction = i === 0 ? 1 : -1
        const revealX = i === 0 ? reveal.left : reveal.right
        const x = drift.x * direction
        const y = -drift.y
        wrapper.style.transform = `translate(calc(${x}px + ${revealX}%), ${y}px) scale(${parallaxScale})`
      })

      parallaxRafId = requestAnimationFrame(renderParallax)
    }
    renderParallax()

    const onFooterMouseMove = (event) =>
      setPointerTarget(event.clientX, event.clientY)
    window.addEventListener('mousemove', onFooterMouseMove)

    // ---- Scroll-triggered reveal: heading chars/content lines slide up
    // into place while the hands slide in from the sides (reveal -> 0),
    // reversing on scroll-back. ----
    const ctx = gsap.context(() => {
      const headings = footer.querySelectorAll('.footer-header h1')
      const headingChars = []
      headings.forEach((heading) => {
        const split = SplitText.create(heading, {
          type: 'chars',
          charsClass: 'char',
        })
        headingChars.push(...split.chars)
      })
      gsap.set(headingChars, { position: 'relative', yPercent: 125 })

      const contentElements = footer.querySelectorAll(
        '.footer-links a, .footer-text p',
      )
      const contentLines = []
      contentElements.forEach((element) => {
        const split = SplitText.create(element, {
          type: 'lines',
          mask: 'lines',
          linesClass: 'line',
        })
        contentLines.push(...split.lines)
      })
      gsap.set(contentLines, { yPercent: 100 })

      if (reduceMotion) {
        gsap.set(reveal, { left: 0, right: 0 })
        gsap.set(headingChars, { yPercent: 0 })
        gsap.set(contentLines, { yPercent: 0 })
        return
      }

      const animateIn = () => {
        gsap.to(reveal, {
          left: 0,
          right: 0,
          duration: 1,
          ease: 'power3.out',
          overwrite: true,
        })
        gsap.to(headingChars, {
          yPercent: 0,
          duration: 1,
          ease: 'power3.out',
          stagger: { each: 0.04, from: 'center' },
          overwrite: true,
        })
        gsap.to(contentLines, {
          yPercent: 0,
          duration: 1,
          ease: 'power3.out',
          stagger: 0.08,
          overwrite: true,
        })
      }

      const animateOut = () => {
        gsap.to(reveal, {
          left: -125,
          right: 125,
          duration: 0.4,
          ease: 'power2.in',
          overwrite: true,
        })
        gsap.to(headingChars, {
          yPercent: 125,
          duration: 0.4,
          ease: 'power2.in',
          stagger: { each: 0.01, from: 'center' },
          overwrite: true,
        })
        gsap.to(contentLines, {
          yPercent: 100,
          duration: 0.4,
          ease: 'power2.in',
          stagger: 0.02,
          overwrite: true,
        })
      }

      // .footer-revealer is a sibling in <main>, outside this component's
      // own DOM subtree — resolve it directly rather than as a selector
      // string, since gsap.context scopes string lookups to footerRef.
      const revealer = document.querySelector('.footer-revealer')

      ScrollTrigger.create({
        trigger: revealer,
        start: 'top 50%',
        onEnter: animateIn,
      })
      ScrollTrigger.create({
        trigger: revealer,
        start: 'top 85%',
        onLeaveBack: animateOut,
      })
    }, footerRef)

    return () => {
      cancelled = true
      handRafIds.forEach((id) => cancelAnimationFrame(id))
      if (parallaxRafId) cancelAnimationFrame(parallaxRafId)
      window.removeEventListener('mousemove', onHandsMouseMove)
      window.removeEventListener('mousemove', onFooterMouseMove)
      imageLoadListeners.forEach(({ image, start }) =>
        image.removeEventListener('load', start),
      )
      createdCanvases.forEach((canvas) => canvas.remove())
      ctx.revert()
    }
  }, [])

  return (
    <footer className="site-footer" ref={footerRef}>
      <div className="footer-images">
        <div className="footer-hand-img">
          <img className="ascii-hand" src="/images/left-hand.jpg" alt="" />
        </div>
        <div className="footer-hand-img">
          <img className="ascii-hand" src="/images/right-hand.jpg" alt="" />
        </div>
      </div>

      <div className="footer-foreground">
        <div className="footer-content">
          <nav className="footer-links">
            <a href="#top">Home</a>
            <a href="#adaptive-learning">Adaptive Learning</a>
            <a href="#memory-lifecycle">Memory</a>
            <a href="#contact">Contact</a>
          </nav>

          <div className="footer-text">
            <p>
              Continuum remembers what a student knows, adapts to how they
              learn, and quietly forgets what no longer matters — so every
              session builds on the last.
            </p>
          </div>
        </div>

        <div className="footer-header">
          <h1>Keep</h1>
          <h1>Learning</h1>
        </div>
      </div>
    </footer>
  )
}

export default Footer
