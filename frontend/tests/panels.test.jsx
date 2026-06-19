import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import SearchPanel from '../src/components/SearchPanel.jsx';
import DecisionPanel from '../src/components/DecisionPanel.jsx';
import CSPPanel from '../src/components/CSPPanel.jsx';
import HybridPanel from '../src/components/HybridPanel.jsx';
import ProbabilisticPanel from '../src/components/ProbabilisticPanel.jsx';

import { api } from '../src/utils/api.js';

vi.mock('../src/utils/api.js', () => ({
  api: {
    runSearch: vi.fn(),
    compareSearch: vi.fn(),
    scheduleCSP: vi.fn(),
    computeUtility: vi.fn(),
    runMinimax: vi.fn(),
    expectedUtility: vi.fn(),
    bayesUpdate: vi.fn(),
    infer: vi.fn(),
    hmmTrack: vi.fn(),
    hybridPlan: vi.fn()
  }
}));

vi.mock('recharts', () => {
  const React = require('react');
  const div = ({ children, className }) => React.createElement('div', { className }, children);
  return {
    ResponsiveContainer: div, RadarChart: div, PolarGrid: div, PolarAngleAxis: div,
    Radar: div, BarChart: div, Bar: div, XAxis: div, YAxis: div, Tooltip: div,
    Cell: div, LineChart: div, Line: div, CartesianGrid: div
  };
});

const defaultProps = {
  startId: 1,
  goalIds: [2],
  routePath: [1, 2],
  attractions: [{id: 1, name: 'A', category: 'historic'}, {id: 2, name: 'B', category: 'nature'}],
  onResult: vi.fn(),
  setLoading: vi.fn(),
  setStatus: vi.fn()
};

describe('Panels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  describe('SearchPanel', () => {
    it('handles run search success', async () => {
      api.runSearch.mockResolvedValue({ success: true, path: [1, 2], total_distance_km: 10, trace: [{ step: 1 }] });
      render(<SearchPanel {...defaultProps} />);
      fireEvent.click(screen.getByText('DFS'));
      fireEvent.click(screen.getByText('time'));
      fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '100' } });
      await act(async () => { fireEvent.click(screen.getByText(/Run DFS/)); });
      expect(api.runSearch).toHaveBeenCalled();
    });

    it('handles run search failure', async () => {
      api.runSearch.mockResolvedValue({ success: false, failure_reason: 'no path' });
      render(<SearchPanel {...defaultProps} />);
      fireEvent.click(screen.getByText('BFS'));
      await act(async () => { fireEvent.click(screen.getByText(/Run BFS/)); });
    });

    it('handles run search throw', async () => {
      api.runSearch.mockRejectedValue(new Error('backend error'));
      render(<SearchPanel {...defaultProps} />);
      fireEvent.click(screen.getByText('BFS'));
      await act(async () => { fireEvent.click(screen.getByText(/Run BFS/)); });
    });

    it('handles empty goals', async () => {
      render(<SearchPanel {...defaultProps} goalIds={[]} />);
      fireEvent.click(screen.getByText('BFS'));
      await act(async () => { fireEvent.click(screen.getByText(/Run BFS/)); });
    });

    it('handles compare all', async () => {
      api.compareSearch.mockResolvedValue({
        comparison: {
          bfs: { nodes_expanded: 10, runtime_ms: 5, total_distance_km: 5, success: true, optimality_gap_pct: 10 },
          dfs: { nodes_expanded: 5, runtime_ms: 2, total_distance_km: 15, success: false }
        }
      });
      render(<SearchPanel {...defaultProps} />);
      await act(async () => { fireEvent.click(screen.getByText('Compare All')); });
    });

    it('handles compare throw', async () => {
      api.compareSearch.mockRejectedValue(new Error('err'));
      render(<SearchPanel {...defaultProps} />);
      await act(async () => { fireEvent.click(screen.getByText('Compare All')); });
    });
    
    it('handles compare empty goals', async () => {
      render(<SearchPanel {...defaultProps} goalIds={[]} />);
      await act(async () => { fireEvent.click(screen.getByText('Compare All')); });
    });
  });

  describe('CSPPanel', () => {
    it('runs csp', async () => {
      api.scheduleCSP.mockResolvedValue({ success: true, schedule: [{ time: '9:00', name: 'A' }] });
      render(<CSPPanel {...defaultProps} />);
      fireEvent.click(screen.getByText('Min-Conflicts'));
      await act(async () => { fireEvent.click(screen.getByText(/Schedule Attractions/)); });
    });
    
    it('runs csp failure', async () => {
      api.scheduleCSP.mockResolvedValue({ success: false, conflict: 'time conflict' });
      render(<CSPPanel {...defaultProps} />);
      await act(async () => { fireEvent.click(screen.getByText(/Schedule Attractions/)); });
    });

    it('runs csp throw', async () => {
      api.scheduleCSP.mockRejectedValue(new Error('err'));
      render(<CSPPanel {...defaultProps} />);
      await act(async () => { fireEvent.click(screen.getByText(/Schedule Attractions/)); });
    });
  });

  describe('DecisionPanel', () => {
    it('handles actions', async () => {
      api.computeUtility.mockResolvedValue({ utility: 0.8, components: { a: 1 } });
      api.runMinimax.mockResolvedValue({ minimax_value: 0.5, optimal_first_choice: 'A', nodes_evaluated: 1, nodes_pruned: 0, pruning_ratio: 0, runtime_ms: 1, trace: [{ action: 'A', alpha: 0, beta: 1, val: 0.5 }] });
      api.expectedUtility.mockResolvedValue({ results: [{ name: 'A', expected_utility: 0.6, recommended: true }, { name: 'B', expected_utility: 0.2, recommended: false }] });
      
      render(<DecisionPanel {...defaultProps} />);
      fireEvent.click(screen.getByText('historical'));
      fireEvent.click(screen.getByText('historical'));
      fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '10' } });
      fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'morning' } });
      fireEvent.change(screen.getAllByRole('spinbutton')[1], { target: { value: '10' } });
      fireEvent.change(screen.getAllByRole('spinbutton')[2], { target: { value: '10' } });

      await act(async () => { fireEvent.click(screen.getByText('Compute Utility')); });
      
      fireEvent.change(screen.getAllByRole('slider')[0], { target: { value: '3' } });
      await act(async () => { fireEvent.click(screen.getByText('Run Minimax')); });
      
      fireEvent.change(screen.getAllByRole('slider')[1], { target: { value: '0.5' } });
      await act(async () => { fireEvent.click(screen.getByText('Compute Expected Utility')); });
    });

    it('handles empty route', async () => {
      render(<DecisionPanel {...defaultProps} routePath={[]} />);
      await act(async () => { fireEvent.click(screen.getByText('Compute Utility')); });
    });
  });

  describe('ProbabilisticPanel', () => {
    it('handles actions', async () => {
      api.bayesUpdate.mockResolvedValue({ crowd_prob: 0.7, crowd_level: 'High' });
      api.infer.mockResolvedValue({ satisfaction_prob: 0.9, details: { High: 0.9 } });
      api.hmmTrack.mockResolvedValue({ state_probs: { 'moving': 0.8, 'visiting': 0.2 }, most_likely_state: 'moving', trace: [{step:1}] });
      
      render(<ProbabilisticPanel {...defaultProps} />);
      fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'rain' } });

      await act(async () => { fireEvent.click(screen.getByText('Run Bayes Update')); });
      await act(async () => { fireEvent.click(screen.getByText('Infer Satisfaction')); });
      
      fireEvent.click(screen.getByText('gps moving'));
      await act(async () => { fireEvent.click(screen.getByText('Track Tourist State')); });
    });
  });

  describe('HybridPanel', () => {
    it('handles actions', async () => {
      api.hybridPlan.mockResolvedValue({ 
        success: true, 
        path: [1], 
        pipeline_trace: [{ stage: 'co1_setup', elapsed_ms: 1 }, { stage: 'co2_search', elapsed_ms: 2 }],
        co1_setup: { peas: { actuators: ['a'] }, environment_type: { observability: 'O', determinism: 'D' }, rules_fired: ['R1'], rule_advice: ['Adv'] },
        co2_search: { candidate_paths: [{ nodes: [1], cost: 10, distance: 5 }] },
        co3_csp: { final_schedule: [{ time: '9:00', name: 'A' }], csp_variables: 2, csp_constraints_checked: 5 },
        co4_decision: { minimax_result: { minimax_value: 0.8, nodes_pruned: 1, trace: [] } },
        co5_prob: { inference: { satisfaction_prob: 0.9, weather_factor: 1, crowd_factor: 1 } },
        co6_ethics: { passed: true, checks: [{ name: 'A', passed: true, message: 'ok' }] }
      });
      render(<HybridPanel {...defaultProps} />);
      fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '10' } });
      fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'rain' } });
      fireEvent.click(screen.getByRole('checkbox'));
      await act(async () => { fireEvent.click(screen.getByText(/Run Full Hybrid Pipeline/i)); });
      
      const co1Btns = screen.getAllByText(/CO1/i);
      await act(async () => { fireEvent.click(co1Btns[co1Btns.length - 1]); });
      const co2Btns = screen.getAllByText(/CO2/i);
      await act(async () => { fireEvent.click(co2Btns[co2Btns.length - 1]); });
      const co3Btns = screen.getAllByText(/CO3/i);
      await act(async () => { fireEvent.click(co3Btns[co3Btns.length - 1]); });
      const co4Btns = screen.getAllByText(/CO4/i);
      await act(async () => { fireEvent.click(co4Btns[co4Btns.length - 1]); });
      const co5Btns = screen.getAllByText(/CO5/i);
      await act(async () => { fireEvent.click(co5Btns[co5Btns.length - 1]); });
      const co6Btns = screen.getAllByText(/CO6/i);
      await act(async () => { fireEvent.click(co6Btns[co6Btns.length - 1]); });
      await act(async () => { fireEvent.click(co6Btns[co6Btns.length - 1]); }); 
    });
    it('handles failures', async () => {
      api.hybridPlan.mockResolvedValue({ success: false, reason: 'failed' });
      render(<HybridPanel {...defaultProps} />);
      await act(async () => { fireEvent.click(screen.getByText(/Run Full Hybrid Pipeline/i)); });
      
      api.hybridPlan.mockRejectedValue(new Error('err'));
      await act(async () => { fireEvent.click(screen.getByText(/Run Full Hybrid Pipeline/i)); });
    });
    it('handles empty goals', async () => {
      render(<HybridPanel {...defaultProps} goalIds={[]} />);
      await act(async () => { fireEvent.click(screen.getByText(/Run Full Hybrid Pipeline/i)); });
    });
  });
});
