import TextPage from '../components/TextPage'

const SECTIONS = [
  {
    number: '01',
    title: 'Sensing what a student needs',
    category: 'Signal detection',
    paragraphs: [
      "Most tutoring software waits for a quiz to tell it something's wrong. Continuum doesn't wait. It reads the ordinary texture of a session — a faster answer than usual, a long pause before a response, a question rephrased twice before it lands, the same small mistake showing up in a new context. None of these are quiz scores, but together they're a clearer signal than one ever was.",
      "That signal gets attached to the concept it belongs to, not just the session it happened in. A hesitation on today's problem means something different if the same hesitation showed up on a related concept two weeks ago. Continuum is the layer that remembers both moments long enough to notice they're connected.",
    ],
  },
  {
    number: '02',
    title: 'Choosing how to teach it',
    category: 'Strategy selection',
    paragraphs: [
      "There isn't one right way to explain a quadratic formula, and Continuum doesn't pretend there is. It holds a small set of teaching strategies — analogy-first, worked-example, question-first — and tracks how well each one has actually landed with this student, on this kind of concept, historically. The strategy it reaches for is the one with the best track record, not the first one on a list.",
      "That choice is never hidden. Every explanation is tagged with the strategy behind it, and a student can ask why that approach was chosen for them today. The reasoning is a recalled success rate, not a mood — which means it can be inspected, questioned, and overridden, instead of just trusted.",
    ],
  },
  {
    number: '03',
    title: 'Watching it stick — or not',
    category: 'Mastery tracking',
    paragraphs: [
      "Mastery isn't a single test score in Continuum's model — it's a running estimate that moves with every relevant answer, up when something clicks, down when a concept that seemed solid starts to wobble. Each concept carries its own number, visible at a glance, colored by how confident the system currently is.",
      "That number is also a gate. A student can't wander into a topic that depends on shaky footing elsewhere — Continuum will say so plainly, and point at exactly which prerequisite needs more work first. Sequencing isn't a fixed curriculum order; it's whatever the student's own mastery map says is ready next.",
    ],
  },
  {
    number: '04',
    title: 'Letting go of what’s resolved',
    category: 'Memory pruning',
    paragraphs: [
      "Most systems that claim to “remember everything” end up drowning in their own history — every old mistake preserved forever, cluttering whatever comes next. Continuum does the opposite on purpose. Once a misconception has been genuinely resolved, demonstrated correctly across more than one context, it's pruned from active memory.",
      "This isn't forgetting for its own sake — it's the same discipline a good tutor practices instinctively, choosing not to bring up a mistake a student has clearly outgrown. What's left behind is a lean, current model of exactly where a student stands today, not an ever-growing transcript of everywhere they've been.",
    ],
  },
]

function AdaptiveLearningPage() {
  return <TextPage eyebrow="How Continuum adapts" sections={SECTIONS} />
}

export default AdaptiveLearningPage
