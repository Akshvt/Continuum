import TextPage from '../components/TextPage'

const SECTIONS = [
  {
    number: '01',
    title: 'A tutor that remembers you',
    category: 'Continuity',
    paragraphs: [
      "Walk into most tutoring tools cold every session and you spend the first ten minutes re-establishing context that should never have been lost — what you already know, what confused you last time, where you left off. Continuum starts exactly where the last session ended, because it never actually forgot.",
      "That continuity compounds. A concept you struggled with three weeks ago quietly informs how something related is explained today, without you having to bring it up yourself. The tutor's memory is doing work in the background so your own working memory doesn't have to.",
    ],
  },
  {
    number: '02',
    title: 'Explanations that fit how you think',
    category: 'Personalization',
    paragraphs: [
      "Not everyone learns the same concept the same way. Some people need the analogy first and the formula second; others want to try the problem and get corrected. Continuum has watched which style has actually worked for you, specifically, and leads with that — not a generic default written for an average student who doesn't exist.",
      "If an explanation isn't landing, that's information too. The next attempt comes from a different angle automatically, because a repeated miss on the same style is itself a signal worth acting on.",
    ],
  },
  {
    number: '03',
    title: 'No repeating yourself',
    category: 'Less friction',
    paragraphs: [
      "You shouldn't have to re-explain your own confusion twice. If you've already worked through why negative exponents trip you up, that understanding carries forward — the tutor won't re-teach it from scratch next time it's relevant, and it won't need you to remind it either.",
      "The same goes for what you've already mastered. Once something is solid, Continuum stops circling back to double-check it out of caution. Your time goes toward what's actually still uncertain, not toward proving again what you've already shown you know.",
    ],
  },
  {
    number: '04',
    title: 'Progress you can actually see',
    category: 'Transparency',
    paragraphs: [
      "Your mastery on every concept is a visible number, not a guess you have to trust. You can see exactly what's solid, what's still developing, and what's blocking the next topic — the same information the tutor is using to decide what to teach you next.",
      "Nothing about the reasoning is hidden. If the tutor picks a particular strategy for you, or tells you a concept needs more work before you move on, you can ask why — and get an actual answer grounded in your own history, not a black box shrugging back at you.",
    ],
  },
]

function ForStudents() {
  return <TextPage eyebrow="What Continuum is like to use" sections={SECTIONS} />
}

export default ForStudents
