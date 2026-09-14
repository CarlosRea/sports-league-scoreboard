import React from 'react';
import { PlayCircle, Radio, Clock, Play, CheckCircle2 } from 'lucide-react';
import type { Match, Team } from '../types/models';

interface ScorekeeperTabProps {
  matches: Match[];
  teams: Team[];
  onOpenScorekeeper: (match: Match) => void;
  onStartMatch: (matchId: string) => void;
}

export const ScorekeeperTab: React.FC<ScorekeeperTabProps> = ({
  matches,
  teams,
  onOpenScorekeeper,
  onStartMatch,
}) => {
  const getTeam = (teamId: string) => teams.find(t => t.id === teamId);

  const liveMatches = matches.filter(m => m.status === 'IN_PROGRESS');
  const scheduledMatches = matches.filter(m => m.status === 'SCHEDULED');
  const finishedMatches = matches.filter(m => m.status === 'FINISHED').slice(0, 4);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-amber-950/40 via-slate-900 to-slate-900 p-5 rounded-2xl border border-amber-500/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30 shrink-0">
            <PlayCircle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">
              Pitchside Referee & Scorekeeper Console
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live scoring, period tracking, and instant match finalization with automatic standings sync.
            </p>
          </div>
        </div>
      </div>

      {/* 1. Live Matches Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
          Matches Currently In Progress ({liveMatches.length})
        </h3>

        {liveMatches.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
            <p className="text-sm font-medium text-slate-300">No matches currently in progress.</p>
            <p className="text-xs text-slate-500 mt-1">Select an upcoming match below and click "Kick Off" to begin live scoring.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {liveMatches.map(match => {
              const home = getTeam(match.homeTeamId);
              const away = getTeam(match.awayTeamId);

              return (
                <div
                  key={match.id}
                  className="bg-slate-900 border-2 border-rose-600/60 rounded-2xl p-5 shadow-xl shadow-rose-950/20 flex flex-col justify-between space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                      <Radio className="w-3.5 h-3.5 animate-pulse" />
                      LIVE {match.elapsedMinutes ? `${match.elapsedMinutes}'` : match.currentPeriod}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">
                      Round {match.matchday}
                    </span>
                  </div>

                  {/* Big Teams & Score layout */}
                  <div className="flex items-center justify-between gap-4 py-2">
                    <div className="flex-1 text-center">
                      <span
                        className="w-4 h-4 rounded-full inline-block mx-auto mb-1"
                        style={{ backgroundColor: home?.logoColor || '#10b981' }}
                      />
                      <div className="font-bold text-sm sm:text-base text-slate-100 truncate">
                        {home?.name}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400">HOME</div>
                    </div>

                    <div className="px-4 py-2 rounded-xl bg-slate-950 border border-rose-800/80 font-mono font-extrabold text-2xl sm:text-3xl text-amber-300">
                      {match.homeScore} - {match.awayScore}
                    </div>

                    <div className="flex-1 text-center">
                      <span
                        className="w-4 h-4 rounded-full inline-block mx-auto mb-1"
                        style={{ backgroundColor: away?.logoColor || '#3b82f6' }}
                      />
                      <div className="font-bold text-sm sm:text-base text-slate-100 truncate">
                        {away?.name}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400">AWAY</div>
                    </div>
                  </div>

                  {/* Launch button */}
                  <button
                    onClick={() => onOpenScorekeeper(match)}
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 transition active:scale-98 flex items-center justify-center gap-2"
                  >
                    <PlayCircle className="w-5 h-5" />
                    Open Live Scoreboard Console
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 2. Scheduled Matches Ready for Kickoff */}
      <div className="space-y-3 pt-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-400" />
          Scheduled Fixtures Ready to Kick Off
        </h3>

        {scheduledMatches.length === 0 ? (
          <p className="text-xs text-slate-500">All scheduled fixtures have been played or started.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {scheduledMatches.map(match => {
              const home = getTeam(match.homeTeamId);
              const away = getTeam(match.awayTeamId);

              return (
                <div
                  key={match.id}
                  className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between gap-3 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Round {match.matchday}</span>
                    <span>{new Date(match.scheduledAt).toLocaleDateString()}</span>
                  </div>

                  <div className="font-medium text-sm text-slate-200">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: home?.logoColor }} />
                        {home?.name}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: away?.logoColor }} />
                        {away?.name}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => onStartMatch(match.id)}
                    className="w-full py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition flex items-center justify-center gap-1.5 shadow-sm active:scale-95"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    Kick Off & Start Match
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 3. Recently Finished Matches */}
      {finishedMatches.length > 0 && (
        <div className="space-y-3 pt-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-slate-500" />
            Recently Completed Matches
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {finishedMatches.map(match => {
              const home = getTeam(match.homeTeamId);
              const away = getTeam(match.awayTeamId);

              return (
                <div
                  key={match.id}
                  onClick={() => onOpenScorekeeper(match)}
                  className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-between gap-2 cursor-pointer hover:border-slate-700 transition"
                >
                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>Round {match.matchday}</span>
                    <span className="text-emerald-500 font-semibold">FT</span>
                  </div>

                  <div className="flex items-center justify-between font-mono text-xs font-semibold text-slate-200">
                    <span className="truncate max-w-[90px]">{home?.shortName}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-300 font-bold">
                      {match.homeScore} - {match.awayScore}
                    </span>
                    <span className="truncate max-w-[90px] text-right">{away?.shortName}</span>
                  </div>

                  <div className="text-[10px] text-slate-500 text-center">
                    Locked into official standings
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
