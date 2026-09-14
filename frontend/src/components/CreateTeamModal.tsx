import React, { useState } from 'react';
import { X, Users, AlertCircle } from 'lucide-react';
import type { CreateTeamDto } from '../types/models';

interface CreateTeamModalProps {
  isOpen: boolean;
  leagueId: string;
  onClose: () => void;
  onCreateTeam: (dto: CreateTeamDto) => Promise<void>;
}

export const CreateTeamModal: React.FC<CreateTeamModalProps> = ({
  isOpen,
  leagueId,
  onClose,
  onCreateTeam,
}) => {
  const [name, setName] = useState('');
  const [shortName, setShortName] = useState('');
  const [logoColor, setLogoColor] = useState('#10b981');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const presetColors = [
    '#10b981', '#0284c7', '#ef4444', '#f59e0b',
    '#6366f1', '#a855f7', '#ec4899', '#14b8a6',
    '#e11d48', '#84cc16', '#06b6d4', '#f97316'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanName = name.trim();
    if (!cleanName) {
      setError('Team name is required.');
      return;
    }

    const cleanShort = shortName.trim().toUpperCase() || cleanName.slice(0, 3).toUpperCase();

    setIsSubmitting(true);
    try {
      await onCreateTeam({
        leagueId,
        name: cleanName,
        shortName: cleanShort,
        logoColor,
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to register team.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-slate-800/90 border-b border-slate-700 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <Users className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-slate-100">
              Register New Club / Team
            </h3>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Team / Club Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Phoenix Rising FC"
              maxLength={40}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Short Code / Initials (2-4 chars)
            </label>
            <input
              type="text"
              value={shortName}
              onChange={(e) => setShortName(e.target.value.toUpperCase().slice(0, 4))}
              placeholder="e.g. PHX"
              maxLength={4}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 placeholder-slate-500 font-mono uppercase focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Club Crest Color
            </label>
            <div className="flex flex-wrap gap-2 items-center">
              {presetColors.map(c => (
                <button
                  type="button"
                  key={c}
                  onClick={() => setLogoColor(c)}
                  className={`w-7 h-7 rounded-full transition transform ${
                    logoColor === c ? 'scale-125 ring-2 ring-white ring-offset-2 ring-offset-slate-900' : 'opacity-80 hover:opacity-100'
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
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
              {isSubmitting ? 'Registering...' : 'Add Team'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
