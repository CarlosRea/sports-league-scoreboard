import type { IScoreboardService } from './types';
import { MockScoreboardService } from './mockService';
import { HttpScoreboardService } from './apiService';

/**
 * Service Factory:
 * Defaults to the in-browser MockScoreboardService with persistent localStorage.
 * If VITE_USE_REAL_API is set to 'true', HttpScoreboardService is used.
 */
const useRealApi = import.meta.env.VITE_USE_REAL_API === 'true';
const apiUrl = import.meta.env.VITE_API_URL || '/api';

export const scoreboardService: IScoreboardService = useRealApi
  ? new HttpScoreboardService(apiUrl)
  : new MockScoreboardService();

export * from './types';
export * from './mockService';
export * from './apiService';
