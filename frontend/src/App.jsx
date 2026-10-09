import React, { useState, useEffect } from 'react';
import OperatorDashboard from './pages/OperatorDashboard';
import PublicDashboard from './pages/PublicDashboard';
import { useTrafficData } from './hooks/useTrafficData';
import './App.css';

export default function App() {
  const trafficData = useTrafficData();

  // Route state: 'operator' (default) or 'public'
  const [currentView, setCurrentView] = useState(() => {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname.toLowerCase();
      const hash = window.location.hash.toLowerCase();
      if (path === '/public' || path.startsWith('/public/') || hash === '#/public' || hash === '#public') {
        return 'public';
      }
    }
    return 'operator';
  });

  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.toLowerCase();
      const hash = window.location.hash.toLowerCase();
      if (path === '/public' || path.startsWith('/public/') || hash === '#/public' || hash === '#public') {
        setCurrentView('public');
      } else {
        setCurrentView('operator');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateToPublic = () => {
    setCurrentView('public');
    if (window.location.pathname !== '/public') {
      window.history.pushState({}, '', '/public');
    }
  };

  const navigateToOperator = () => {
    setCurrentView('operator');
    if (window.location.pathname !== '/') {
      window.history.pushState({}, '', '/');
    }
  };

  if (currentView === 'public') {
    return (
      <PublicDashboard
        selectedScenario={trafficData.selectedScenario}
        setSelectedScenario={trafficData.setSelectedScenario}
        selectedJunction={trafficData.selectedJunction}
        setSelectedJunction={trafficData.setSelectedJunction}
        activeData={trafficData.activeData}
        corridorState={trafficData.corridorState}
        connectionStatus={trafficData.connectionStatus}
        isBackendConnected={trafficData.isBackendConnected}
        onSwitchToOperator={navigateToOperator}
      />
    );
  }

  return (
    <OperatorDashboard
      selectedScenario={trafficData.selectedScenario}
      setSelectedScenario={trafficData.setSelectedScenario}
      selectedJunction={trafficData.selectedJunction}
      setSelectedJunction={trafficData.setSelectedJunction}
      userRole={trafficData.userRole}
      setUserRole={trafficData.setUserRole}
      activeData={trafficData.activeData}
      corridorState={trafficData.corridorState}
      currentRecommendation={trafficData.currentRecommendation}
      auditEvents={trafficData.auditEvents}
      connectionStatus={trafficData.connectionStatus}
      isBackendConnected={trafficData.isBackendConnected}
      replayStep={trafficData.replayStep}
      isReplaying={trafficData.isReplaying}
      handleReplay={trafficData.handleReplay}
      approvalStatus={trafficData.approvalStatus}
      handleApproveRecommendation={trafficData.handleApproveRecommendation}
      onSwitchToPublic={navigateToPublic}
      isPlaying={trafficData.isPlaying}
      simTime={trafficData.simTime}
      simTotalTime={trafficData.simTotalTime}
      simSpeed={trafficData.simSpeed}
      handlePlay={trafficData.handlePlay}
      handlePause={trafficData.handlePause}
      handleStep={trafficData.handleStep}
      handleReset={trafficData.handleReset}
      handleSpeedChange={trafficData.handleSpeedChange}
      selectedItemType={trafficData.selectedItemType}
      selectedItemId={trafficData.selectedItemId}
      handleLocate={trafficData.handleLocate}
      roadsList={trafficData.roadsList}
      vehiclesList={trafficData.vehiclesList}
    />
  );
}
