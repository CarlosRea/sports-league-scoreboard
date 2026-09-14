import type { IScoreboardService } from './types';
import { MockScoreboardService } from './mockService';
import { HttpScoreboardService } from './apiService';

/**
 * Service Factory:
 * Connects to the real FastAPI backend running on port 8009 by default.
 * If VITE_USE_MOCK is explicitly set to 'true', MockScoreboardService is used instead.
 */
const useMock = import.meta.env.VITE_USE_MOCK === 'true';
const defaultApiUrl = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:8009/api';
const apiUrl = import.meta.env.VITE_API_URL || defaultApiUrl;

export const scoreboardService: IScoreboardService = useMock
  ? new MockScoreboardService()
  : new HttpScoreboardService(apiUrl);

export * from './types';
export * from './mockService';
export * from './apiService';
