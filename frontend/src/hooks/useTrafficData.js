/**
 * TrafficTwin AI — useTrafficData Custom Hook (Modules M9 & M10)
 * Manages live connection state, demo roles, scenario selection,
 * junction states, M9 plan evaluation data, audit events, and replay synchronization.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { trafficService } from '../services/trafficService';
import { SCENARIOS } from '../data/corridorData';

export function useTrafficData() {
  const [selectedScenario, setSelectedScenario] = useState('blocked_downstream');
  const [selectedJunction, setSelectedJunction] = useState('J3');
  const [userRole, setUserRole] = useState('OPERATOR'); // VIEWER | OPERATOR | ADMIN
  const [connectionStatus, setConnectionStatus] = useState('RECORDED SIMULATION');
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [corridorState, setCorridorState] = useState(null);
  const [currentRecommendation, setCurrentRecommendation] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [replayStep, setReplayStep] = useState(0);
  const [isReplaying, setIsReplaying] = useState(false);
  const [approvalStatus, setApprovalStatus] = useState(null);
  const replayTimerRef = useRef(null);

  // Active scenario data from authentic records
  const activeData = SCENARIOS[selectedScenario] || SCENARIOS.blocked_downstream;

  // Poll backend health and corridor state
  const refreshBackendData = useCallback(async () => {
    try {
      const health = await trafficService.checkHealth();
      if (health?.status === 'connected') {
        setIsBackendConnected(true);
        setConnectionStatus('SIMULATION CONNECTED');

        const [state, rec, audits] = await Promise.all([
          trafficService.getCorridorState(selectedScenario),
          trafficService.getCurrentRecommendation(selectedScenario),
          trafficService.getAuditEvents(),
        ]);

        if (state) setCorridorState(state);
        if (rec) setCurrentRecommendation(rec);
        if (audits) setAuditEvents(audits);
      } else {
        setIsBackendConnected(false);
        setConnectionStatus('RECORDED SIMULATION');
      }
    } catch {
      setIsBackendConnected(false);
      setConnectionStatus('RECORDED SIMULATION');
    }
  }, [selectedScenario]);

  useEffect(() => {
    refreshBackendData();
    const interval = setInterval(refreshBackendData, 4000);
    return () => clearInterval(interval);
  }, [refreshBackendData]);

  // When scenario changes, reset replay and focus junction
  useEffect(() => {
    setReplayStep(0);
    setIsReplaying(false);
    setApprovalStatus(null);
    if (replayTimerRef.current) clearInterval(replayTimerRef.current);

    if (selectedScenario === 'blocked_downstream' || selectedScenario === 'rush') {
      setSelectedJunction('J3');
    } else if (selectedScenario === 'ambulance') {
      setSelectedJunction('J2');
    } else {
      setSelectedJunction('J1');
    }
  }, [selectedScenario]);

  // Synchronized Decision Replay handler
  const handleReplay = useCallback(() => {
    if (isReplaying) return;
    setIsReplaying(true);
    setReplayStep(0);
    let currentStep = 0;

    replayTimerRef.current = setInterval(() => {
      currentStep += 1;
      setReplayStep(currentStep);

      if (currentStep >= 7) {
        clearInterval(replayTimerRef.current);
        setTimeout(() => setIsReplaying(false), 800);
      }
    }, 700);
  }, [isReplaying]);

  // Operator Approval Action
  const handleApproveRecommendation = useCallback(async (recId, notes = '') => {
    try {
      const result = await trafficService.approveRecommendation(recId, userRole, notes);
      setApprovalStatus({
        success: true,
        message: `Recommendation ${recId} approved by ${userRole}.`,
        details: result,
      });
      // Refresh audit events
      const audits = await trafficService.getAuditEvents();
      if (audits) setAuditEvents(audits);
      return result;
    } catch (err) {
      setApprovalStatus({
        success: false,
        message: err.message || 'Approval rejected by authorization policy.',
      });
      throw err;
    }
  }, [userRole]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (replayTimerRef.current) clearInterval(replayTimerRef.current);
    };
  }, []);

  return {
    selectedScenario,
    setSelectedScenario,
    selectedJunction,
    setSelectedJunction,
    userRole,
    setUserRole,
    activeData,
    corridorState,
    currentRecommendation,
    auditEvents,
    connectionStatus,
    isBackendConnected,
    replayStep,
    isReplaying,
    handleReplay,
    approvalStatus,
    handleApproveRecommendation,
  };
}
