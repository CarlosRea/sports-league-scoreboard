# Sports League Scoreboard - System Specification

## 1. Executive Summary

The **Sports League Scoreboard** is a modern, responsive web application designed for amateur sports leagues, community tournaments, and recreational clubs (such as amateur soccer, futsal, field hockey, rugby, etc.). 

The platform simplifies league operations by providing:
- Rapid league and team onboarding.
- Fixture creation and match scheduling.
- A mobile-friendly, pitchside live scorekeeper interface.
- Instant match finalization workflows.
- Real-time, automated calculation of league standings based on the standard amateur points system:
  - **Win**: 3 points
  - **Draw / Tie**: 1 point
  - **Loss**: 0 points
- Clear tie-breaking mechanics (Goal Difference, Goals For, Head-to-Head, Team Name).

---

## 2. System Architecture & Tech Stack

```
+-------------------------------------------------------------+
|                      Client Layer                           |
|  - Public Dashboard (Standings Table, Fixtures & Results)   |
|  - Pitchside Scorekeeper UI (Mobile / Tablet Optimized)     |
|  - Admin Dashboard (Leagues, Teams, Schedules)              |
+------------------------------+------------------------------+
                               | HTTPS / WSS / SSE
+------------------------------v------------------------------+
|                     Application Layer                       |
|  - Next.js / Node.js API Service                            |
|  - Input Validation & Sanitization (Zod schemas)            |
|  - Standings Calculation Engine                             |
|  - Real-time Broadcast Hub (SSE / WebSockets)               |
|  - Auth & Role-Based Access Control (Admin vs Scorekeeper)  |
+------------------------------+------------------------------+
                               | Parameterized SQL / ORM
+------------------------------v------------------------------+
|                     Persistence Layer                       |
|  - Relational Database (PostgreSQL / SQLite with Prisma)    |
|  - ACID-compliant transactions for match result locking     |
+-------------------------------------------------------------+
```

### 2.1 Recommended Tech Stack
- **Frontend**: Next.js (React 19 / React 18) with TypeScript and Tailwind CSS.
- **Backend / API**: Next.js Server Actions / Route Handlers or Express/Fastify REST API.
- **Database / ORM**: PostgreSQL (production) or SQLite (local development/testing) managed via Prisma or Drizzle ORM.
- **Real-Time Updates**: Server-Sent Events (SSE) or WebSockets for live score propagation to public viewers.
- **Validation**: Zod for end-to-end schema validation and type safety.
- **Testing**: Vitest / Jest for unit and integration testing, Playwright for E2E flows.

---

## 3. Data Models & Entity Relationships

```
+--------------------+           1:N          +--------------------+
|       League       |----------------------->|        Team        |
+--------------------+                        +--------------------+
| id (UUID / Int PK) |                        | id (UUID / Int PK) |
| name (VARCHAR)     |                        | league_id (FK)     |
| sport_type         |                        | name (VARCHAR)     |
| points_win = 3     |                        | short_name (CHAR)  |
| points_draw = 1    |                        | logo_url (NULLABLE)|
| points_loss = 0    |                        +--------------------+
+--------------------+                                  |
          | 1:N                                         |
          |                                             |
          v                                             | (Home / Away)
+--------------------+                                  |
|       Match        |<---------------------------------+
+--------------------+
| id (UUID / Int PK) |
| league_id (FK)     |
| home_team_id (FK)  |
| away_team_id (FK)  |
| round / matchday   |
| scheduled_at       |
| status             | (SCHEDULED | IN_PROGRESS | FINISHED | CANCELLED)
| home_score (INT)   |
| away_score (INT)   |
| current_period     | (Pre-match, 1st Half, Halftime, 2nd Half, Full Time)
| started_at         |
| finished_at        |
+--------------------+
          | 1:N
          v
+--------------------+
|     MatchEvent     |
+--------------------+
| id (UUID / Int PK) |
| match_id (FK)      |
| event_type         | (SCORE_UPDATE, PERIOD_CHANGE, NOTE)
| minute / timestamp |
| home_score_snapshot|
| away_score_snapshot|
| note (VARCHAR)     |
+--------------------+
```

### 3.1 Schema Definitions (TypeScript / Prisma-compatible)

#### League
- `id`: `String` (UUIDv4) or `Int` (Autoincrement Primary Key).
- `name`: `String` (e.g., "Metro Amateur Premier League").
- `season`: `String` (e.g., "2026/2027").
- `pointsWin`: `Int` (Default: `3`).
- `pointsDraw`: `Int` (Default: `1`).
- `pointsLoss`: `Int` (Default: `0`).
- `createdAt`: `DateTime`.
- `updatedAt`: `DateTime`.

#### Team
- `id`: `String` (UUIDv4) or `Int` (PK).
- `leagueId`: `String` (Foreign Key referencing `League.id`).
- `name`: `String` (Unique per league, e.g., "Riverside FC").
- `shortName`: `String` (2-4 characters, e.g., "RFC").
- `logoUrl`: `String?` (Optional sanitized URL or local icon path).
- `createdAt`: `DateTime`.

#### Match
- `id`: `String` (UUIDv4) or `Int` (PK).
- `leagueId`: `String` (Foreign Key referencing `League.id`).
- `homeTeamId`: `String` (Foreign Key referencing `Team.id`).
- `awayTeamId`: `String` (Foreign Key referencing `Team.id`).
- `matchday`: `Int` (Round number, e.g., 1, 2, 3).
- `scheduledAt`: `DateTime` (Kick-off date & time).
- `status`: `Enum ('SCHEDULED', 'IN_PROGRESS', 'FINISHED', 'CANCELLED')`. Default: `'SCHEDULED'`.
- `homeScore`: `Int` (Default: `0`, >= 0).
- `awayScore`: `Int` (Default: `0`, >= 0).
- `currentPeriod`: `String` (e.g., "Not Started", "1st Half", "Half Time", "2nd Half", "Finished").
- `startedAt`: `DateTime?` (Timestamp when match moved to `IN_PROGRESS`).
- `finishedAt`: `DateTime?` (Timestamp when match moved to `FINISHED`).
- `createdAt`: `DateTime`.
- `updatedAt`: `DateTime`.

#### MatchEvent (Audit & Score Log)
- `id`: `String` (UUIDv4) or `Int` (PK).
- `matchId`: `String` (Foreign Key referencing `Match.id`).
- `type`: `Enum ('GOAL_HOME', 'GOAL_AWAY', 'CORRECTION', 'PERIOD_START', 'MATCH_END')`.
- `elapsedMinutes`: `Int?` (Elapsed match minute).
- `homeScoreAfter`: `Int`.
- `awayScoreAfter`: `Int`.
- `recordedAt`: `DateTime` (Default: `now()`).

---

## 4. Functional Requirements & Core Business Logic

### 4.1 League and Team Management
1. **League Setup**:
   - Create a league with a name, season/year, and scoring configuration (default: 3 points win, 1 point draw, 0 points loss).
2. **Team Registration**:
   - Add teams with unique names within the league.
   - Prevent duplicate team names inside the same league.
   - Minimum 2 teams to schedule matches.

### 4.2 Match Lifecycle & Validation
Matches follow a strict state machine:

```
    [ SCHEDULED ]
          |
          | startMatch()
          v
    [ IN_PROGRESS ] <--- (enterScore / updateScore)
          |
          | finishMatch()
          v
     [ FINISHED ]
          |
          +--> (Automatically triggers recalculation of Standings)
```

#### Validation Rules:
- A team cannot play against itself (`homeTeamId != awayTeamId`).
- Both teams must belong to the same `leagueId`.
- Scores must be non-negative integers (`score >= 0`).
- A match in `SCHEDULED` status can be started or edited.
- Scores can be actively incremented, decremented, or edited when `status == IN_PROGRESS`.
- When `finishMatch()` is called:
  - The match status changes to `FINISHED`.
  - `finishedAt` timestamp is recorded.
  - The match score is officially marked as final.
  - League standings table updates instantly.
- Re-opening or correcting a `FINISHED` match is restricted to authorized League Admins and immediately triggers recalculation of standings.

### 4.3 Pitchside Scorekeeper Interface
Designed specifically for mobile and touch devices on the sideline:
- Large, high-contrast tap targets (+1 / -1 buttons) for both Home and Away teams.
- Direct score input keypad for rapid corrections.
- Match clock / status toggle ("Start Match", "Half Time", "Resume", "End Match").
- Confirmation dialog before triggering "Finish Match" to prevent accidental completion.
- Offline resilience / Optimistic UI: immediate local UI response, queued background sync.

### 4.4 League Standings Calculation Engine
The standings table is calculated dynamically from all completed matches (`status == FINISHED`) in the league.

#### Calculation Formula:
For each team in the league:
1. **Played (`P`)**: Count of all finished matches where the team is either `homeTeam` or `awayTeam`.
2. **Won (`W`)**:
   - Number of finished matches where `(team is home AND homeScore > awayScore)` OR `(team is away AND awayScore > homeScore)`.
3. **Drawn (`D`)**:
   - Number of finished matches where `homeScore == awayScore`.
4. **Lost (`L`)**:
   - Number of finished matches where `(team is home AND homeScore < awayScore)` OR `(team is away AND awayScore < homeScore)`.
5. **Goals For (`GF`)**:
   - Sum of goals/points scored by the team across all finished matches.
6. **Goals Against (`GA`)**:
   - Sum of goals/points conceded by the team across all finished matches.
7. **Goal Difference (`GD`)**:
   - `GD = GF - GA`.
8. **Points (`PTS`)**:
   - `PTS = (W * pointsWin) + (D * pointsDraw) + (L * pointsLoss)`.
   - With the standard 3-1-0 configuration: `PTS = (W * 3) + (D * 1) + (L * 0)`.
9. **Recent Form (`Form`)**:
   - Sequence of results from the last 5 finished matches (ordered newest first), represented as `['W', 'D', 'L', ...]`.

#### Tie-Breaking Order:
When two or more teams have equal points, ranks are resolved in the following strict order:
1. **Total Points (`PTS`)** (Descending)
2. **Goal Difference (`GD`)** (Descending: higher positive difference ranks higher)
3. **Goals For (`GF`)** (Descending: higher total goals scored ranks higher)
4. **Head-to-Head Record** between tied teams (Points in matches between tied teams, then GD in those matches)
5. **Team Name** (Alphabetical ascending as deterministic tie-breaker)

---

## 5. API Specification (REST & Real-time)

### 5.1 Leagues & Teams
- `GET /api/leagues`
  - Returns list of all leagues.
- `POST /api/leagues`
  - Payload: `{ name: string, season: string, pointsWin?: number, pointsDraw?: number, pointsLoss?: number }`
  - Creates a new league.
- `GET /api/leagues/:leagueId`
  - Returns league details.
- `GET /api/leagues/:leagueId/teams`
  - Returns all teams in the league.
- `POST /api/leagues/:leagueId/teams`
  - Payload: `{ name: string, shortName: string, logoUrl?: string }`
  - Registers a new team in the league.

### 5.2 Matches & Scorekeeping
- `GET /api/leagues/:leagueId/matches`
  - Query params: `status`, `round`, `teamId`.
  - Returns matches filtered by criteria.
- `POST /api/leagues/:leagueId/matches`
  - Payload: `{ homeTeamId: string, awayTeamId: string, matchday?: number, scheduledAt: string }`
  - Creates/schedules a match.
- `GET /api/matches/:matchId`
  - Returns detailed match information, current scores, and status.
- `POST /api/matches/:matchId/start`
  - Transitions match from `SCHEDULED` to `IN_PROGRESS`.
- `PATCH /api/matches/:matchId/score`
  - Payload: `{ homeScore: number, awayScore: number, period?: string, note?: string }`
  - Updates live score. Broadcasts real-time event.
- `POST /api/matches/:matchId/finish`
  - Transitions match to `FINISHED`. Computes and locks final score. Triggers standings recalculation.

### 5.3 Standings
- `GET /api/leagues/:leagueId/standings`
  - Query params: `live` (boolean, default: `false`).
    - If `live=false`: calculated strictly from `status == 'FINISHED'`.
    - If `live=true`: includes real-time in-progress match scores as a provisional preview.
  - Response:
    ```json
    {
      "leagueId": "uuid-123",
      "leagueName": "Metro Amateur Premier League",
      "calculatedAt": "2026-09-14T20:00:00Z",
      "standings": [
        {
          "rank": 1,
          "teamId": "t1",
          "teamName": "Riverside FC",
          "shortName": "RFC",
          "played": 10,
          "won": 7,
          "drawn": 2,
          "lost": 1,
          "goalsFor": 24,
          "goalsAgainst": 10,
          "goalDifference": 14,
          "points": 23,
          "form": ["W", "W", "D", "W", "L"]
        }
      ]
    }
    ```

### 5.4 Real-time Streaming
- `GET /api/leagues/:leagueId/live-stream` (Server-Sent Events)
  - Broadcasts events:
    - `match_score_updated`: `{ matchId, homeScore, awayScore, period }`
    - `match_finished`: `{ matchId, finalHomeScore, finalAwayScore }`
    - `standings_updated`: Full updated standings payload.

---

## 6. User Interface & User Experience (UI/UX)

### 6.1 Public League Hub
- **Header**: League selector, current season indicator, quick links (Standings, Matches, Teams).
- **Live Match Strip**: Carousel / banner displaying matches currently `IN_PROGRESS` with live score badges pulsing in real time.
- **Standings Table**:
  - Columns: Rank, Club / Team, P, W, D, L, GF, GA, GD, PTS, Last 5 (Form).
  - Clear visual demarcation for top ranks (e.g., Champions / Promotion zone in gold/green) and bottom ranks (relegation in soft red).
  - Fully responsive: on mobile screens, less critical columns (GF, GA) collapse with an expandable drawer, keeping P, GD, PTS prominently visible.
- **Fixtures & Results View**:
  - Filterable by matchday / round or team.
  - Distinct badges for `FT` (Full Time / Finished), `LIVE`, and scheduled kick-off times.

### 6.2 Pitchside Scorekeeper Dashboard
- Dedicated distraction-free view (`/matches/:matchId/scorekeeper`).
- Large +1 / -1 stepper buttons with high touch contrast for glove or direct sunlight pitchside use.
- Status quick controls:
  - "Kick Off" button.
  - Period toggles ("1st Half", "Half Time", "2nd Half").
  - Big red/green "Finalize Match" button with two-step modal confirmation ("Are you sure you want to finish the match with final score X - Y?").

---

## 7. Security & Data Integrity Specification

Following strict secure web development standards (OWASP Top 10, Mandatory Secure Web Skills):

### 7.1 Input Validation & SQL Injection Prevention
- All incoming payloads must be strictly validated using schema libraries (e.g. Zod).
- Numerical inputs (`homeScore`, `awayScore`, `matchday`) must be validated as non-negative integers (`z.number().int().min(0)`).
- Strings (`team.name`, `league.name`) must have strict length bounds and be stripped of null bytes or dangerous control characters.
- All database interactions must use parameterized queries, prepared statements, or ORM abstraction (Prisma/Drizzle). String concatenation in SQL queries is strictly prohibited.

### 7.2 Cross-Site Scripting (XSS) Prevention
- Frontend rendering must use framework-native auto-escaping (React JSX `{team.name}`).
- Prohibit any usage of `dangerouslySetInnerHTML`.
- HTML attributes must always be properly quoted.
- Output encoding must be guaranteed when displaying team names or custom league descriptions.

### 7.3 Authentication & Authorization
- **Roles**:
  - `Public / Viewer`: Read-only access to leagues, teams, matches, live scores, and standings.
  - `Scorekeeper / Referee`: Can update live scores and start/finish assigned matches.
  - `League Administrator`: Full access to create/delete leagues, add teams, generate fixtures, and adjust official records.
- Server-side session authentication with `HttpOnly`, `Secure`, `SameSite=Lax` cookies.
- Authorization checks must be verified on the server side close to data access, never trusted from client flags.

### 7.4 Security Headers & Network Safety
- Enforce Content Security Policy (CSP):
  ```http
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-ancestors 'none';
  ```
- Anti-clickjacking: `X-Frame-Options: DENY`.
- MIME sniffing prevention: `X-Content-Type-Options: nosniff`.
- Local test servers must bind exclusively to `localhost` or `127.0.0.1`, never to `0.0.0.0`.

---

## 8. Standings Calculation Algorithm (Pseudo-code & Edge Cases)

```typescript
interface MatchResult {
  homeTeamId: string;
  awayTeamId: string;
  homeScore: number;
  awayScore: number;
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'FINISHED' | 'CANCELLED';
}

interface TeamStanding {
  teamId: string;
  teamName: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  form: ('W' | 'D' | 'L')[];
}

export function calculateStandings(
  teams: { id: string; name: string }[],
  matches: MatchResult[],
  pointsConfig = { win: 3, draw: 1, loss: 0 }
): TeamStanding[] {
  // 1. Initialize stats table for all teams
  const table = new Map<string, TeamStanding>();
  for (const team of teams) {
    table.set(team.id, {
      teamId: team.id,
      teamName: team.name,
      played: 0,
      won: 0,
      drawn: 0,
      lost: 0,
      goalsFor: 0,
      goalsAgainst: 0,
      goalDifference: 0,
      points: 0,
      form: []
    });
  }

  // 2. Filter for finished matches only
  const finishedMatches = matches.filter(m => m.status === 'FINISHED');

  // 3. Process match outcomes
  for (const m of finishedMatches) {
    const home = table.get(m.homeTeamId);
    const away = table.get(m.awayTeamId);
    if (!home || !away) continue;

    home.played += 1;
    away.played += 1;

    home.goalsFor += m.homeScore;
    home.goalsAgainst += m.awayScore;
    away.goalsFor += m.awayScore;
    away.goalsAgainst += m.homeScore;

    if (m.homeScore > m.awayScore) {
      home.won += 1;
      home.points += pointsConfig.win;
      away.lost += 1;
      away.points += pointsConfig.loss;
      home.form.push('W');
      away.form.push('L');
    } else if (m.homeScore < m.awayScore) {
      away.won += 1;
      away.points += pointsConfig.win;
      home.lost += 1;
      home.points += pointsConfig.loss;
      away.form.push('W');
      home.form.push('L');
    } else {
      home.drawn += 1;
      home.points += pointsConfig.draw;
      away.drawn += 1;
      away.points += pointsConfig.draw;
      home.form.push('D');
      away.form.push('D');
    }
  }

  // 4. Calculate GD and limit form to last 5 matches
  for (const row of table.values()) {
    row.goalDifference = row.goalsFor - row.goalsAgainst;
    row.form = row.form.slice(-5).reverse(); // newest first
  }

  // 5. Sort table according to tie-breaking criteria
  return Array.from(table.values()).sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points;
    if (b.goalDifference !== a.goalDifference) return b.goalDifference - a.goalDifference;
    if (b.goalsFor !== a.goalsFor) return b.goalsFor - a.goalsFor;
    return a.teamName.localeCompare(b.teamName);
  });
}
```

---

## 9. Verification & Testing Plan

### 9.1 Unit Tests (Standings Engine)
- **Zero Matches**: All teams have 0 P, 0 W, 0 D, 0 L, 0 PTS, sorted alphabetically.
- **Single Match (Home Win)**: Home team gets 3 PTS, away gets 0 PTS. Correct GF, GA, GD.
- **Single Match (Draw)**: Both teams get 1 point, 0 GD.
- **High Scoring Draw (e.g. 4-4)**: Both teams get 1 point, GF=4, GA=4, GD=0.
- **Tie-breaker 1 (GD)**: Two teams with identical 3 points; team with +3 GD ranks higher than team with +1 GD.
- **Tie-breaker 2 (GF)**: Two teams with identical points (3) and GD (+1); team with 3-2 win ranks higher than team with 1-0 win.
- **Tie-breaker 3 (Alphabetical)**: Identical record resolves deterministically by team name.
- **Unfinished Matches Exclusion**: Matches with status `SCHEDULED` or `IN_PROGRESS` are strictly excluded from official standings.

### 9.2 Integration Tests
- Full match lifecycle API tests:
  - Create match -> Verify status is `SCHEDULED`.
  - Start match -> Verify status is `IN_PROGRESS`.
  - Send live score update -> Verify updated score and event log.
  - Finish match -> Verify status is `FINISHED`, standings endpoint returns updated points.
- Error handling tests:
  - Rejecting negative scores (`-1`).
  - Rejecting match creation with the same team as home and away.
  - Non-existent league ID / team ID returns clean 404/400 without leaking stack traces.

### 9.3 Security Verification Plan
- **Security Scanner**: Run security scanning tools on all endpoints and files for common vulnerabilities (SQL injection, XSS, insecure headers).
- **Security Audit**: Audit input validation, secret handling, CSRF protections, and authorization barriers.
- **Network Listening**: Verify test servers bind only to `127.0.0.1`.
