import type { Match, Team, TeamStanding, MatchResultChar } from '../types/models';

export interface StandingsConfig {
  pointsWin?: number;
  pointsDraw?: number;
  pointsLoss?: number;
  includeInProgress?: boolean;
}

/**
 * Pure calculation engine for league standings following docs/spec.md:
 * - 3 points for Win, 1 point for Draw, 0 points for Loss (customizable)
 * - Tie-breakers: Points -> Goal Difference -> Goals For -> Head-to-Head -> Alphabetical
 * - Tracks form for the last 5 completed matches (newest first)
 */
export function calculateStandings(
  teams: Team[],
  matches: Match[],
  config: StandingsConfig = {}
): TeamStanding[] {
  const pointsWin = config.pointsWin ?? 3;
  const pointsDraw = config.pointsDraw ?? 1;
  const pointsLoss = config.pointsLoss ?? 0;
  const includeInProgress = config.includeInProgress ?? false;

  // Initialize accumulator for every team in the league
  const statsMap = new Map<string, {
    team: Team;
    played: number;
    won: number;
    drawn: number;
    lost: number;
    goalsFor: number;
    goalsAgainst: number;
    points: number;
    formChronological: MatchResultChar[]; // ordered by match finished/date time
  }>();

  for (const team of teams) {
    statsMap.set(team.id, {
      team,
      played: 0,
      won: 0,
      drawn: 0,
      lost: 0,
      goalsFor: 0,
      goalsAgainst: 0,
      points: 0,
      formChronological: [],
    });
  }

  // Filter matches to consider: strictly FINISHED, plus optionally IN_PROGRESS if live provisional table
  const relevantMatches = matches
    .filter(m => m.status === 'FINISHED' || (includeInProgress && m.status === 'IN_PROGRESS'))
    // Sort matches chronologically to produce accurate form guide
    .sort((a, b) => {
      const timeA = new Date(a.finishedAt || a.scheduledAt).getTime();
      const timeB = new Date(b.finishedAt || b.scheduledAt).getTime();
      return timeA - timeB;
    });

  for (const match of relevantMatches) {
    const home = statsMap.get(match.homeTeamId);
    const away = statsMap.get(match.awayTeamId);

    if (!home || !away) continue;

    home.played += 1;
    away.played += 1;

    home.goalsFor += match.homeScore;
    home.goalsAgainst += match.awayScore;
    away.goalsFor += match.awayScore;
    away.goalsAgainst += match.homeScore;

    if (match.homeScore > match.awayScore) {
      home.won += 1;
      home.points += pointsWin;
      away.lost += 1;
      away.points += pointsLoss;
      home.formChronological.push('W');
      away.formChronological.push('L');
    } else if (match.homeScore < match.awayScore) {
      away.won += 1;
      away.points += pointsWin;
      home.lost += 1;
      home.points += pointsLoss;
      away.formChronological.push('W');
      home.formChronological.push('L');
    } else {
      home.drawn += 1;
      home.points += pointsDraw;
      away.drawn += 1;
      away.points += pointsDraw;
      home.formChronological.push('D');
      away.formChronological.push('D');
    }
  }

  // Helper for head-to-head tie-breaker between two teams
  function getHeadToHeadPoints(teamAId: string, teamBId: string): number {
    let diff = 0;
    for (const m of relevantMatches) {
      if (m.homeTeamId === teamAId && m.awayTeamId === teamBId) {
        if (m.homeScore > m.awayScore) diff += pointsWin;
        else if (m.homeScore < m.awayScore) diff -= pointsWin;
      } else if (m.homeTeamId === teamBId && m.awayTeamId === teamAId) {
        if (m.awayScore > m.homeScore) diff += pointsWin;
        else if (m.awayScore < m.homeScore) diff -= pointsWin;
      }
    }
    return diff;
  }

  // Convert map to array and sort
  const standingsRows = Array.from(statsMap.values()).map(item => {
    const goalDifference = item.goalsFor - item.goalsAgainst;
    // Last 5 matches, newest first
    const form = [...item.formChronological].slice(-5).reverse();

    return {
      rank: 1, // Will be set after sorting
      teamId: item.team.id,
      teamName: item.team.name,
      shortName: item.team.shortName,
      logoColor: item.team.logoColor,
      played: item.played,
      won: item.won,
      drawn: item.drawn,
      lost: item.lost,
      goalsFor: item.goalsFor,
      goalsAgainst: item.goalsAgainst,
      goalDifference,
      points: item.points,
      form,
    };
  });

  // Sort by tie-breaking hierarchy:
  // 1. Points (descending)
  // 2. Goal Difference (descending)
  // 3. Goals For (descending)
  // 4. Head-to-Head points
  // 5. Team Name (alphabetical ascending)
  standingsRows.sort((a, b) => {
    if (b.points !== a.points) {
      return b.points - a.points;
    }
    if (b.goalDifference !== a.goalDifference) {
      return b.goalDifference - a.goalDifference;
    }
    if (b.goalsFor !== a.goalsFor) {
      return b.goalsFor - a.goalsFor;
    }
    const h2h = getHeadToHeadPoints(b.teamId, a.teamId);
    if (h2h !== 0) {
      return h2h;
    }
    return a.teamName.localeCompare(b.teamName);
  });

  // Assign final 1-based ranks
  return standingsRows.map((row, index) => ({
    ...row,
    rank: index + 1,
  }));
}
