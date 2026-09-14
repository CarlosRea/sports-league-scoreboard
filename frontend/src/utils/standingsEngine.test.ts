import { describe, it, expect } from 'vitest';
import { calculateStandings } from './standingsEngine';
import type { Team, Match } from '../types/models';

describe('Standings Calculation Engine (3-1-0 Point System)', () => {
  const teams: Team[] = [
    { id: 'team-a', leagueId: 'l1', name: 'Alpha FC', shortName: 'ALP', logoColor: '#ff0000', createdAt: '' },
    { id: 'team-b', leagueId: 'l1', name: 'Beta United', shortName: 'BET', logoColor: '#00ff00', createdAt: '' },
    { id: 'team-c', leagueId: 'l1', name: 'Gamma City', shortName: 'GAM', logoColor: '#0000ff', createdAt: '' },
  ];

  it('initializes all teams with 0 points when no matches have finished', () => {
    const standings = calculateStandings(teams, []);
    expect(standings).toHaveLength(3);
    for (const row of standings) {
      expect(row.played).toBe(0);
      expect(row.won).toBe(0);
      expect(row.drawn).toBe(0);
      expect(row.lost).toBe(0);
      expect(row.points).toBe(0);
      expect(row.goalDifference).toBe(0);
      expect(row.form).toEqual([]);
    }
  });

  it('awards 3 points for a win and 0 for a loss', () => {
    const matches: Match[] = [
      {
        id: 'm1',
        leagueId: 'l1',
        homeTeamId: 'team-a',
        awayTeamId: 'team-b',
        matchday: 1,
        scheduledAt: '2026-09-01T10:00:00Z',
        status: 'FINISHED',
        homeScore: 3,
        awayScore: 1,
        currentPeriod: 'Full Time',
        createdAt: '',
        updatedAt: '',
      },
    ];

    const standings = calculateStandings(teams, matches);
    const alpha = standings.find(s => s.teamId === 'team-a')!;
    const beta = standings.find(s => s.teamId === 'team-b')!;

    expect(alpha.rank).toBe(1);
    expect(alpha.played).toBe(1);
    expect(alpha.won).toBe(1);
    expect(alpha.points).toBe(3);
    expect(alpha.goalsFor).toBe(3);
    expect(alpha.goalsAgainst).toBe(1);
    expect(alpha.goalDifference).toBe(2);
    expect(alpha.form).toEqual(['W']);

    expect(beta.played).toBe(1);
    expect(beta.lost).toBe(1);
    expect(beta.points).toBe(0);
    expect(beta.goalDifference).toBe(-2);
    expect(beta.form).toEqual(['L']);
  });

  it('awards 1 point each for a draw', () => {
    const matches: Match[] = [
      {
        id: 'm1',
        leagueId: 'l1',
        homeTeamId: 'team-a',
        awayTeamId: 'team-b',
        matchday: 1,
        scheduledAt: '2026-09-01T10:00:00Z',
        status: 'FINISHED',
        homeScore: 2,
        awayScore: 2,
        currentPeriod: 'Full Time',
        createdAt: '',
        updatedAt: '',
      },
    ];

    const standings = calculateStandings(teams, matches);
    const alpha = standings.find(s => s.teamId === 'team-a')!;
    const beta = standings.find(s => s.teamId === 'team-b')!;

    expect(alpha.points).toBe(1);
    expect(alpha.drawn).toBe(1);
    expect(alpha.goalDifference).toBe(0);
    expect(alpha.form).toEqual(['D']);

    expect(beta.points).toBe(1);
    expect(beta.drawn).toBe(1);
    expect(beta.goalDifference).toBe(0);
    expect(beta.form).toEqual(['D']);
  });

  it('breaks ties using Goal Difference (GD) when points are equal', () => {
    const matches: Match[] = [
      {
        id: 'm1',
        leagueId: 'l1',
        homeTeamId: 'team-a',
        awayTeamId: 'team-c',
        matchday: 1,
        scheduledAt: '2026-09-01T10:00:00Z',
        status: 'FINISHED',
        homeScore: 4,
        awayScore: 0, // Alpha: 3 pts, GD +4
        currentPeriod: 'Full Time',
        createdAt: '',
        updatedAt: '',
      },
      {
        id: 'm2',
        leagueId: 'l1',
        homeTeamId: 'team-b',
        awayTeamId: 'team-c',
        matchday: 2,
        scheduledAt: '2026-09-02T10:00:00Z',
        status: 'FINISHED',
        homeScore: 1,
        awayScore: 0, // Beta: 3 pts, GD +1
        currentPeriod: 'Full Time',
        createdAt: '',
        updatedAt: '',
      },
    ];

    const standings = calculateStandings(teams, matches);
    expect(standings[0].teamId).toBe('team-a'); // GD +4
    expect(standings[1].teamId).toBe('team-b'); // GD +1
  });

  it('ignores SCHEDULED and IN_PROGRESS matches for official standings', () => {
    const matches: Match[] = [
      {
        id: 'm1',
        leagueId: 'l1',
        homeTeamId: 'team-a',
        awayTeamId: 'team-b',
        matchday: 1,
        scheduledAt: '2026-09-01T10:00:00Z',
        status: 'IN_PROGRESS',
        homeScore: 5,
        awayScore: 0,
        currentPeriod: '1st Half',
        createdAt: '',
        updatedAt: '',
      },
    ];

    const standings = calculateStandings(teams, matches, { includeInProgress: false });
    expect(standings.every(s => s.played === 0 && s.points === 0)).toBe(true);

    const liveStandings = calculateStandings(teams, matches, { includeInProgress: true });
    const liveAlpha = liveStandings.find(s => s.teamId === 'team-a')!;
    expect(liveAlpha.played).toBe(1);
    expect(liveAlpha.points).toBe(3);
  });
});
