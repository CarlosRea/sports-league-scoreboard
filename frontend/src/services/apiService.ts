import type { IScoreboardService, ServiceEvent } from './types';
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

/**
 * Production HTTP Implementation of IScoreboardService.
 * Calls real REST API endpoints and connects to Server-Sent Events (SSE) for live score updates.
 */
export class HttpScoreboardService implements IScoreboardService {
  private baseUrl: string;
  private eventSource: EventSource | null = null;
  private listeners: Set<(event: ServiceEvent) => void> = new Set();

  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
      ...options,
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`API Error [${res.status}]: ${errorText || res.statusText}`);
    }

    return res.json();
  }

  public subscribe(listener: (event: ServiceEvent) => void): () => void {
    this.listeners.add(listener);

    // Lazily setup SSE stream if not connected
    if (!this.eventSource && typeof window !== 'undefined') {
      try {
        this.eventSource = new EventSource(`${this.baseUrl}/stream`);
        this.eventSource.onmessage = (msg) => {
          try {
            const data = JSON.parse(msg.data);
            this.listeners.forEach(l => l(data));
          } catch (e) {
            console.error('Failed to parse SSE event', e);
          }
        };
      } catch (err) {
        console.warn('Could not connect to SSE stream', err);
      }
    }

    return () => {
      this.listeners.delete(listener);
      if (this.listeners.size === 0 && this.eventSource) {
        this.eventSource.close();
        this.eventSource = null;
      }
    };
  }

  public async getLeagues(): Promise<League[]> {
    return this.request<League[]>('/leagues');
  }

  public async getLeague(id: string): Promise<League | null> {
    return this.request<League>(`/leagues/${encodeURIComponent(id)}`);
  }

  public async createLeague(dto: CreateLeagueDto): Promise<League> {
    return this.request<League>('/leagues', {
      method: 'POST',
      body: JSON.stringify(dto),
    });
  }

  public async getTeams(leagueId: string): Promise<Team[]> {
    return this.request<Team[]>(`/leagues/${encodeURIComponent(leagueId)}/teams`);
  }

  public async createTeam(dto: CreateTeamDto): Promise<Team> {
    return this.request<Team>(`/leagues/${encodeURIComponent(dto.leagueId)}/teams`, {
      method: 'POST',
      body: JSON.stringify(dto),
    });
  }

  public async getMatches(leagueId: string, filters?: { status?: string; matchday?: number }): Promise<Match[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.matchday) params.set('matchday', filters.matchday.toString());
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<Match[]>(`/leagues/${encodeURIComponent(leagueId)}/matches${query}`);
  }

  public async getMatch(matchId: string): Promise<Match | null> {
    return this.request<Match>(`/matches/${encodeURIComponent(matchId)}`);
  }

  public async createMatch(dto: CreateMatchDto): Promise<Match> {
    return this.request<Match>(`/leagues/${encodeURIComponent(dto.leagueId)}/matches`, {
      method: 'POST',
      body: JSON.stringify(dto),
    });
  }

  public async startMatch(matchId: string): Promise<Match> {
    return this.request<Match>(`/matches/${encodeURIComponent(matchId)}/start`, {
      method: 'POST',
    });
  }

  public async updateScore(matchId: string, dto: UpdateScoreDto): Promise<Match> {
    return this.request<Match>(`/matches/${encodeURIComponent(matchId)}/score`, {
      method: 'PATCH',
      body: JSON.stringify(dto),
    });
  }

  public async finishMatch(matchId: string): Promise<Match> {
    return this.request<Match>(`/matches/${encodeURIComponent(matchId)}/finish`, {
      method: 'POST',
    });
  }

  public async getStandings(leagueId: string, liveProvisional = false): Promise<StandingsResponse> {
    return this.request<StandingsResponse>(
      `/leagues/${encodeURIComponent(leagueId)}/standings?live=${liveProvisional}`
    );
  }

  public async resetDemoData(): Promise<void> {
    await this.request('/dev/reset', { method: 'POST' });
  }
}
