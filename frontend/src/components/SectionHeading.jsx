import './SectionHeading.css'

function SectionHeading({ children }) {
  return (
    <div className="section-heading-block">
      <h2 className="section-heading">{children}</h2>
    </div>
  )
}

export default SectionHeading
