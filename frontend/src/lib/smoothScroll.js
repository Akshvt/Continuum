import Lenis from 'lenis'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

let lenis = null
let rafCallback = null

/**
 * Wires Lenis smooth scroll into GSAP's ticker so both stay on the same
 * rAF loop instead of drifting apart on two independent loops.
 */
export function initSmoothScroll() {
  if (lenis) return lenis

  lenis = new Lenis({
    autoRaf: false,
  })

  lenis.on('scroll', ScrollTrigger.update)

  rafCallback = (time) => {
    lenis.raf(time * 1000)
  }
  gsap.ticker.add(rafCallback)
  gsap.ticker.lagSmoothing(0)

  return lenis
}

export function destroySmoothScroll() {
  if (rafCallback) {
    gsap.ticker.remove(rafCallback)
    rafCallback = null
  }
  if (lenis) {
    lenis.destroy()
    lenis = null
  }
}

export function getLenis() {
  return lenis
}
