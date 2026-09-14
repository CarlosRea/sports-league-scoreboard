import React, { useState } from 'react';
import { X, Calendar, AlertCircle } from 'lucide-react';
import type { Team, CreateMatchDto } from '../types/models';

interface CreateMatchModalProps {
  isOpen: boolean;
  leagueId: string;
  teams: Team[];
  onClose: () => void;
  onCreateMatch: (dto: CreateMatchDto) => Promise<void>;
}

export const CreateMatchModal: React.FC<CreateMatchModalProps> = ({
  isOpen,
  leagueId,
  teams,
  onClose,
  onCreateMatch,
}) => {
  if (!isOpen) return null;

  const [homeTeamId, setHomeTeamId] = useState(teams[0]?.id || '');
  const [awayTeamId, setAwayTeamId] = useState(teams[1]?.id || '');
  const [matchday, setMatchday] = useState<number>(1);
  const [scheduledDate, setScheduledDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    d.setHours(15, 0, 0, 0);
    return d.toISOString().slice(0, 16);
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!homeTeamId || !awayTeamId) {
      setError('Please select both home and away teams.');
      return;
    }

    if (homeTeamId === awayTeamId) {
      setError('A team cannot play against itself. Please choose two distinct teams.');
      return;
    }

    if (matchday < 1) {
      setError('Matchday must be at least 1.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onCreateMatch({
        leagueId,
        homeTeamId,
        awayTeamId,
        matchday,
        scheduledAt: new Date(scheduledDate).toISOString(),
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create match.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="bg-slate-800/90 border-b border-slate-700 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <Calendar className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-slate-100">
              Schedule New Match
            </h3>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body / Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Home Team */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Home Team
            </label>
            <select
              value={homeTeamId}
              onChange={(e) => setHomeTeamId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
            >
              {teams.map(team => (
                <option key={team.id} value={team.id}>
                  {team.name} ({team.shortName})
                </option>
              ))}
            </select>
          </div>

          {/* Away Team */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Away Team
            </label>
            <select
              value={awayTeamId}
              onChange={(e) => setAwayTeamId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
            >
              {teams.map(team => (
                <option key={team.id} value={team.id} disabled={team.id === homeTeamId}>
                  {team.name} ({team.shortName}) {team.id === homeTeamId ? '(Selected as Home)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Matchday & Date Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Matchday / Round
              </label>
              <input
                type="number"
                min={1}
                value={matchday}
                onChange={(e) => setMatchday(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Date & Kick-off
              </label>
              <input
                type="datetime-local"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold shadow-md transition"
            >
              {isSubmitting ? 'Creating...' : 'Create Match'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
