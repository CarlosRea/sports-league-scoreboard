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
 * Calls real FastAPI REST endpoints on port 8009 and connects to Server-Sent Events (SSE).
 * Automatically handles authentication credentials and provides resilient error handling.
 */
export class HttpScoreboardService implements IScoreboardService {
  private baseUrl: string;
  private eventSource: EventSource | null = null;
  private listeners: Set<(event: ServiceEvent) => void> = new Set();
  private token: string | null = null;

  constructor(baseUrl = 'http://127.0.0.1:8009/api') {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('scoreboard_auth_token');
    }
  }

  public setAuthToken(token: string | null): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('scoreboard_auth_token', token);
      } else {
        localStorage.removeItem('scoreboard_auth_token');
      }
    }
  }

  public getAuthToken(): string | null {
    return this.token;
  }

  /**
   * Log in to obtain a JWT Bearer token and session cookie.
   * Defaults to pre-seeded admin credentials if none provided.
   */
  public async login(username = 'admin', password = 'AdminPassword123!'): Promise<string> {
    const res = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      let errDetail = res.statusText;
      try {
        const json = await res.json();
        errDetail = json.detail || json.message || errDetail;
      } catch {
        // use statusText fallback
      }
      throw new Error(`Authentication failed [${res.status}]: ${errDetail}`);
    }

    const data = await res.json();
    this.setAuthToken(data.access_token);
    return data.access_token;
  }

  private async request<T>(path: string, options?: RequestInit, isRetry = false): Promise<T> {
    const method = (options?.method || 'GET').toUpperCase();
    const isMutating = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);

    // Auto-authenticate for mutating requests if not yet authenticated
    if (isMutating && !this.token && path !== '/auth/login') {
      try {
        await this.login();
      } catch (authErr) {
        console.warn('Auto-login attempt failed; continuing request anyway', authErr);
      }
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string> || {}),
    };

    if (this.token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      credentials: 'include',
      ...options,
      headers,
    });

    // If unauthorized, retry once with a fresh login
    if (res.status === 401 && !isRetry && path !== '/auth/login') {
      try {
        await this.login();
        return await this.request<T>(path, options, true);
      } catch {
        // Fall through to standard error handling below
      }
    }

    if (!res.ok) {
      let errorMsg = `API Error [${res.status}]: ${res.statusText}`;
      try {
        const errJson = await res.json();
        if (errJson.message) {
          errorMsg = errJson.message;
          if (errJson.details && Array.isArray(errJson.details)) {
            errorMsg += ` (${errJson.details.join(', ')})`;
          }
        } else if (errJson.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // Ignore JSON parse failure and use fallback
      }
      throw new Error(errorMsg);
    }

    // Return empty object for 204 No Content
    if (res.status === 204) {
      return {} as T;
    }

    return res.json();
  }

  public subscribe(listener: (event: ServiceEvent) => void): () => void {
    this.listeners.add(listener);

    // Lazily setup SSE stream if not connected
    if (!this.eventSource && typeof window !== 'undefined') {
      try {
        const streamUrl = `${this.baseUrl}/stream`;
        this.eventSource = new EventSource(streamUrl);

        this.eventSource.onmessage = (msg) => {
          try {
            const raw = JSON.parse(msg.data);
            const normalizedEvent: ServiceEvent = {
              type: raw.type,
              payload: raw.payload ?? raw.data,
            };
            this.listeners.forEach((l) => l(normalizedEvent));
          } catch (e) {
            console.error('Failed to parse SSE event payload', e);
          }
        };

        this.eventSource.onerror = (err) => {
          console.warn('Scoreboard SSE connection interrupted, reconnecting...', err);
        };
      } catch (err) {
        console.warn('Could not initialize SSE stream connection', err);
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
