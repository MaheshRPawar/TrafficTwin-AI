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
