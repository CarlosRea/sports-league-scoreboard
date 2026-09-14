import React from 'react';
import { Play, PlayCircle, CheckCircle2, Calendar, Clock, ChevronRight } from 'lucide-react';
import type { Match, Team } from '../types/models';

interface MatchCardProps {
  match: Match;
  teams: Team[];
  onOpenScorekeeper: (match: Match) => void;
  onStartMatch: (matchId: string) => void;
  onViewEvents?: (match: Match) => void;
}

export const MatchCard: React.FC<MatchCardProps> = ({
  match,
  teams,
  onOpenScorekeeper,
  onStartMatch,
  onViewEvents,
}) => {
  const home = teams.find(t => t.id === match.homeTeamId);
  const away = teams.find(t => t.id === match.awayTeamId);

  const isLive = match.status === 'IN_PROGRESS';
  const isFinished = match.status === 'FINISHED';
  const isScheduled = match.status === 'SCHEDULED';

  const formatScheduledDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div
      className={`rounded-xl border transition-all duration-200 p-4 ${
        isLive
          ? 'bg-slate-900 border-rose-600/50 shadow-lg shadow-rose-950/30 ring-1 ring-rose-500/20'
          : isFinished
          ? 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700/80'
      }`}
    >
      {/* Top row: Matchday & Status Badge */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className="text-[11px] font-semibold tracking-wider uppercase text-slate-400">
          Matchday {match.matchday}
        </span>

        {isLive && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping"></span>
            LIVE {match.elapsedMinutes ? `${match.elapsedMinutes}'` : match.currentPeriod}
          </span>
        )}

        {isFinished && (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            Full Time
          </span>
        )}

        {isScheduled && (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
            <Clock className="w-3 h-3 text-slate-400" />
            {formatScheduledDate(match.scheduledAt)}
          </span>
        )}
      </div>

      {/* Match Scoreboard Area */}
      <div className="grid grid-cols-7 items-center gap-2 py-2">
        {/* Home Team */}
        <div className="col-span-3 flex items-center justify-end gap-2 text-right">
          <div>
            <div className="font-semibold text-sm sm:text-base text-slate-100 leading-tight">
              {home?.name || 'Home Team'}
            </div>
            <div className="text-[11px] font-mono text-slate-400">
              {home?.shortName}
            </div>
          </div>
          <span
            className="w-4 h-4 rounded-full shadow-sm shrink-0"
            style={{ backgroundColor: home?.logoColor || '#64748b' }}
          />
        </div>

        {/* Score / VS Center */}
        <div className="col-span-1 flex flex-col items-center justify-center">
          {isScheduled ? (
            <div className="px-2 py-1 rounded bg-slate-800 text-slate-400 text-xs font-bold uppercase tracking-wider">
              VS
            </div>
          ) : (
            <div
              className={`px-3 py-1 rounded-lg font-mono font-bold text-lg sm:text-xl tracking-tight ${
                isLive
                  ? 'bg-rose-950/60 text-amber-300 border border-rose-800/60'
                  : 'bg-slate-800 text-slate-100 border border-slate-700'
              }`}
            >
              {match.homeScore} - {match.awayScore}
            </div>
          )}
        </div>

        {/* Away Team */}
        <div className="col-span-3 flex items-center justify-start gap-2 text-left">
          <span
            className="w-4 h-4 rounded-full shadow-sm shrink-0"
            style={{ backgroundColor: away?.logoColor || '#64748b' }}
          />
          <div>
            <div className="font-semibold text-sm sm:text-base text-slate-100 leading-tight">
              {away?.name || 'Away Team'}
            </div>
            <div className="text-[11px] font-mono text-slate-400">
              {away?.shortName}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Actions Row */}
      <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between">
        <div className="text-[11px] text-slate-400 flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span>{new Date(match.scheduledAt).toLocaleDateString()}</span>
          {match.events && match.events.length > 0 && (
            <span className="ml-1 text-slate-400">({match.events.length} events)</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {isScheduled && (
            <button
              onClick={() => onStartMatch(match.id)}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition active:scale-95 shadow-sm"
            >
              <Play className="w-3 h-3 fill-current" />
              Kick Off
            </button>
          )}

          {isLive && (
            <button
              onClick={() => onOpenScorekeeper(match)}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition active:scale-95 shadow-md shadow-amber-500/20"
            >
              <PlayCircle className="w-3.5 h-3.5" />
              Pitchside Scorekeeper
            </button>
          )}

          {isFinished && (
            <button
              onClick={() => (onViewEvents ? onViewEvents(match) : onOpenScorekeeper(match))}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
            >
              Details
              <ChevronRight className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
