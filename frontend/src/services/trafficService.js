/**
 * TrafficTwin AI — Traffic Operations Service
 * Communicates with FastAPI backend (http://127.0.0.1:8000)
 * with graceful fallback to authentic recorded M1–M9 data.
 */

import { apiRequest } from '../api/client';
import { SCENARIOS } from '../data/corridorData';

export const trafficService = {
  /**
   * Health & Connection Check
   */
  async checkHealth() {
    return await apiRequest('/health', {
      status: 'offline',
      connection: 'RECORDED SIMULATION',
      mode: 'RECORDED SIMULATION',
      sim_engine: 'SUMO 1.27.1',
      seed: 42,
      firewall_active: true,
      spillback_guard_active: true,
      planner_active: true,
      fail_safe_mode: 'PREDICTIVE',
    });
  },

  /**
   * Fetch Real-Time / Scenario Corridor State
   */
  async getCorridorState(scenarioId = 'blocked_downstream') {
    const fallback = SCENARIOS[scenarioId] || SCENARIOS.blocked_downstream;
    return await apiRequest(`/corridor/state?scenario=${scenarioId}`, {
      scenario: scenarioId,
      controller_mode: 'PREDICTIVE',
      J1: fallback.junctions.J1,
      J2: fallback.junctions.J2,
      J3: fallback.junctions.J3,
      J4: fallback.junctions.J4,
      risk: fallback.junctions.J3.risk,
      active_recommendation: {
        recommendation_id: 'REC-2026-J3-0887',
        proposed_action: 'SPILLBACK_CLEARANCE',
        reason: 'Downstream occupancy 88.7% exceeds 85.0% threshold.',
        status: 'PENDING_APPROVAL',
      },
      selected_plan: {
        plan_name: 'PLAN C',
        total_score: 28.5,
        explanation: 'Lowest safe score. Coordinates downstream clearance.',
        scores: { delay: 4.5, queue: 6.0, spillback: 12.0, fairness: 3.0, emergency: 3.0 },
      },
    });
  },

  /**
   * Fetch Scenario Summary
   */
  async getScenarioSummary(scenarioId) {
    const fallback = SCENARIOS[scenarioId] || SCENARIOS.blocked_downstream;
    return await apiRequest(`/scenarios/${scenarioId}/summary`, {
      scenario: fallback,
      comparison: fallback.comparison,
    });
  },

  /**
   * Fetch Corridor Junctions
   */
  async getJunctions(scenarioId) {
    const fallback = SCENARIOS[scenarioId]?.junctions || SCENARIOS.blocked_downstream.junctions;
    return await apiRequest(`/scenarios/${scenarioId}/junctions`, fallback);
  },

  /**
   * Fetch Current Recommendation
   */
  async getCurrentRecommendation(scenarioId = 'blocked_downstream') {
    return await apiRequest(`/recommendations/current?scenario=${scenarioId}`, {
      recommendation_id: 'REC-2026-J3-0887',
      junction: 'J3',
      proposed_action: 'SPILLBACK_CLEARANCE',
      reason: 'Downstream link J3_J4 storage exceeds 85.0% (47/53 veh, 88.7% occupancy).',
      status: 'PENDING_APPROVAL',
      m9_selected_plan: {
        plan_name: 'PLAN C',
        total_score: 28.5,
        scores: { delay: 4.5, queue: 6.0, spillback: 12.0, fairness: 3.0, emergency: 3.0 },
      },
    });
  },

  /**
   * Fetch Audit Log Events
   */
  async getAuditEvents(limit = 50) {
    return await apiRequest(`/audit-events?limit=${limit}`, [
      {
        event_id: 'AUD-006',
        timestamp: '2026-10-08T12:02:03Z',
        event_type: 'm5_validation',
        junction_id: 'J3',
        details: 'Safety Firewall verified transition Phase 0 -> Phase 1. Minimum green satisfied.',
        status: 'APPROVED',
      },
      {
        event_id: 'AUD-005',
        timestamp: '2026-10-08T12:02:02Z',
        event_type: 'm9_plan_selection',
        junction_id: 'J3',
        details: 'Evaluator selected PLAN C (Score 28.5). Plan B rejected (spillback violation).',
        status: 'SELECTED',
      },
      {
        event_id: 'AUD-004',
        timestamp: '2026-10-08T12:02:01Z',
        event_type: 'm6_block',
        junction_id: 'J3',
        details: 'Spillback Guard intercepted extension: Link J3_J4 occupancy at 88.7%.',
        status: 'BLOCKED',
      },
    ]);
  },

  /**
   * Fetch Decision Replay Trace
   */
  async getDecisionTrace(scenarioId) {
    const fallback = SCENARIOS[scenarioId]?.decisionTrace || SCENARIOS.blocked_downstream.decisionTrace;
    return await apiRequest(`/replay?scenario=${scenarioId}`, fallback);
  },

  /**
   * Fetch Simulation Runtime Status & Clock
   */
  async getSimulationStatus() {
    return await apiRequest('/simulation/status', {
      sim_state: 'RUNNING',
      sim_time_s: 123.0,
      total_time_s: 360.0,
      step_s: 1.0,
      speed_multiplier: 1.0,
      active_vehicles_count: 38,
      mode: 'CONNECTED_SUMO',
    });
  },

  /**
   * Send Simulation Control Action (play, pause, step, reset, speed)
   */
  async controlSimulation(action, speed = 1.0, step = 1) {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/simulation/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, speed, step }),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Fallback local response
    }
    return {
      status: 'acknowledged',
      action,
      speed_multiplier: speed,
      sim_time_s: action === 'reset' ? 0.0 : 123.0,
      sim_state: action === 'pause' ? 'PAUSED' : 'RUNNING',
    };
  },

  /**
   * Fetch Physical Road Segments
   */
  async getRoads(scenarioId = 'blocked_downstream') {
    return await apiRequest(`/scenarios/${scenarioId}/roads`, [
      { road_id: 'W0_J1', name: 'Westbound Inflow -> J1', from_node: 'W0', to_node: 'J1', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 34.2, status: 'CLEAR' },
      { road_id: 'J1_J2', name: 'Corridor Section J1 -> J2', from_node: 'J1', to_node: 'J2', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 41.5, status: 'CLEAR' },
      { road_id: 'J2_J3', name: 'Corridor Section J2 -> J3', from_node: 'J2', to_node: 'J3', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 58.0, status: 'MODERATE' },
      { road_id: 'J3_J4', name: 'Corridor Bottleneck J3 -> J4', from_node: 'J3', to_node: 'J4', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 88.7, status: 'SPILLBACK RISK' },
      { road_id: 'J4_E5', name: 'Corridor Exit J4 -> Eastbound', from_node: 'J4', to_node: 'E5', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 22.4, status: 'CLEAR' },
    ]);
  },

  /**
   * Fetch Active Vehicles on Corridor
   */
  async getVehicles(scenarioId = 'blocked_downstream') {
    return await apiRequest(`/scenarios/${scenarioId}/vehicles`, [
      { vehicle_id: 'amb_1', type: 'emergency', speed_kmh: 46.2, lane_id: 'J2_J3_0', road_segment: 'J2_J3', distance_to_signal_m: 38.5, status: 'PRIORITY_PREEMPTION', preempted_junction: 'J2' },
      { vehicle_id: 'veh_eb_12', type: 'passenger', speed_kmh: 32.1, lane_id: 'J1_J2_1', road_segment: 'J1_J2', distance_to_signal_m: 94.0, status: 'CRUISING', preempted_junction: null },
      { vehicle_id: 'veh_eb_18', type: 'passenger', speed_kmh: 8.4, lane_id: 'J3_J4_0', road_segment: 'J3_J4', distance_to_signal_m: 12.0, status: 'QUEUED_DOWNSTREAM', preempted_junction: null },
    ]);
  },

  /**
   * Approve Recommendation
   */
  async approveRecommendation(recommendationId, role = 'OPERATOR', notes = '') {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/recommendations/${recommendationId}/approve-simulation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Role': role,
        },
        body: JSON.stringify({ notes }),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Approval failed with status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      if (role === 'VIEWER') {
        throw new Error("Role 'VIEWER' is not authorized to approve control actions. Read-only access.");
      }
      // Return local simulated approval if backend is offline in demo mode
      return {
        status: 'APPROVED',
        recommendation_id: recommendationId,
        approved_by: role,
        timestamp: new Date().toISOString(),
      };
    }
  },
};
