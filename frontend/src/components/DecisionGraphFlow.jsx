import React, { useMemo } from 'react';
import { ReactFlow, Background, Position } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Custom clean operational node
const OperationStepNode = ({ data }) => {
  const isCritical = data.statusCode === 'critical';
  const isApproved = data.statusCode === 'approved';
  const isExecuted = data.statusCode === 'executed';
  const isActive = data.active;

  return (
    <div
      className={`op-flow-node ${isCritical ? 'node-critical' : isApproved ? 'node-approved' : isExecuted ? 'node-executed' : ''} ${isActive ? 'node-active' : ''}`}
    >
      <div className="flow-node-header">
        <span className="flow-node-step mono">{data.step}</span>
        <span className="flow-node-layer">{data.layer}</span>
        <span
          className={`flow-node-badge ${isCritical ? 'badge-crit' : isApproved ? 'badge-norm' : 'badge-info'}`}
        >
          {data.status}
        </span>
      </div>
      <div className="flow-node-title">{data.title}</div>
      <div className="flow-node-data mono">{data.data}</div>
      <div className="flow-node-detail">{data.detail}</div>
    </div>
  );
};

const nodeTypes = {
  operationStep: OperationStepNode,
};

export default function DecisionGraphFlow({
  decisionSteps,
  replayStep = 0,
}) {
  // Convert decision steps to ReactFlow nodes
  const nodes = useMemo(() => {
    return decisionSteps.map((step, idx) => {
      const stepNum = idx + 1;
      const isReached = replayStep === 0 || stepNum <= replayStep;

      return {
        id: `node-${stepNum}`,
        type: 'operationStep',
        position: { x: 12, y: idx * 84 },
        data: {
          step: `0${stepNum}`,
          layer: step.layer || step.title,
          title: step.title,
          data: step.data,
          detail: step.detail,
          status: step.status,
          statusCode: step.status_code || (step.status === 'CRITICAL' || step.status === 'BLOCKED' ? 'critical' : step.status === 'VALIDATED' ? 'approved' : 'info'),
          active: isReached,
        },
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      };
    });
  }, [decisionSteps, replayStep]);

  // Edges connecting step 1 -> 2 -> 3 -> 4 -> 5 -> 6
  const edges = useMemo(() => {
    const list = [];
    for (let i = 1; i < decisionSteps.length; i++) {
      const isEdgeActive = replayStep === 0 || i < replayStep;
      list.push({
        id: `edge-${i}-${i + 1}`,
        source: `node-${i}`,
        target: `node-${i + 1}`,
        animated: isEdgeActive,
        style: {
          stroke: isEdgeActive ? '#2563eb' : '#cbd5e1',
          strokeWidth: isEdgeActive ? 2 : 1.5,
        },
      });
    }
    return list;
  }, [decisionSteps, replayStep]);

  return (
    <div className="react-flow-wrapper">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#edf2f7" gap={16} size={1} />
      </ReactFlow>
    </div>
  );
}
