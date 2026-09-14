import React from 'react';
import { Users, Plus, ShieldCheck } from 'lucide-react';
import type { Team, TeamStanding } from '../types/models';

interface TeamsViewProps {
  teams: Team[];
  standings: TeamStanding[];
  onOpenCreateTeam: () => void;
}

export const TeamsView: React.FC<TeamsViewProps> = ({
  teams,
  standings,
  onOpenCreateTeam,
}) => {
  const getStats = (teamId: string) => standings.find(s => s.teamId === teamId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-400" />
            Registered Clubs ({teams.length})
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Member clubs and current tournament records
          </p>
        </div>

        <button
          onClick={onOpenCreateTeam}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition"
        >
          <Plus className="w-4 h-4" />
          Register New Club
        </button>
      </div>

      {/* Grid of Team Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {teams.map(team => {
          const stats = getStats(team.id);

          return (
            <div
              key={team.id}
              className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-slate-950 font-mono shadow-md shrink-0"
                    style={{ backgroundColor: team.logoColor || '#10b981' }}
                  >
                    {team.shortName.slice(0, 2)}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100 text-sm sm:text-base leading-tight">
                      {team.name}
                    </h3>
                    <div className="text-xs font-mono text-slate-400 mt-0.5">
                      Code: {team.shortName}
                    </div>
                  </div>
                </div>

                {stats && (
                  <span className="px-2 py-0.5 rounded-md bg-slate-800 text-amber-400 text-xs font-bold border border-slate-700 font-mono">
                    #{stats.rank}
                  </span>
                )}
              </div>

              {/* Stats pills */}
              <div className="grid grid-cols-4 gap-2 pt-3 border-t border-slate-800/80 text-center">
                <div className="bg-slate-800/50 rounded-lg py-1.5 px-1">
                  <div className="text-[10px] uppercase font-semibold text-slate-400">P</div>
                  <div className="font-mono font-bold text-xs text-slate-200">{stats?.played ?? 0}</div>
                </div>
                <div className="bg-slate-800/50 rounded-lg py-1.5 px-1">
                  <div className="text-[10px] uppercase font-semibold text-slate-400">W-D-L</div>
                  <div className="font-mono font-bold text-[11px] text-slate-200">
                    {stats ? `${stats.won}-${stats.drawn}-${stats.lost}` : '0-0-0'}
                  </div>
                </div>
                <div className="bg-slate-800/50 rounded-lg py-1.5 px-1">
                  <div className="text-[10px] uppercase font-semibold text-slate-400">GD</div>
                  <div className="font-mono font-bold text-xs text-slate-200">
                    {stats ? (stats.goalDifference > 0 ? `+${stats.goalDifference}` : stats.goalDifference) : 0}
                  </div>
                </div>
                <div className="bg-emerald-950/40 border border-emerald-500/20 rounded-lg py-1.5 px-1">
                  <div className="text-[10px] uppercase font-bold text-emerald-400">PTS</div>
                  <div className="font-mono font-bold text-xs text-emerald-300">{stats?.points ?? 0}</div>
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-emerald-500" />
                  Active in League
                </span>
                <span>GF: {stats?.goalsFor ?? 0} | GA: {stats?.goalsAgainst ?? 0}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
