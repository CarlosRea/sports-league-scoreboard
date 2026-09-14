import React from 'react';
import { Trophy, PlayCircle, Calendar, Users, Plus, RotateCcw } from 'lucide-react';
import type { League } from '../types/models';

interface NavbarProps {
  currentLeague: League | null;
  activeTab: 'standings' | 'matches' | 'scorekeeper' | 'teams';
  onSelectTab: (tab: 'standings' | 'matches' | 'scorekeeper' | 'teams') => void;
  liveMatchesCount: number;
  onOpenCreateMatch: () => void;
  onOpenCreateTeam: () => void;
  onResetData: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentLeague,
  activeTab,
  onSelectTab,
  liveMatchesCount,
  onOpenCreateMatch,
  onOpenCreateTeam,
  onResetData,
}) => {
  return (
    <header className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top row: Brand + League + Quick Actions */}
        <div className="flex items-center justify-between h-16 gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-amber-500/20 shrink-0">
              <Trophy className="w-5 h-5 text-slate-950 font-bold" />
            </div>
            <div className="min-w-0">
              <h1 className="text-lg font-bold text-slate-100 tracking-tight leading-tight truncate">
                {currentLeague?.name || 'Sports League Scoreboard'}
              </h1>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="text-emerald-400 font-semibold">{currentLeague?.season || '2026/27'}</span>
                <span>•</span>
                <span>{currentLeague?.sportType || 'Amateur League'}</span>
                <span>•</span>
                <span className="text-slate-300 font-mono">Win: 3pts | Draw: 1pt | Loss: 0pt</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={onOpenCreateMatch}
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition active:scale-95"
            >
              <Plus className="w-3.5 h-3.5" />
              New Match
            </button>

            <button
              onClick={onOpenCreateTeam}
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition active:scale-95"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Team
            </button>

            <button
              onClick={onResetData}
              title="Reset to default demo data"
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 text-xs font-medium border border-slate-700/80 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Reset Demo</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center justify-between overflow-x-auto no-scrollbar border-t border-slate-800/60 pt-1">
          <nav className="flex space-x-1 sm:space-x-4 py-2">
            <button
              onClick={() => onSelectTab('standings')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition ${
                activeTab === 'standings'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Trophy className="w-4 h-4" />
              Standings
            </button>

            <button
              onClick={() => onSelectTab('matches')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition ${
                activeTab === 'matches'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Calendar className="w-4 h-4" />
              Matches & Results
            </button>

            <button
              onClick={() => onSelectTab('scorekeeper')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition ${
                activeTab === 'scorekeeper'
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <PlayCircle className="w-4 h-4" />
              Pitchside Scorekeeper
              {liveMatchesCount > 0 && (
                <span className="inline-flex items-center justify-center px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-rose-500 text-white animate-pulse">
                  {liveMatchesCount} LIVE
                </span>
              )}
            </button>

            <button
              onClick={() => onSelectTab('teams')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition ${
                activeTab === 'teams'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Users className="w-4 h-4" />
              Clubs
            </button>
          </nav>

          {/* Mobile quick action icons */}
          <div className="flex sm:hidden items-center gap-1.5 py-1">
            <button
              onClick={onOpenCreateMatch}
              className="p-1.5 rounded-lg bg-emerald-600 text-white text-xs"
              title="New Match"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
