# Sports League Scoreboard - Frontend Application

A responsive web application built with React, TypeScript, and Tailwind CSS for managing amateur sports leagues, scheduling fixtures, recording live scores pitchside, and computing real-time standings using the 3-1-0 points system (3 for win, 1 for draw, 0 for loss).

## Architecture & Centralized Service Layer

All backend operations are centralized in `src/services/`:
- `IScoreboardService` (`src/services/types.ts`): Interface declaring all operations for leagues, clubs, matches, live score updates, standings, and pub/sub event subscriptions.
- `MockScoreboardService` (`src/services/mockService.ts`): Fully in-browser implementation with persistent `localStorage` and real-time subscription events.
- `HttpScoreboardService` (`src/services/apiService.ts`): REST + Server-Sent Events (SSE) implementation ready for deployment against a live backend.
- `src/services/index.ts`: Singleton service factory defaulting to `MockScoreboardService`.

## Features
- **Automatic League Standings**: Calculated dynamically with standard amateur points rules (Win: 3pts, Draw: 1pt, Loss: 0pt). Includes deterministic tie-breaking (Points > Goal Difference > Goals For > Head-to-Head > Team Name) and 5-match form guides.
- **Provisional Live Standings Toggle**: Optional toggle to preview standings impact during active in-progress matches.
- **Pitchside Scorekeeper**: Mobile-first console featuring large touch steppers (+1 / -1), match periods (1st Half, Halftime, 2nd Half, Full Time), match clock minute adjustments, and match event logging.
- **Match Lifecycle & Validation**: Strict state progression (`SCHEDULED` -> `IN_PROGRESS` -> `FINISHED`). Requires confirmation before finalizing and locking scores.
- **Match Scheduling & Team Registration**: Modal forms with validations (e.g. preventing a team from playing against itself).

## Getting Started

### Development
```bash
npm install
npm run dev
```

### Build & Preview
```bash
npm run build
npm run preview -- --host 127.0.0.1
```

### Running Unit Tests
```bash
npx vitest run
```
