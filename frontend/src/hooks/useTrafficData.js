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

  // Simulation Controls & Object Inspection State
  const [isPlaying, setIsPlaying] = useState(true);
  const [simTime, setSimTime] = useState(123.0);
  const [simTotalTime] = useState(360.0);
  const [simSpeed, setSimSpeed] = useState(1.0);
  const [selectedItemType, setSelectedItemType] = useState('junction'); // 'junction' | 'road' | 'vehicle'
  const [selectedItemId, setSelectedItemId] = useState('J3');
  const [roadsList, setRoadsList] = useState([]);
  const [vehiclesList, setVehiclesList] = useState([]);

  // Active scenario data from authentic records
  const activeData = SCENARIOS[selectedScenario] || SCENARIOS.blocked_downstream;

  // Poll backend health, corridor state, roads, vehicles, and simulation status
  const refreshBackendData = useCallback(async () => {
    try {
      const health = await trafficService.checkHealth();
      if (health?.status === 'connected') {
        setIsBackendConnected(true);
        setConnectionStatus('SIMULATION CONNECTED');

        const [state, rec, audits, simStat, roads, vehs] = await Promise.all([
          trafficService.getCorridorState(selectedScenario),
          trafficService.getCurrentRecommendation(selectedScenario),
          trafficService.getAuditEvents(),
          trafficService.getSimulationStatus(),
          trafficService.getRoads(selectedScenario),
          trafficService.getVehicles(selectedScenario),
        ]);

        if (state) setCorridorState(state);
        if (rec) setCurrentRecommendation(rec);
        if (audits) setAuditEvents(audits);
        if (simStat) {
          if (simStat.sim_state === 'PAUSED') setIsPlaying(false);
          if (typeof simStat.sim_time_s === 'number') setSimTime(simStat.sim_time_s);
        }
        if (roads) setRoadsList(roads);
        if (vehs) setVehiclesList(vehs);
      } else {
        setIsBackendConnected(false);
        setConnectionStatus('RECORDED SIMULATION');
        const [roads, vehs] = await Promise.all([
          trafficService.getRoads(selectedScenario),
          trafficService.getVehicles(selectedScenario),
        ]);
        if (roads) setRoadsList(roads);
        if (vehs) setVehiclesList(vehs);
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

  // Simulation Clock tick when isPlaying is true
  useEffect(() => {
    if (!isPlaying) return;
    const timer = setInterval(() => {
      setSimTime((prev) => {
        const next = prev + simSpeed;
        return next > simTotalTime ? 0 : next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [isPlaying, simSpeed, simTotalTime]);

  // Simulation Controls
  const handlePlay = useCallback(async () => {
    setIsPlaying(true);
    await trafficService.controlSimulation('play', simSpeed);
  }, [simSpeed]);

  const handlePause = useCallback(async () => {
    setIsPlaying(false);
    await trafficService.controlSimulation('pause', simSpeed);
  }, [simSpeed]);

  const handleStep = useCallback(async () => {
    setIsPlaying(false);
    setSimTime((prev) => Math.min(prev + 1.0, simTotalTime));
    await trafficService.controlSimulation('step', simSpeed, 1);
  }, [simSpeed, simTotalTime]);

  const handleReset = useCallback(async () => {
    setIsPlaying(false);
    setSimTime(0.0);
    setReplayStep(0);
    await trafficService.controlSimulation('reset', simSpeed);
  }, [simSpeed]);

  const handleSpeedChange = useCallback(async (speed) => {
    const num = parseFloat(speed);
    setSimSpeed(num);
    await trafficService.controlSimulation('speed', num);
  }, []);

  // Locate / Inspection handler
  const handleLocate = useCallback((type, id) => {
    setSelectedItemType(type);
    setSelectedItemId(id);
    if (type === 'junction') {
      setSelectedJunction(id);
    }
  }, []);

  // When scenario changes, reset replay and focus junction
  useEffect(() => {
    setReplayStep(0);
    setIsReplaying(false);
    setApprovalStatus(null);
    if (replayTimerRef.current) clearInterval(replayTimerRef.current);

    if (selectedScenario === 'blocked_downstream' || selectedScenario === 'rush') {
      setSelectedJunction('J3');
      setSelectedItemType('junction');
      setSelectedItemId('J3');
    } else if (selectedScenario === 'ambulance') {
      setSelectedJunction('J2');
      setSelectedItemType('junction');
      setSelectedItemId('J2');
    } else {
      setSelectedJunction('J1');
      setSelectedItemType('junction');
      setSelectedItemId('J1');
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
    // Simulation playback & locate
    isPlaying,
    simTime,
    simTotalTime,
    simSpeed,
    handlePlay,
    handlePause,
    handleStep,
    handleReset,
    handleSpeedChange,
    selectedItemType,
    selectedItemId,
    handleLocate,
    roadsList,
    vehiclesList,
  };
}
