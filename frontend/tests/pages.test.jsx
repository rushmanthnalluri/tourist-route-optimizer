import React from 'react';
import { render, act, fireEvent, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CO1Page from '../src/pages/CO1Page.jsx';
import CO2Page from '../src/pages/CO2Page.jsx';
import CO3Page from '../src/pages/CO3Page.jsx';
import CO4Page from '../src/pages/CO4Page.jsx';
import CO5Page from '../src/pages/CO5Page.jsx';
import CO6Page from '../src/pages/CO6Page.jsx';
import HomePage from '../src/pages/HomePage.jsx';

import { useApp } from '../src/context/AppContext';
import { MemoryRouter } from 'react-router-dom';
import { api } from '../src/utils/api.js';

global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

vi.mock('../src/utils/api.js', () => ({
  api: {
    getAttractions: vi.fn().mockResolvedValue([]),
    getGraph: vi.fn().mockResolvedValue({}),
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

vi.mock('react-leaflet', () => {
  const React = require('react');
  const div = (props) => React.createElement('div', props, props.children);
  return {
    MapContainer: div, TileLayer: div, Marker: div, Popup: div, Polyline: div,
    useMap: () => ({ setView: vi.fn(), fitBounds: vi.fn() }),
    useMapEvents: vi.fn()
  };
});

vi.mock('../src/context/AppContext', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useApp: () => ({
      attractions: [{id: 1, name: 'Charminar', category: 'historical', lat: 17, lng: 78}], 
      startId: 1, goalIds: [1], routePath: [1],
      loading: false, statusMsg: 'Ready', setStartId: vi.fn(), toggleGoalId: vi.fn(),
      toggleGoal: vi.fn(), handleMapPick: vi.fn(), mapPickActive: false, addCustomPlace: vi.fn(),
      startMapPick: vi.fn(), cancelMapPick: vi.fn(), setStatus: vi.fn(), setLoading: vi.fn(),
      routingPayload: vi.fn(() => ({})), removeCustomPlace: vi.fn(),
      resolveRoutingIds: vi.fn((ids) => ids)
    })
  };
});

const Wrap = ({ children }) => (
  <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>{children}</MemoryRouter>
);

describe('Pages', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('renders CO1Page', async () => {
    render(<CO1Page />, { wrapper: Wrap });
    fireEvent.click(screen.getByText('Environment Types'));
    fireEvent.click(screen.getByText('Knowledge Repr.'));
    fireEvent.click(screen.getByText('Problem Formulation'));
  });

  it('renders CO2Page', async () => {
    api.runSearch.mockResolvedValue({ success: true, path: [1], trace: [{step:1}] });
    api.compareSearch.mockResolvedValue({ comparison: { BFS: { nodes_expanded: 1, runtime_ms: 1, total_distance_km: 1, success: true } } });
    render(<CO2Page />, { wrapper: Wrap });
    fireEvent.click(screen.getByText('DFS'));
    fireEvent.click(screen.getByText('Time'));
    fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '100' } });
    await act(async () => { fireEvent.click(screen.getByText('Run DFS')); });
    
    await act(async () => { fireEvent.click(screen.getByText('Compare All')); });
    
    api.runSearch.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Run DFS')); });
    api.compareSearch.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Compare All')); });
  });

  it('renders CO3Page', async () => {
    api.scheduleCSP.mockResolvedValue({ success: true, schedule: [{time:'9:00', name:'A'}] });
    render(<CO3Page />, { wrapper: Wrap });
    fireEvent.click(screen.getByText('Min-Conflicts'));
    await act(async () => { fireEvent.click(screen.getByText('Schedule Attractions')); });
    
    api.scheduleCSP.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Schedule Attractions')); });
  });

  it('renders CO4Page', async () => {
    api.computeUtility.mockResolvedValue({ utility: 0.8, components: {a:1} });
    api.runMinimax.mockResolvedValue({ trace: [], minimax_value: 0.5, optimal_first_choice: 'A' });
    api.expectedUtility.mockResolvedValue({ results: [{name: 'A', expected_utility: 0.5, recommended: true}] });
    
    render(<CO4Page />, { wrapper: Wrap });
    fireEvent.click(screen.getByText('historical'));
    await act(async () => { fireEvent.click(screen.getByText('Compute Expected Utility')); });
    await act(async () => { fireEvent.click(screen.getByText('Compute Utility')); });
    await act(async () => { fireEvent.click(screen.getByText('Run Minimax')); });

    api.computeUtility.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Compute Utility')); });
    api.runMinimax.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Run Minimax')); });
    api.expectedUtility.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Compute Expected Utility')); });
  });

  it('renders CO5Page', async () => {
    api.bayesUpdate.mockResolvedValue({ crowd_prob: 0.8, crowd_level: 'High' });
    api.infer.mockResolvedValue({ satisfaction_prob: 0.9, details: {} });
    api.hmmTrack.mockResolvedValue({ trace: [], most_likely_state: 'moving', state_probs: {} });

    render(<CO5Page />, { wrapper: Wrap });
    await act(async () => { fireEvent.click(screen.getByText('Run Bayes Update')); });
    await act(async () => { fireEvent.click(screen.getByText('Infer Satisfaction')); });
    await act(async () => { fireEvent.click(screen.getByText(/Track Tourist State/)); });
    
    fireEvent.click(screen.getByText('gps moving'));
    
    api.bayesUpdate.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Run Bayes Update')); });
    api.infer.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Infer Satisfaction')); });
    api.hmmTrack.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText(/Track Tourist State/)); });
  });

  it('renders CO6Page', async () => {
    api.hybridPlan.mockResolvedValue({ 
      co2_search: { path: [1] },
      co3_csp: { schedule: [] },
      co5_prob: { inference: { satisfaction_prob: 0.9 } },
      co4_decision: { minimax_result: { minimax_value: 0.8 } },
      co6_ethics: { passed: true, checks: [] },
      total_runtime_ms: 10
    });
    render(<CO6Page />, { wrapper: Wrap });
    await act(async () => { fireEvent.click(screen.getByText('Run Full Hybrid Pipeline')); });
    
    api.hybridPlan.mockRejectedValue(new Error('err'));
    await act(async () => { fireEvent.click(screen.getByText('Run Full Hybrid Pipeline')); });
  });

  it('renders HomePage', async () => {
    render(<HomePage />, { wrapper: Wrap });
    
    fireEvent.change(screen.getByPlaceholderText(/Search attractions/i), { target: { value: 'charminar' } });
    
    await act(async () => { fireEvent.click(screen.getByText('Add custom place')); });
    fireEvent.change(screen.getByPlaceholderText('Place name'), { target: { value: 'MyPlace' } });
    fireEvent.change(screen.getByPlaceholderText('Latitude'), { target: { value: '17.1' } });
    fireEvent.change(screen.getByPlaceholderText('Longitude'), { target: { value: '78.1' } });
    await act(async () => { fireEvent.click(screen.getByText('Save place')); });

    await act(async () => { fireEvent.click(screen.getByText('Add custom place')); });
    fireEvent.change(screen.getByPlaceholderText('Place name'), { target: { value: '' } });
    await act(async () => { fireEvent.click(screen.getByText('Save place')); });
    
    fireEvent.change(screen.getByPlaceholderText('Place name'), { target: { value: 'MyPlace' } });
    fireEvent.change(screen.getByPlaceholderText('Latitude'), { target: { value: 'invalid' } });
    await act(async () => { fireEvent.click(screen.getByText('Save place')); });

    await act(async () => { fireEvent.click(screen.getByText('Pick on map')); });

    await act(async () => { fireEvent.click(screen.getByText('Run Full Pipeline')); });
  });
});
