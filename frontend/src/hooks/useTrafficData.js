/**
 * TrafficTwin AI — useTrafficData Custom Hook
 * Manages live connection state, scenario selection, junction states, and replay synchronization.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { trafficService } from '../services/trafficService';
import { SCENARIOS } from '../data/corridorData';

export function useTrafficData() {
  const [selectedScenario, setSelectedScenario] = useState('blocked_downstream');
  const [selectedJunction, setSelectedJunction] = useState('J3');
  const [connectionStatus, setConnectionStatus] = useState('RECORDED SIMULATION');
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [replayStep, setReplayStep] = useState(0);
  const [isReplaying, setIsReplaying] = useState(false);
  const replayTimerRef = useRef(null);

  // Active scenario data from authentic records
  const activeData = SCENARIOS[selectedScenario] || SCENARIOS.blocked_downstream;

  // Check backend health periodically
  useEffect(() => {
    let isMounted = true;
    async function checkBackend() {
      try {
        const health = await trafficService.checkHealth();
        if (isMounted) {
          if (health?.status === 'connected') {
            setIsBackendConnected(true);
            setConnectionStatus('SIMULATION CONNECTED');
          } else {
            setIsBackendConnected(false);
            setConnectionStatus('RECORDED SIMULATION');
          }
        }
      } catch {
        if (isMounted) {
          setIsBackendConnected(false);
          setConnectionStatus('RECORDED SIMULATION');
        }
      }
    }

    checkBackend();
    const interval = setInterval(checkBackend, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // When scenario changes, reset replay and focus junction
  useEffect(() => {
    setReplayStep(0);
    setIsReplaying(false);
    if (replayTimerRef.current) clearInterval(replayTimerRef.current);

    if (selectedScenario === 'blocked_downstream' || selectedScenario === 'rush') {
      setSelectedJunction('J3');
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

      if (currentStep >= 6) {
        clearInterval(replayTimerRef.current);
        setTimeout(() => setIsReplaying(false), 800);
      }
    }, 700);
  }, [isReplaying]);

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
    activeData,
    connectionStatus,
    isBackendConnected,
    replayStep,
    isReplaying,
    handleReplay,
  };
}
