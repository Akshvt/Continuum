# Continuum: The Tutor That Never Forgets

Every AI tutor app claims to "personalize," but in reality, they mostly reset to zero every session. Continuum is different. It is an agentic tutoring system that actually remembers a specific student across weeks, months, and years—like a real teacher who has been with them all year. It visibly gets better at teaching them the longer it runs.

## 🌟 The Concept: "Never Lose the Plot"

Continuum leverages a deeply integrated memory and knowledge graph system to track exactly what a student knows, what they struggle with, and how they learn best. 

Instead of generating generic questions, Continuum continuously adapts its approach based on four core cognitive operations powered by Cognee:

- **`remember()`**: Every time a student attempts a concept, you feed it the outcome. *(e.g., "Riya got the variables question wrong because she thought they were immutable like literals, and we used a question-first explanation.")*
- **`recall()`**: When the tutor needs to decide what to teach next, it asks: *"What prerequisites has this student struggled with that are connected to what they're stuck on now?"* A graph traversal surfaces the exact weak link instead of guessing.
- **`improve()`**: After each session, it re-weights the graph based on which teaching strategy actually worked. Explanations that produced real understanding (e.g., analogies vs. worked examples) get reinforced, and ones that flopped get deprioritized for that specific student.
- **`forget()`**: Once a misconception is genuinely fixed and mastery is confirmed (e.g., 3 consecutive correct answers), the system prunes that outdated wrong-answer history. This stops the resolved misconception from shaping how the tutor talks to them, without wiping the rest of their permanent learning record.

## 🏗️ Architecture & Cognee Integration

Continuum's intelligence is driven by **Cognee Cloud**, functioning as the semantic and relational memory engine for the application.

### How it works:
1. **Curriculum Graph**: The backend seeds a directed acyclic graph (DAG) of programming concepts (e.g., `literals_and_values` → `variables` → `data_types`).
2. **Student Identity**: Students are tracked via deterministic hashing (`student_id`). No complex auth needed.
3. **Adaptive Question Generation**: 
   - The backend uses `recall()` to query Cognee for the student's active misconceptions and the current concept's prerequisites.
   - It queries Cognee to determine the best `teaching_style` for the student.
   - It feeds this context to an LLM (OpenAI) to generate a highly targeted, format-diverse question.
4. **Grading & Memory Logging**:
   - The student answers, and the LLM grades the answer.
   - If wrong, a specific misconception is identified and logged via `remember()`.
   - If right, mastery increases. If 3 consecutive correct answers are recorded on a concept, the system triggers `forget()` to prune the outdated misconceptions.
5. **Strategy Refinement**: The system runs `improve()` to optimize the structural graph weights, adjusting the preferred teaching strategy based on recent success rates.

## 💻 Tech Stack

### Frontend
- **React.js** (Vite) for rapid, component-based UI development.
- **React Router** for seamless single-page application navigation.
- **Vanilla CSS** with a premium, minimalist design system (glassmorphism, subtle micro-animations, dark-mode aesthetics).
- **Vercel** for lightning-fast edge deployment.

### Backend
- **FastAPI (Python)** for high-performance, async API routing.
- **OpenAI API** for intelligent question generation, grading, and misconception extraction.
- **Cognee (Cloud)** for all graph memory operations (`remember`, `recall`, `improve`, `forget`).
- **Render** for reliable backend hosting.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API Key
- Cognee API Key (Cloud)

### Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/Akshvt/Continuum.git
cd Continuum
```

**2. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file based on the template
cp .env.example .env
# Add your OPENAI_API_KEY and COGNEE_API_KEY to .env

# Run the FastAPI server
uvicorn main:app --reload --port 8000
```

**3. Frontend Setup**
```bash
cd frontend
npm install

# Create a .env.local file
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Start the Vite dev server
npm run dev
```

**4. Explore**
Open `http://localhost:5173` in your browser. Enter a name on the Entry screen to begin a self-improving tutoring session!
