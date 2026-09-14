import React, { useState, useEffect, useCallback } from 'react';
import type { League, Team, Match, StandingsResponse, MatchPeriod, CreateMatchDto, CreateTeamDto } from './types/models';
import { scoreboardService } from './services';
import { Navbar } from './components/Navbar';
import { LiveScoreboardBanner } from './components/LiveScoreboardBanner';
import { StandingsTable } from './components/StandingsTable';
import { MatchesView } from './components/MatchesView';
import { ScorekeeperTab } from './components/ScorekeeperTab';
import { TeamsView } from './components/TeamsView';
import { PitchsideScorekeeperModal } from './components/PitchsideScorekeeperModal';
import { CreateMatchModal } from './components/CreateMatchModal';
import { CreateTeamModal } from './components/CreateTeamModal';

export const App: React.FC = () => {
  const [currentLeague, setCurrentLeague] = useState<League | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [standingsData, setStandingsData] = useState<StandingsResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'standings' | 'matches' | 'scorekeeper' | 'teams'>('standings');
  const [isLiveProvisional, setIsLiveProvisional] = useState(false);

  // Modals
  const [activeScorekeeperMatch, setActiveScorekeeperMatch] = useState<Match | null>(null);
  const [isCreateMatchOpen, setIsCreateMatchOpen] = useState(false);
  const [isCreateTeamOpen, setIsCreateTeamOpen] = useState(false);

  // Loading & Notification state
  const [isLoading, setIsLoading] = useState(true);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'info' } | null>(null);

  const showToast = (message: string, type: 'success' | 'info' = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3500);
  };

  // Load all league data
  const loadData = useCallback(async (provisional = isLiveProvisional) => {
    try {
      const leagues = await scoreboardService.getLeagues();
      const league = leagues[0] || null;
      setCurrentLeague(league);

      if (league) {
        const [leagueTeams, leagueMatches, leagueStandings] = await Promise.all([
          scoreboardService.getTeams(league.id),
          scoreboardService.getMatches(league.id),
          scoreboardService.getStandings(league.id, provisional),
        ]);

        setTeams(leagueTeams);
        setMatches(leagueMatches);
        setStandingsData(leagueStandings);

        // Keep active scorekeeper match in sync
        setActiveScorekeeperMatch(prev => {
          if (!prev) return null;
          return leagueMatches.find(m => m.id === prev.id) || null;
        });
      }
    } catch (err) {
      console.error('Failed to load scoreboard data', err);
    } finally {
      setIsLoading(false);
    }
  }, [isLiveProvisional]);

  // Initial load
  useEffect(() => {
    loadData(isLiveProvisional);
  }, [loadData, isLiveProvisional]);

  // Subscribe to service events (SSE / WebSocket abstraction)
  useEffect(() => {
    const unsubscribe = scoreboardService.subscribe((event) => {
      // Refresh state whenever matches change or standings recalculate
      loadData(isLiveProvisional);

      if (event.type === 'MATCH_FINISHED') {
        showToast('Match finalized! Official standings updated.', 'success');
      } else if (event.type === 'MATCH_CREATED') {
        showToast('New match scheduled.', 'info');
      } else if (event.type === 'RESET_DATA') {
        showToast('Demo data successfully reset.', 'info');
      }
    });

    return () => {
      unsubscribe();
    };
  }, [loadData, isLiveProvisional]);

  // Live matches for banner & counters
  const liveMatches = matches.filter(m => m.status === 'IN_PROGRESS');

  // Actions
  const handleStartMatch = async (matchId: string) => {
    try {
      const updated = await scoreboardService.startMatch(matchId);
      setActiveScorekeeperMatch(updated);
      showToast('Match kicked off! Pitchside scorekeeper opened.', 'success');
    } catch (err: any) {
      alert(err?.message || 'Failed to start match');
    }
  };

  const handleUpdateScore = async (
    matchId: string,
    homeScore: number,
    awayScore: number,
    period: MatchPeriod,
    minute?: number,
    note?: string
  ) => {
    try {
      await scoreboardService.updateScore(matchId, {
        homeScore,
        awayScore,
        period,
        minute,
        note,
      });
    } catch (err: any) {
      alert(err?.message || 'Failed to update score');
    }
  };

  const handleFinishMatch = async (matchId: string) => {
    try {
      await scoreboardService.finishMatch(matchId);
      setActiveScorekeeperMatch(null);
    } catch (err: any) {
      alert(err?.message || 'Failed to finish match');
    }
  };

  const handleCreateMatch = async (dto: CreateMatchDto) => {
    await scoreboardService.createMatch(dto);
    setIsCreateMatchOpen(false);
    showToast('Match successfully created.', 'success');
  };

  const handleCreateTeam = async (dto: CreateTeamDto) => {
    await scoreboardService.createTeam(dto);
    setIsCreateTeamOpen(false);
    showToast(`Team "${dto.name}" registered successfully.`, 'success');
  };

  const handleResetDemoData = async () => {
    if (window.confirm('Reset all scores, matches, and teams to initial demo state?')) {
      await scoreboardService.resetDemoData();
    }
  };

  const handleToggleLiveProvisional = (val: boolean) => {
    setIsLiveProvisional(val);
    loadData(val);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm font-medium">Loading League Scoreboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-emerald-500 selection:text-slate-950">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-800 border border-emerald-500/50 text-slate-100 text-xs sm:text-sm px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-bounce">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>{notification.message}</span>
        </div>
      )}

      {/* Top Navbar */}
      <Navbar
        currentLeague={currentLeague}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        liveMatchesCount={liveMatches.length}
        onOpenCreateMatch={() => setIsCreateMatchOpen(true)}
        onOpenCreateTeam={() => setIsCreateTeamOpen(true)}
        onResetData={handleResetDemoData}
      />

      {/* Live Match Strip / Ticker */}
      <LiveScoreboardBanner
        liveMatches={liveMatches}
        teams={teams}
        onOpenScorekeeper={(match) => setActiveScorekeeperMatch(match)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {activeTab === 'standings' && (
          <StandingsTable
            standings={standingsData?.standings || []}
            isLiveProvisional={isLiveProvisional}
            onToggleLiveProvisional={handleToggleLiveProvisional}
          />
        )}

        {activeTab === 'matches' && (
          <MatchesView
            matches={matches}
            teams={teams}
            onOpenScorekeeper={(match) => setActiveScorekeeperMatch(match)}
            onStartMatch={handleStartMatch}
            onOpenCreateMatch={() => setIsCreateMatchOpen(true)}
          />
        )}

        {activeTab === 'scorekeeper' && (
          <ScorekeeperTab
            matches={matches}
            teams={teams}
            onOpenScorekeeper={(match) => setActiveScorekeeperMatch(match)}
            onStartMatch={handleStartMatch}
          />
        )}

        {activeTab === 'teams' && (
          <TeamsView
            teams={teams}
            standings={standingsData?.standings || []}
            onOpenCreateTeam={() => setIsCreateTeamOpen(true)}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/60 py-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Sports League Scoreboard • Amateur Tournament Manager</span>
          <span className="font-mono text-slate-400">3 Points Win | 1 Draw | 0 Loss</span>
        </div>
      </footer>

      {/* Pitchside Live Scorekeeper Modal */}
      {activeScorekeeperMatch && (
        <PitchsideScorekeeperModal
          match={activeScorekeeperMatch}
          teams={teams}
          onClose={() => setActiveScorekeeperMatch(null)}
          onUpdateScore={handleUpdateScore}
          onFinishMatch={handleFinishMatch}
        />
      )}

      {/* Create Match Modal */}
      {currentLeague && (
        <CreateMatchModal
          isOpen={isCreateMatchOpen}
          leagueId={currentLeague.id}
          teams={teams}
          onClose={() => setIsCreateMatchOpen(false)}
          onCreateMatch={handleCreateMatch}
        />
      )}

      {/* Create Team Modal */}
      {currentLeague && (
        <CreateTeamModal
          isOpen={isCreateTeamOpen}
          leagueId={currentLeague.id}
          onClose={() => setIsCreateTeamOpen(false)}
          onCreateTeam={handleCreateTeam}
        />
      )}
    </div>
  );
};

export default App;
