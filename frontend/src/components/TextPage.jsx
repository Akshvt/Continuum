import { useEffect } from 'react'
import { initSmoothScroll, destroySmoothScroll } from '../lib/smoothScroll'
import Footer from './Footer'
import Nav from './Nav'
import './TextPage.css'

function TextPage({ eyebrow, sections }) {
  useEffect(() => {
    initSmoothScroll()
    return () => destroySmoothScroll()
  }, [])

  return (
    <div className="page-frame">
      <Nav />
      <main>
        <div className="text-page">
          <p className="text-page-eyebrow">{eyebrow}</p>

          {sections.map((section) => (
            <section className="ed-section" key={section.number}>
              <div className="ed-number">{section.number}</div>
              <div className="ed-content">
                <div className="ed-rule" />
                <div className="ed-heading-col">
                  <h2>{section.title}</h2>
                  <span className="ed-category">{section.category}</span>
                </div>
                <div className="ed-body-col">
                  {section.paragraphs.map((paragraph, index) => (
                    <p key={index}>{paragraph}</p>
                  ))}
                </div>
              </div>
            </section>
          ))}
        </div>
        <div className="footer-revealer" />
      </main>
      <Footer />
    </div>
  )
}

export default TextPage
