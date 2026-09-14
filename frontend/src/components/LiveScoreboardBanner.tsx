import React from 'react';
import { Radio, ArrowRight, Clock } from 'lucide-react';
import type { Match, Team } from '../types/models';

interface LiveScoreboardBannerProps {
  liveMatches: Match[];
  teams: Team[];
  onOpenScorekeeper: (match: Match) => void;
}

export const LiveScoreboardBanner: React.FC<LiveScoreboardBannerProps> = ({
  liveMatches,
  teams,
  onOpenScorekeeper,
}) => {
  if (liveMatches.length === 0) return null;

  const getTeam = (teamId: string) => teams.find(t => t.id === teamId);

  return (
    <div className="bg-gradient-to-r from-rose-950/70 via-slate-900 to-amber-950/50 border-b border-rose-800/40 py-2 px-4 sm:px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
          </span>
          <span className="text-xs font-bold uppercase tracking-wider text-rose-300 flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5" />
            Live Now ({liveMatches.length})
          </span>
        </div>

        {/* Live Match Chips */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          {liveMatches.map(match => {
            const home = getTeam(match.homeTeamId);
            const away = getTeam(match.awayTeamId);

            return (
              <div
                key={match.id}
                className="flex items-center gap-3 bg-slate-800/90 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs shadow-md"
              >
                <div className="flex items-center gap-1 text-slate-300">
                  <Clock className="w-3 h-3 text-rose-400" />
                  <span className="font-semibold text-rose-400">
                    {match.elapsedMinutes ? `${match.elapsedMinutes}'` : match.currentPeriod}
                  </span>
                </div>

                <div className="flex items-center gap-2 font-medium">
                  <span className="flex items-center gap-1.5">
                    <span
                      className="w-2.5 h-2.5 rounded-full inline-block"
                      style={{ backgroundColor: home?.logoColor || '#64748b' }}
                    />
                    <span className="text-slate-100">{home?.name || 'Home'}</span>
                  </span>

                  <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 font-mono font-bold text-amber-300 text-sm">
                    {match.homeScore} - {match.awayScore}
                  </span>

                  <span className="flex items-center gap-1.5">
                    <span className="text-slate-100">{away?.name || 'Away'}</span>
                    <span
                      className="w-2.5 h-2.5 rounded-full inline-block"
                      style={{ backgroundColor: away?.logoColor || '#64748b' }}
                    />
                  </span>
                </div>

                <button
                  onClick={() => onOpenScorekeeper(match)}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-[11px] transition active:scale-95"
                >
                  Score
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
