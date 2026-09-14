import type {
  League,
  Team,
  Match,
  StandingsResponse,
  CreateMatchDto,
  UpdateScoreDto,
  CreateTeamDto,
  CreateLeagueDto,
} from '../types/models';

export type ServiceEventType = 
  | 'MATCH_UPDATED' 
  | 'MATCH_CREATED' 
  | 'MATCH_FINISHED' 
  | 'STANDINGS_RECALCULATED'
  | 'RESET_DATA';

export interface ServiceEvent {
  type: ServiceEventType;
  payload: any;
}

export interface IScoreboardService {
  // Leagues
  getLeagues(): Promise<League[]>;
  getLeague(id: string): Promise<League | null>;
  createLeague(dto: CreateLeagueDto): Promise<League>;

  // Teams
  getTeams(leagueId: string): Promise<Team[]>;
  createTeam(dto: CreateTeamDto): Promise<Team>;

  // Matches
  getMatches(leagueId: string, filters?: { status?: string; matchday?: number }): Promise<Match[]>;
  getMatch(matchId: string): Promise<Match | null>;
  createMatch(dto: CreateMatchDto): Promise<Match>;
  startMatch(matchId: string): Promise<Match>;
  updateScore(matchId: string, dto: UpdateScoreDto): Promise<Match>;
  finishMatch(matchId: string): Promise<Match>;

  // Standings
  getStandings(leagueId: string, liveProvisional?: boolean): Promise<StandingsResponse>;

  // Demo / Dev utility
  resetDemoData(): Promise<void>;

  // Real-time Event Subscription (SSE / WebSocket abstraction)
  subscribe(listener: (event: ServiceEvent) => void): () => void;
}
