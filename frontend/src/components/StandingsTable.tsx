import React from 'react';
import { Trophy, HelpCircle, Activity } from 'lucide-react';
import type { TeamStanding, MatchResultChar } from '../types/models';

interface StandingsTableProps {
  standings: TeamStanding[];
  isLiveProvisional: boolean;
  onToggleLiveProvisional: (val: boolean) => void;
  onSelectTeam?: (teamId: string) => void;
}

export const StandingsTable: React.FC<StandingsTableProps> = ({
  standings,
  isLiveProvisional,
  onToggleLiveProvisional,
  onSelectTeam,
}) => {
  const renderFormBadge = (result: MatchResultChar, index: number) => {
    let bg = 'bg-slate-700 text-slate-200';
    if (result === 'W') bg = 'bg-emerald-600 text-white';
    if (result === 'D') bg = 'bg-amber-600 text-white';
    if (result === 'L') bg = 'bg-rose-600 text-white';

    const label = result === 'W' ? 'Win' : result === 'D' ? 'Draw' : 'Loss';

    return (
      <span
        key={index}
        title={label}
        className={`w-5 h-5 rounded-md inline-flex items-center justify-center text-[10px] font-bold ${bg} shadow-sm`}
      >
        {result}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Standings Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-400" />
            League Standings
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Standard 3-1-0 points system (Win: 3pts • Draw: 1pt • Loss: 0pt)
          </p>
        </div>

        {/* Live Table Toggle */}
        <div className="flex items-center gap-3">
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={isLiveProvisional}
              onChange={(e) => onToggleLiveProvisional(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-10 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600"></div>
            <span className="ml-2 text-xs font-semibold text-slate-300 flex items-center gap-1">
              <Activity className={`w-3.5 h-3.5 ${isLiveProvisional ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
              Provisional Live Table
            </span>
          </label>
        </div>
      </div>

      {isLiveProvisional && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-300 flex items-center gap-2">
          <Activity className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>Provisional View Active:</strong> Current scores from in-progress matches are included. Official standings only lock when matches finish.
          </span>
        </div>
      )}

      {/* Main Standings Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 shadow-xl">
        <table className="w-full text-left border-collapse text-xs sm:text-sm">
          <thead>
            <tr className="bg-slate-800/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-700/80">
              <th className="py-3 px-3 sm:px-4 text-center w-12">Pos</th>
              <th className="py-3 px-3 sm:px-4">Club</th>
              <th className="py-3 px-2 sm:px-3 text-center" title="Played">P</th>
              <th className="py-3 px-2 sm:px-3 text-center" title="Won">W</th>
              <th className="py-3 px-2 sm:px-3 text-center" title="Drawn">D</th>
              <th className="py-3 px-2 sm:px-3 text-center" title="Lost">L</th>
              <th className="py-3 px-2 sm:px-3 text-center hidden md:table-cell" title="Goals For">GF</th>
              <th className="py-3 px-2 sm:px-3 text-center hidden md:table-cell" title="Goals Against">GA</th>
              <th className="py-3 px-2 sm:px-3 text-center" title="Goal Difference">GD</th>
              <th className="py-3 px-3 sm:px-4 text-center font-bold text-slate-200" title="Points">PTS</th>
              <th className="py-3 px-3 sm:px-4 text-center hidden sm:table-cell">Form</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {standings.length === 0 ? (
              <tr>
                <td colSpan={11} className="text-center py-8 text-slate-500">
                  No teams found in this league.
                </td>
              </tr>
            ) : (
              standings.map((row) => {
                const isLeader = row.rank === 1;
                const isPodium = row.rank <= 3;
                const isRelegation = row.rank > standings.length - 2 && standings.length >= 4;

                let rankBadgeBg = 'text-slate-400 bg-slate-800';
                if (isLeader) rankBadgeBg = 'text-amber-400 bg-amber-500/10 font-bold border border-amber-500/40';
                else if (isPodium) rankBadgeBg = 'text-emerald-400 bg-emerald-500/10 font-bold border border-emerald-500/30';
                else if (isRelegation) rankBadgeBg = 'text-rose-400 bg-rose-500/10 font-semibold border border-rose-500/30';

                return (
                  <tr
                    key={row.teamId}
                    onClick={() => onSelectTeam?.(row.teamId)}
                    className="hover:bg-slate-800/40 transition duration-150 cursor-pointer group"
                  >
                    {/* Rank */}
                    <td className="py-3 px-3 sm:px-4 text-center">
                      <span className={`inline-flex items-center justify-center w-6 h-6 rounded-md text-xs ${rankBadgeBg}`}>
                        {row.rank}
                      </span>
                    </td>

                    {/* Team Name & Crest */}
                    <td className="py-3 px-3 sm:px-4 font-medium text-slate-100">
                      <div className="flex items-center gap-2.5">
                        <span
                          className="w-3.5 h-3.5 rounded-full shadow-sm shrink-0"
                          style={{ backgroundColor: row.logoColor || '#64748b' }}
                        />
                        <span className="font-semibold text-slate-100 group-hover:text-emerald-400 transition">
                          {row.teamName}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400 uppercase hidden sm:inline">
                          ({row.shortName})
                        </span>
                      </div>
                    </td>

                    {/* P, W, D, L */}
                    <td className="py-3 px-2 sm:px-3 text-center text-slate-300 font-mono">{row.played}</td>
                    <td className="py-3 px-2 sm:px-3 text-center text-slate-300 font-mono">{row.won}</td>
                    <td className="py-3 px-2 sm:px-3 text-center text-slate-300 font-mono">{row.drawn}</td>
                    <td className="py-3 px-2 sm:px-3 text-center text-slate-300 font-mono">{row.lost}</td>

                    {/* GF, GA */}
                    <td className="py-3 px-2 sm:px-3 text-center text-slate-400 font-mono hidden md:table-cell">{row.goalsFor}</td>
                    <td className="py-3 px-2 sm:px-3 text-center text-slate-400 font-mono hidden md:table-cell">{row.goalsAgainst}</td>

                    {/* GD */}
                    <td className="py-3 px-2 sm:px-3 text-center font-mono font-medium">
                      <span
                        className={
                          row.goalDifference > 0
                            ? 'text-emerald-400'
                            : row.goalDifference < 0
                            ? 'text-rose-400'
                            : 'text-slate-400'
                        }
                      >
                        {row.goalDifference > 0 ? `+${row.goalDifference}` : row.goalDifference}
                      </span>
                    </td>

                    {/* Points */}
                    <td className="py-3 px-3 sm:px-4 text-center font-mono font-bold text-slate-100 text-sm sm:text-base bg-slate-800/30">
                      {row.points}
                    </td>

                    {/* Form Guide (last 5) */}
                    <td className="py-3 px-3 sm:px-4 text-center hidden sm:table-cell">
                      <div className="flex items-center justify-center gap-1">
                        {row.form.length === 0 ? (
                          <span className="text-slate-600 text-xs">-</span>
                        ) : (
                          row.form.map((res, i) => renderFormBadge(res, i))
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Tie-breaker & Legend info */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs text-slate-400 px-2 gap-2">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-amber-500/80"></span>
            1st: Champion
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-emerald-500/80"></span>
            Top 3: Podium
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-rose-500/80"></span>
            Bottom 2: Relegation Zone
          </span>
        </div>

        <div className="flex items-center gap-1 text-slate-400" title="Tie-breaking order: Points > Goal Difference > Goals For > Head-to-Head > Alphabetical">
          <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
          <span>Tie-breakers: PTS &gt; GD &gt; GF &gt; Head-to-Head</span>
        </div>
      </div>
    </div>
  );
};
