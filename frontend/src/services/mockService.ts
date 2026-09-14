import type {
  IScoreboardService,
  ServiceEvent,
} from './types';
import type {
  League,
  Team,
  Match,
  StandingsResponse,
  CreateMatchDto,
  UpdateScoreDto,
  CreateTeamDto,
  CreateLeagueDto,
  MatchEvent,
} from '../types/models';
import {
  INITIAL_LEAGUE,
  INITIAL_TEAMS,
  INITIAL_MATCHES,
} from './mockData';
import { calculateStandings } from '../utils/standingsEngine';

const STORAGE_KEY_LEAGUES = 'sports_scoreboard_leagues_v1';
const STORAGE_KEY_TEAMS = 'sports_scoreboard_teams_v1';
const STORAGE_KEY_MATCHES = 'sports_scoreboard_matches_v1';

export class MockScoreboardService implements IScoreboardService {
  private listeners: Set<(event: ServiceEvent) => void> = new Set();

  constructor() {
    this.ensureInitialized();
  }

  private ensureInitialized(): void {
    if (typeof window === 'undefined') return;
    if (!localStorage.getItem(STORAGE_KEY_LEAGUES)) {
      localStorage.setItem(STORAGE_KEY_LEAGUES, JSON.stringify([INITIAL_LEAGUE]));
    }
    if (!localStorage.getItem(STORAGE_KEY_TEAMS)) {
      localStorage.setItem(STORAGE_KEY_TEAMS, JSON.stringify(INITIAL_TEAMS));
    }
    if (!localStorage.getItem(STORAGE_KEY_MATCHES)) {
      localStorage.setItem(STORAGE_KEY_MATCHES, JSON.stringify(INITIAL_MATCHES));
    }
  }

  private getStoredLeagues(): League[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY_LEAGUES);
      return data ? JSON.parse(data) : [INITIAL_LEAGUE];
    } catch {
      return [INITIAL_LEAGUE];
    }
  }

  private saveLeagues(leagues: League[]): void {
    localStorage.setItem(STORAGE_KEY_LEAGUES, JSON.stringify(leagues));
  }

  private getStoredTeams(): Team[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY_TEAMS);
      return data ? JSON.parse(data) : INITIAL_TEAMS;
    } catch {
      return INITIAL_TEAMS;
    }
  }

  private saveTeams(teams: Team[]): void {
    localStorage.setItem(STORAGE_KEY_TEAMS, JSON.stringify(teams));
  }

  private getStoredMatches(): Match[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY_MATCHES);
      return data ? JSON.parse(data) : INITIAL_MATCHES;
    } catch {
      return INITIAL_MATCHES;
    }
  }

  private saveMatches(matches: Match[]): void {
    localStorage.setItem(STORAGE_KEY_MATCHES, JSON.stringify(matches));
  }

  private emit(event: ServiceEvent): void {
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch (err) {
        console.error('Error in service event listener', err);
      }
    }
  }

  public subscribe(listener: (event: ServiceEvent) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  // --- Leagues ---
  public async getLeagues(): Promise<League[]> {
    return this.getStoredLeagues();
  }

  public async getLeague(id: string): Promise<League | null> {
    const leagues = this.getStoredLeagues();
    return leagues.find(l => l.id === id) || null;
  }

  public async createLeague(dto: CreateLeagueDto): Promise<League> {
    const leagues = this.getStoredLeagues();
    const newLeague: League = {
      id: `league-${Date.now()}`,
      name: dto.name.trim(),
      season: dto.season.trim(),
      sportType: dto.sportType?.trim() || 'Soccer',
      pointsWin: dto.pointsWin ?? 3,
      pointsDraw: dto.pointsDraw ?? 1,
      pointsLoss: dto.pointsLoss ?? 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    leagues.push(newLeague);
    this.saveLeagues(leagues);
    return newLeague;
  }

  // --- Teams ---
  public async getTeams(leagueId: string): Promise<Team[]> {
    const teams = this.getStoredTeams();
    return teams.filter(t => t.leagueId === leagueId);
  }

  public async createTeam(dto: CreateTeamDto): Promise<Team> {
    const teams = this.getStoredTeams();
    const cleanName = dto.name.trim();

    // Check duplicate team name in league
    const exists = teams.some(
      t => t.leagueId === dto.leagueId && t.name.toLowerCase() === cleanName.toLowerCase()
    );
    if (exists) {
      throw new Error(`A team named "${cleanName}" already exists in this league.`);
    }

    const defaultColors = ['#10b981', '#0284c7', '#ef4444', '#f59e0b', '#6366f1', '#a855f7', '#ec4899', '#14b8a6'];
    const randomColor = defaultColors[teams.length % defaultColors.length];

    const newTeam: Team = {
      id: `team-${Date.now()}`,
      leagueId: dto.leagueId,
      name: cleanName,
      shortName: dto.shortName.trim().toUpperCase().slice(0, 4) || cleanName.slice(0, 3).toUpperCase(),
      logoColor: dto.logoColor || randomColor,
      createdAt: new Date().toISOString(),
    };

    teams.push(newTeam);
    this.saveTeams(teams);
    this.emit({ type: 'STANDINGS_RECALCULATED', payload: { leagueId: dto.leagueId } });
    return newTeam;
  }

  // --- Matches ---
  public async getMatches(leagueId: string, filters?: { status?: string; matchday?: number }): Promise<Match[]> {
    let matches = this.getStoredMatches().filter(m => m.leagueId === leagueId);

    if (filters?.status && filters.status !== 'ALL') {
      matches = matches.filter(m => m.status === filters.status);
    }
    if (filters?.matchday) {
      matches = matches.filter(m => m.matchday === filters.matchday);
    }

    // Sort: Live first, then Scheduled by date ascending, then Finished by date descending
    return matches.sort((a, b) => {
      const statusOrder: Record<string, number> = {
        IN_PROGRESS: 1,
        SCHEDULED: 2,
        FINISHED: 3,
        CANCELLED: 4,
      };
      if (statusOrder[a.status] !== statusOrder[b.status]) {
        return statusOrder[a.status] - statusOrder[b.status];
      }
      return new Date(b.scheduledAt).getTime() - new Date(a.scheduledAt).getTime();
    });
  }

  public async getMatch(matchId: string): Promise<Match | null> {
    const matches = this.getStoredMatches();
    return matches.find(m => m.id === matchId) || null;
  }

  public async createMatch(dto: CreateMatchDto): Promise<Match> {
    if (dto.homeTeamId === dto.awayTeamId) {
      throw new Error('A team cannot play against itself.');
    }

    const matches = this.getStoredMatches();
    const newMatch: Match = {
      id: `match-${Date.now()}`,
      leagueId: dto.leagueId,
      homeTeamId: dto.homeTeamId,
      awayTeamId: dto.awayTeamId,
      matchday: Math.max(1, dto.matchday || 1),
      scheduledAt: dto.scheduledAt || new Date().toISOString(),
      status: 'SCHEDULED',
      homeScore: 0,
      awayScore: 0,
      currentPeriod: 'Not Started',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      events: [],
    };

    matches.push(newMatch);
    this.saveMatches(matches);
    this.emit({ type: 'MATCH_CREATED', payload: newMatch });
    return newMatch;
  }

  public async startMatch(matchId: string): Promise<Match> {
    const matches = this.getStoredMatches();
    const index = matches.findIndex(m => m.id === matchId);
    if (index === -1) throw new Error('Match not found');

    const match = matches[index];
    const now = new Date().toISOString();

    const startEvent: MatchEvent = {
      id: `ev-${Date.now()}`,
      matchId,
      type: 'MATCH_STARTED',
      minute: 0,
      homeScoreAfter: match.homeScore,
      awayScoreAfter: match.awayScore,
      note: 'Match kicked off',
      recordedAt: now,
    };

    const updated: Match = {
      ...match,
      status: 'IN_PROGRESS',
      currentPeriod: '1st Half',
      elapsedMinutes: 1,
      startedAt: match.startedAt || now,
      updatedAt: now,
      events: [...(match.events || []), startEvent],
    };

    matches[index] = updated;
    this.saveMatches(matches);
    this.emit({ type: 'MATCH_UPDATED', payload: updated });
    return updated;
  }

  public async updateScore(matchId: string, dto: UpdateScoreDto): Promise<Match> {
    const matches = this.getStoredMatches();
    const index = matches.findIndex(m => m.id === matchId);
    if (index === -1) throw new Error('Match not found');

    const match = matches[index];
    const now = new Date().toISOString();

    const safeHomeScore = Math.max(0, Math.floor(dto.homeScore));
    const safeAwayScore = Math.max(0, Math.floor(dto.awayScore));

    // Determine event type
    let eventType: MatchEvent['type'] = 'SCORE_ADJUST';
    let defaultNote = 'Score updated';

    if (safeHomeScore > match.homeScore) {
      eventType = 'GOAL_HOME';
      defaultNote = 'Home goal';
    } else if (safeAwayScore > match.awayScore) {
      eventType = 'GOAL_AWAY';
      defaultNote = 'Away goal';
    } else if (dto.period && dto.period !== match.currentPeriod) {
      eventType = 'PERIOD_CHANGE';
      defaultNote = `Period changed to ${dto.period}`;
    }

    const event: MatchEvent = {
      id: `ev-${Date.now()}`,
      matchId,
      type: eventType,
      minute: dto.minute ?? match.elapsedMinutes ?? 0,
      homeScoreAfter: safeHomeScore,
      awayScoreAfter: safeAwayScore,
      note: dto.note || defaultNote,
      recordedAt: now,
    };

    const updated: Match = {
      ...match,
      homeScore: safeHomeScore,
      awayScore: safeAwayScore,
      currentPeriod: dto.period ?? match.currentPeriod,
      elapsedMinutes: dto.minute ?? match.elapsedMinutes,
      updatedAt: now,
      events: [...(match.events || []), event],
    };

    matches[index] = updated;
    this.saveMatches(matches);
    this.emit({ type: 'MATCH_UPDATED', payload: updated });
    return updated;
  }

  public async finishMatch(matchId: string): Promise<Match> {
    const matches = this.getStoredMatches();
    const index = matches.findIndex(m => m.id === matchId);
    if (index === -1) throw new Error('Match not found');

    const match = matches[index];
    const now = new Date().toISOString();

    const endEvent: MatchEvent = {
      id: `ev-${Date.now()}`,
      matchId,
      type: 'MATCH_FINISHED',
      minute: 90,
      homeScoreAfter: match.homeScore,
      awayScoreAfter: match.awayScore,
      note: `Final Whistle: ${match.homeScore} - ${match.awayScore}`,
      recordedAt: now,
    };

    const updated: Match = {
      ...match,
      status: 'FINISHED',
      currentPeriod: 'Full Time',
      finishedAt: now,
      updatedAt: now,
      events: [...(match.events || []), endEvent],
    };

    matches[index] = updated;
    this.saveMatches(matches);

    this.emit({ type: 'MATCH_FINISHED', payload: updated });
    this.emit({ type: 'STANDINGS_RECALCULATED', payload: { leagueId: match.leagueId } });
    return updated;
  }

  // --- Standings ---
  public async getStandings(leagueId: string, liveProvisional = false): Promise<StandingsResponse> {
    const league = await this.getLeague(leagueId);
    const teams = await this.getTeams(leagueId);
    const matches = this.getStoredMatches().filter(m => m.leagueId === leagueId);

    const standings = calculateStandings(teams, matches, {
      pointsWin: league?.pointsWin ?? 3,
      pointsDraw: league?.pointsDraw ?? 1,
      pointsLoss: league?.pointsLoss ?? 0,
      includeInProgress: liveProvisional,
    });

    return {
      leagueId,
      leagueName: league?.name ?? 'League Standings',
      calculatedAt: new Date().toISOString(),
      isLiveProvisional: liveProvisional,
      standings,
    };
  }

  // --- Reset Demo Data ---
  public async resetDemoData(): Promise<void> {
    localStorage.setItem(STORAGE_KEY_LEAGUES, JSON.stringify([INITIAL_LEAGUE]));
    localStorage.setItem(STORAGE_KEY_TEAMS, JSON.stringify(INITIAL_TEAMS));
    localStorage.setItem(STORAGE_KEY_MATCHES, JSON.stringify(INITIAL_MATCHES));
    this.emit({ type: 'RESET_DATA', payload: null });
    this.emit({ type: 'STANDINGS_RECALCULATED', payload: { leagueId: INITIAL_LEAGUE.id } });
  }
}
