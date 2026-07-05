# Continuum

**A tutor that never forgets.**

Continuum is an adaptive tutoring concept built around a persistent memory engine — it remembers every session, adapts its teaching strategy to how each student learns, tracks mastery per concept, and quietly prunes misconceptions once they're resolved, so nothing is ever explained twice.

🔗 **Live demo:** [continuum-eta-eight.vercel.app](https://continuum-eta-eight.vercel.app/)

> **Note:** This repo is the **frontend only** — a design/UX showcase for the full-stack project. It runs on mocked data so you can see the product experience end to end without a backend running. For the full-stack version (FastAPI + Cognee memory service), check the repo of the same name in my repos.

## What's in the demo

- **Landing page** — hero, adaptive learning scroll section, memory lifecycle, tech overview
- **`/login`, `/signup`** — split-screen auth flow with a dithered photo panel
- **`/adaptive-learning`, `/for-students`** — long-form editorial content pages
- **`/app`** — the actual product: a tutoring chat interface with
  - Live `recall()` / `remember()` / `improve()` / `forget()` memory-lifecycle events surfaced inline as the conversation happens
  - A mastery map, strategy performance panel, and misconception tracker
  - A collapsible dashboard that becomes a slide-in drawer on mobile

## Tech stack

React 19 · Vite · React Router · GSAP (ScrollTrigger, SplitText) · Lenis smooth scroll

## Running it locally

```bash
npm install
npm run dev
```

## Project structure

```
src/
  components/   shared UI (Nav, Footer, TextPage, auth icons, etc.)
  pages/        routed pages (Home, Login, SignUp, Session, ...)
  sections/     landing-page sections (Hero, AdaptiveLearning, ...)
  lib/          smooth-scroll setup
```
