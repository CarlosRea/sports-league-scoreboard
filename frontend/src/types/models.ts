export type MatchStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'FINISHED' | 'CANCELLED';

export type MatchPeriod = 
  | 'Not Started' 
  | '1st Half' 
  | 'Half Time' 
  | '2nd Half' 
  | 'Full Time';

export interface League {
  id: string;
  name: string;
  season: string;
  sportType: string;
  pointsWin: number;
  pointsDraw: number;
  pointsLoss: number;
  createdAt: string;
  updatedAt: string;
}

export interface Team {
  id: string;
  leagueId: string;
  name: string;
  shortName: string;
  logoColor: string; // Hex or tailwind color for stylized crest
  logoUrl?: string;
  createdAt: string;
}

export interface MatchEvent {
  id: string;
  matchId: string;
  type: 'GOAL_HOME' | 'GOAL_AWAY' | 'SCORE_ADJUST' | 'PERIOD_CHANGE' | 'MATCH_STARTED' | 'MATCH_FINISHED';
  minute: number;
  homeScoreAfter: number;
  awayScoreAfter: number;
  note?: string;
  recordedAt: string;
}

export interface Match {
  id: string;
  leagueId: string;
  homeTeamId: string;
  awayTeamId: string;
  matchday: number;
  scheduledAt: string;
  status: MatchStatus;
  homeScore: number;
  awayScore: number;
  currentPeriod: MatchPeriod;
  elapsedMinutes?: number;
  startedAt?: string;
  finishedAt?: string;
  createdAt: string;
  updatedAt: string;
  events?: MatchEvent[];
}

export type MatchResultChar = 'W' | 'D' | 'L';

export interface TeamStanding {
  rank: number;
  teamId: string;
  teamName: string;
  shortName: string;
  logoColor: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  form: MatchResultChar[]; // Last 5 matches, newest first
}

export interface StandingsResponse {
  leagueId: string;
  leagueName: string;
  calculatedAt: string;
  isLiveProvisional?: boolean;
  standings: TeamStanding[];
}

export interface CreateMatchDto {
  leagueId: string;
  homeTeamId: string;
  awayTeamId: string;
  matchday: number;
  scheduledAt: string;
}

export interface UpdateScoreDto {
  homeScore: number;
  awayScore: number;
  period?: MatchPeriod;
  minute?: number;
  note?: string;
}

export interface CreateTeamDto {
  leagueId: string;
  name: string;
  shortName: string;
  logoColor?: string;
}

export interface CreateLeagueDto {
  name: string;
  season: string;
  sportType?: string;
  pointsWin?: number;
  pointsDraw?: number;
  pointsLoss?: number;
}
