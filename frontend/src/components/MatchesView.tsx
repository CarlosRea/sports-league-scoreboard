import React, { useState } from 'react';
import { Calendar, Plus, Filter } from 'lucide-react';
import type { Match, Team } from '../types/models';
import { MatchCard } from './MatchCard';

interface MatchesViewProps {
  matches: Match[];
  teams: Team[];
  onOpenScorekeeper: (match: Match) => void;
  onStartMatch: (matchId: string) => void;
  onOpenCreateMatch: () => void;
}

export const MatchesView: React.FC<MatchesViewProps> = ({
  matches,
  teams,
  onOpenScorekeeper,
  onStartMatch,
  onOpenCreateMatch,
}) => {
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'IN_PROGRESS' | 'SCHEDULED' | 'FINISHED'>('ALL');
  const [matchdayFilter, setMatchdayFilter] = useState<number | 'ALL'>('ALL');

  // Compute available matchdays
  const matchdays = Array.from(new Set(matches.map(m => m.matchday))).sort((a, b) => a - b);

  const filteredMatches = matches.filter(m => {
    if (statusFilter !== 'ALL' && m.status !== statusFilter) return false;
    if (matchdayFilter !== 'ALL' && m.matchday !== matchdayFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-emerald-400" />
            Matches & Fixtures ({filteredMatches.length})
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Full tournament calendar, live sideline scoreboards, and full-time results
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* Status Filter buttons */}
          <div className="flex items-center bg-slate-900 border border-slate-700/80 rounded-xl p-1 text-xs">
            <button
              onClick={() => setStatusFilter('ALL')}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                statusFilter === 'ALL'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setStatusFilter('IN_PROGRESS')}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                statusFilter === 'IN_PROGRESS'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Live
            </button>
            <button
              onClick={() => setStatusFilter('SCHEDULED')}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                statusFilter === 'SCHEDULED'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Upcoming
            </button>
            <button
              onClick={() => setStatusFilter('FINISHED')}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                statusFilter === 'FINISHED'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Finished
            </button>
          </div>

          {/* Matchday Select */}
          {matchdays.length > 0 && (
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700/80 rounded-xl px-2.5 py-1 text-xs text-slate-300">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={matchdayFilter}
                onChange={(e) => setMatchdayFilter(e.target.value === 'ALL' ? 'ALL' : Number(e.target.value))}
                className="bg-transparent border-0 text-slate-200 text-xs focus:outline-none cursor-pointer pr-2"
              >
                <option value="ALL" className="bg-slate-800">All Rounds</option>
                {matchdays.map(d => (
                  <option key={d} value={d} className="bg-slate-800">
                    Round {d}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* New Match Button */}
          <button
            onClick={onOpenCreateMatch}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition active:scale-95"
          >
            <Plus className="w-3.5 h-3.5" />
            New Match
          </button>
        </div>
      </div>

      {/* Matches Grid */}
      {filteredMatches.length === 0 ? (
        <div className="text-center py-12 bg-slate-900/40 rounded-xl border border-slate-800/80 text-slate-400">
          <Calendar className="w-10 h-10 mx-auto text-slate-600 mb-3" />
          <p className="text-sm font-semibold text-slate-300">No matches match your filter criteria.</p>
          <p className="text-xs text-slate-500 mt-1">Try selecting "All" or schedule a new match.</p>
          <button
            onClick={onOpenCreateMatch}
            className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-500 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            Schedule Match
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredMatches.map(match => (
            <MatchCard
              key={match.id}
              match={match}
              teams={teams}
              onOpenScorekeeper={onOpenScorekeeper}
              onStartMatch={onStartMatch}
            />
          ))}
        </div>
      )}
    </div>
  );
};
