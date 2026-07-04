import { useEffect } from 'react'
import { initSmoothScroll, destroySmoothScroll } from '../lib/smoothScroll'
import Footer from '../components/Footer'
import Nav from '../components/Nav'
import ScrollProgress from '../components/ScrollProgress'
import SectionHeading from '../components/SectionHeading'
import Hero from '../sections/Hero'
import AdaptiveLearning from '../sections/AdaptiveLearning'
import MemoryLifecycle from '../sections/MemoryLifecycle'
import TechSystem from '../sections/TechSystem'

function Home() {
  useEffect(() => {
    initSmoothScroll()
    return () => destroySmoothScroll()
  }, [])

  return (
    <div className="page-frame">
      <ScrollProgress />
      <Nav />
      <main>
        <Hero />
        <SectionHeading>Why this tutor is different</SectionHeading>
        <AdaptiveLearning />
        <MemoryLifecycle />
        <TechSystem />
        {/* Remaining sections are added one at a time, in order, as each is approved. */}
        <div className="footer-revealer" />
      </main>
      <Footer />
    </div>
  )
}

export default Home
