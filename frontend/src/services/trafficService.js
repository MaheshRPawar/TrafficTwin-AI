/**
 * TrafficTwin AI — Traffic Operations Service
 * Communicates with backend endpoints or extracts recorded M1–M6 data.
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
   * Fetch Decision Trace
   */
  async getDecisionTrace(scenarioId) {
    const fallback = SCENARIOS[scenarioId]?.decisionTrace || SCENARIOS.blocked_downstream.decisionTrace;
    return await apiRequest(`/scenarios/${scenarioId}/decision_trace`, fallback);
  },
};
