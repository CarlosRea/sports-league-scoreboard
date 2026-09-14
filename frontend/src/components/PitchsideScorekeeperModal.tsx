import React, { useState, useEffect } from 'react';
import {
  X,
  Plus,
  Minus,
  CheckCircle,
  AlertTriangle,
  Clock,
  Radio,
  History,
} from 'lucide-react';
import type { Match, Team, MatchPeriod } from '../types/models';

interface PitchsideScorekeeperModalProps {
  match: Match | null;
  teams: Team[];
  onClose: () => void;
  onUpdateScore: (matchId: string, homeScore: number, awayScore: number, period: MatchPeriod, minute?: number, note?: string) => Promise<void>;
  onFinishMatch: (matchId: string) => Promise<void>;
}

export const PitchsideScorekeeperModal: React.FC<PitchsideScorekeeperModalProps> = ({
  match,
  teams,
  onClose,
  onUpdateScore,
  onFinishMatch,
}) => {
  // Local state for responsive real-time feedback
  const [homeScore, setHomeScore] = useState(match?.homeScore ?? 0);
  const [awayScore, setAwayScore] = useState(match?.awayScore ?? 0);
  const [period, setPeriod] = useState<MatchPeriod>(match?.currentPeriod ?? '1st Half');
  const [minute, setMinute] = useState<number>(match?.elapsedMinutes || 1);
  const [showConfirmFinish, setShowConfirmFinish] = useState(false);
  const [quickNote, setQuickNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sync with prop updates if match changes
  useEffect(() => {
    if (match) {
      setHomeScore(match.homeScore);
      setAwayScore(match.awayScore);
      setPeriod(match.currentPeriod);
      setMinute(match.elapsedMinutes || 1);
    }
  }, [match]);

  if (!match) return null;

  const home = teams.find(t => t.id === match.homeTeamId);
  const away = teams.find(t => t.id === match.awayTeamId);

  const isFinished = match.status === 'FINISHED';

  const handleAdjustScore = async (side: 'home' | 'away', delta: number) => {
    if (isFinished) return;
    const newHome = side === 'home' ? Math.max(0, homeScore + delta) : homeScore;
    const newAway = side === 'away' ? Math.max(0, awayScore + delta) : awayScore;

    setHomeScore(newHome);
    setAwayScore(newAway);

    const teamName = side === 'home' ? (home?.name || 'Home') : (away?.name || 'Away');
    const note = delta > 0 ? `Goal scored by ${teamName}` : `Score adjustment for ${teamName}`;

    await onUpdateScore(match.id, newHome, newAway, period, minute, note);
  };

  const handlePeriodChange = async (newPeriod: MatchPeriod) => {
    if (isFinished) return;
    setPeriod(newPeriod);
    let defaultMinute = minute;
    if (newPeriod === '1st Half') defaultMinute = 1;
    if (newPeriod === 'Half Time') defaultMinute = 45;
    if (newPeriod === '2nd Half') defaultMinute = 46;
    if (newPeriod === 'Full Time') defaultMinute = 90;
    setMinute(defaultMinute);

    await onUpdateScore(match.id, homeScore, awayScore, newPeriod, defaultMinute, `Period changed to ${newPeriod}`);
  };

  const handleMinuteChange = async (newMin: number) => {
    if (isFinished) return;
    const safeMin = Math.max(0, Math.min(130, newMin));
    setMinute(safeMin);
    await onUpdateScore(match.id, homeScore, awayScore, period, safeMin);
  };

  const handleAddQuickEvent = async () => {
    if (!quickNote.trim() || isFinished) return;
    setIsSubmitting(true);
    try {
      await onUpdateScore(match.id, homeScore, awayScore, period, minute, quickNote.trim());
      setQuickNote('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmFinish = async () => {
    setIsSubmitting(true);
    try {
      await onFinishMatch(match.id);
      setShowConfirmFinish(false);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const periodsList: MatchPeriod[] = ['1st Half', 'Half Time', '2nd Half', 'Full Time'];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header Bar */}
        <div className="bg-slate-800/90 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30">
              <Radio className="w-4 h-4 animate-pulse" />
            </span>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-slate-100">
                Pitchside Scorekeeper
              </h3>
              <p className="text-xs text-slate-400">
                Matchday {match.matchday} • {match.status}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 sm:p-6 space-y-6 overflow-y-auto">
          {/* Match Finished Banner */}
          {isFinished && (
            <div className="p-3 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-300 text-xs sm:text-sm flex items-center gap-2.5">
              <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
              <div>
                <strong>Official Match Finished:</strong> This match has concluded and the final score is locked into the league standings.
              </div>
            </div>
          )}

          {/* Period & Minute Bar */}
          {!isFinished && (
            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/70 flex flex-wrap items-center justify-between gap-3">
              {/* Period tabs */}
              <div className="flex items-center gap-1">
                {periodsList.map(p => (
                  <button
                    key={p}
                    onClick={() => handlePeriodChange(p)}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold transition ${
                      period === p
                        ? 'bg-amber-500 text-slate-950 shadow-sm'
                        : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>

              {/* Minute adjuster */}
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <Clock className="w-4 h-4 text-amber-400" />
                <span>Minute:</span>
                <button
                  onClick={() => handleMinuteChange(minute - 1)}
                  className="w-6 h-6 rounded bg-slate-700 hover:bg-slate-600 flex items-center justify-center font-bold"
                >
                  -
                </button>
                <span className="font-mono font-bold text-amber-300 w-8 text-center text-sm">
                  {minute}'
                </span>
                <button
                  onClick={() => handleMinuteChange(minute + 1)}
                  className="w-6 h-6 rounded bg-slate-700 hover:bg-slate-600 flex items-center justify-center font-bold"
                >
                  +
                </button>
              </div>
            </div>
          )}

          {/* Large Pitchside Stepper Controls */}
          <div className="grid grid-cols-2 gap-4 sm:gap-6">
            {/* Home Team Card */}
            <div className="bg-slate-800/70 rounded-2xl p-4 sm:p-5 border border-slate-700 flex flex-col items-center text-center">
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="w-3.5 h-3.5 rounded-full"
                  style={{ backgroundColor: home?.logoColor || '#10b981' }}
                />
                <span className="font-bold text-sm sm:text-base text-slate-100 truncate max-w-[130px] sm:max-w-[180px]">
                  {home?.name || 'Home'}
                </span>
              </div>
              <span className="text-xs font-mono text-slate-400 uppercase mb-3">
                {home?.shortName} • HOME
              </span>

              {/* Big Score Display */}
              <div className="text-5xl sm:text-6xl font-extrabold font-mono text-amber-300 my-2 select-none">
                {homeScore}
              </div>

              {/* Touch Stepper Buttons */}
              {!isFinished ? (
                <div className="flex items-center gap-3 mt-3 w-full justify-center">
                  <button
                    onClick={() => handleAdjustScore('home', -1)}
                    disabled={homeScore <= 0}
                    className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-slate-700 hover:bg-slate-600 disabled:opacity-30 text-slate-200 flex items-center justify-center font-bold transition active:scale-95 shadow-md"
                    title="Subtract 1 Goal"
                  >
                    <Minus className="w-6 h-6" />
                  </button>
                  <button
                    onClick={() => handleAdjustScore('home', 1)}
                    className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center font-bold transition active:scale-95 shadow-lg shadow-emerald-600/30"
                    title="Add 1 Goal"
                  >
                    <Plus className="w-7 h-7" />
                  </button>
                </div>
              ) : (
                <div className="text-xs text-slate-400 mt-2">Score Finalized</div>
              )}
            </div>

            {/* Away Team Card */}
            <div className="bg-slate-800/70 rounded-2xl p-4 sm:p-5 border border-slate-700 flex flex-col items-center text-center">
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="w-3.5 h-3.5 rounded-full"
                  style={{ backgroundColor: away?.logoColor || '#3b82f6' }}
                />
                <span className="font-bold text-sm sm:text-base text-slate-100 truncate max-w-[130px] sm:max-w-[180px]">
                  {away?.name || 'Away'}
                </span>
              </div>
              <span className="text-xs font-mono text-slate-400 uppercase mb-3">
                {away?.shortName} • AWAY
              </span>

              {/* Big Score Display */}
              <div className="text-5xl sm:text-6xl font-extrabold font-mono text-amber-300 my-2 select-none">
                {awayScore}
              </div>

              {/* Touch Stepper Buttons */}
              {!isFinished ? (
                <div className="flex items-center gap-3 mt-3 w-full justify-center">
                  <button
                    onClick={() => handleAdjustScore('away', -1)}
                    disabled={awayScore <= 0}
                    className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-slate-700 hover:bg-slate-600 disabled:opacity-30 text-slate-200 flex items-center justify-center font-bold transition active:scale-95 shadow-md"
                    title="Subtract 1 Goal"
                  >
                    <Minus className="w-6 h-6" />
                  </button>
                  <button
                    onClick={() => handleAdjustScore('away', 1)}
                    className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center font-bold transition active:scale-95 shadow-lg shadow-emerald-600/30"
                    title="Add 1 Goal"
                  >
                    <Plus className="w-7 h-7" />
                  </button>
                </div>
              ) : (
                <div className="text-xs text-slate-400 mt-2">Score Finalized</div>
              )}
            </div>
          </div>

          {/* Quick Note / Event Input */}
          {!isFinished && (
            <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-700/60">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Add Match Event / Referee Note
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={quickNote}
                  onChange={(e) => setQuickNote(e.target.value)}
                  placeholder="e.g. Header goal from corner kick, Penalty awarded..."
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
                <button
                  onClick={handleAddQuickEvent}
                  disabled={!quickNote.trim() || isSubmitting}
                  className="px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200 text-xs font-semibold transition"
                >
                  Log Event
                </button>
              </div>
            </div>
          )}

          {/* Match Event Timeline Log */}
          {match.events && match.events.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-slate-400" />
                Match Timeline ({match.events.length})
              </h4>
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 max-h-36 overflow-y-auto space-y-2">
                {[...match.events].reverse().map(ev => (
                  <div key={ev.id} className="flex items-center justify-between text-xs text-slate-300 border-b border-slate-800/60 pb-1.5 last:border-0 last:pb-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-amber-400 w-8">
                        {ev.minute}'
                      </span>
                      <span>{ev.note || ev.type}</span>
                    </div>
                    <span className="font-mono font-semibold text-slate-400">
                      {ev.homeScoreAfter} - {ev.awayScoreAfter}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Bar */}
        <div className="bg-slate-800/90 border-t border-slate-700 p-4 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-700/80 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-medium transition"
          >
            Close
          </button>

          {!isFinished && (
            <button
              onClick={() => setShowConfirmFinish(true)}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white font-bold text-xs sm:text-sm shadow-md shadow-rose-900/30 transition active:scale-95 flex items-center gap-1.5"
            >
              <CheckCircle className="w-4 h-4" />
              Finish Match & Lock Score
            </button>
          )}
        </div>
      </div>

      {/* Safety Confirmation Dialog for Finish Match */}
      {showConfirmFinish && (
        <div className="fixed inset-0 z-60 bg-slate-950/90 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-amber-500/50 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-amber-400">
              <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h4 className="text-lg font-bold text-slate-100">
                Confirm Match Finalization
              </h4>
            </div>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Are you sure you want to finish this match with the final score of:
            </p>

            <div className="bg-slate-950 p-4 rounded-xl text-center font-mono text-2xl font-black text-amber-300 border border-slate-800">
              {home?.name}: {homeScore} - {awayScore} :{away?.name}
            </div>

            <p className="text-xs text-slate-400">
              This will officially lock the match, mark its status as <strong>FINISHED</strong>, and automatically update the league standings table.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowConfirmFinish(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs sm:text-sm font-medium transition"
              >
                Keep In Progress
              </button>
              <button
                onClick={handleConfirmFinish}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs sm:text-sm font-bold shadow-md transition"
              >
                {isSubmitting ? 'Finalizing...' : 'Yes, Conclude Match'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
