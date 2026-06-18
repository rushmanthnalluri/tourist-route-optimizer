import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ErrorBoundary } from '../src/components/ErrorBoundary.jsx';
import PageLayout from '../src/components/PageLayout.jsx';
import { useApp } from '../src/context/AppContext';

const defaultMock = {
  attractions: [{id: 1, name: 'Charminar', category: 'historical', lat: 17, lng: 78}], 
  graph: {},
  startId: 1,
  setStartId: vi.fn(),
  goalIds: [],
  setGoalIds: vi.fn(),
  toggleGoal: vi.fn(),
  routePath: [],
  setRoutePath: vi.fn(),
  traceSteps: [],
  setTraceSteps: vi.fn(),
  loading: false,
  setLoading: vi.fn(),
  statusMsg: 'Ready',
  setStatusMsg: vi.fn(),
  setStatus: vi.fn(),
  backendOk: true,
  getAttraction: vi.fn((id) => ({id: 1, name: 'Charminar', category: 'historical', lat: 17, lng: 78})),
  routingPayload: vi.fn(),
  resolveRoutingId: vi.fn((id) => id),
  resolveRoutingIds: vi.fn((ids) => ids),
  addCustomPlace: vi.fn(),
  removeCustomPlace: vi.fn(),
  mapPickActive: false,
  startMapPick: vi.fn(),
  cancelMapPick: vi.fn(),
  handleMapPick: vi.fn()
};

vi.mock('../src/context/AppContext', () => ({
  useApp: vi.fn(() => defaultMock)
}));

vi.mock('../src/components/MapView.jsx', () => {
  const React = require('react');
  return { default: () => React.createElement('div', { 'data-testid': 'map-view' }) };
});

const ProblemChild = () => {
  throw new Error('Test Error');
};

describe('ErrorBoundary', () => {
  it('renders children if no error', () => {
    render(<ErrorBoundary><div data-testid="child" /></ErrorBoundary>);
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('renders fallback if error', () => {
    const originalError = console.error;
    console.error = vi.fn();
    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    );
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    console.error = originalError;
  });
});

describe('PageLayout', () => {
  it('renders correctly', () => {
    useApp.mockReturnValue({
      routePath: [], attractions: [], startId: 0, goalIds: [],
      statusMsg: 'Status msg', loading: true, mapPickActive: false, handleMapPick: vi.fn()
    });
    
    render(
      <PageLayout title="Test Title" subtitle="Test Subtitle">
        <div data-testid="layout-child" />
      </PageLayout>
    );
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Subtitle')).toBeInTheDocument();
    expect(screen.getByText(/Working/i)).toBeInTheDocument();
    expect(screen.getByTestId('layout-child')).toBeInTheDocument();
    expect(screen.getByTestId('map-view')).toBeInTheDocument();
  });

  it('renders status message when not loading', () => {
    useApp.mockReturnValue({
      routePath: [], attractions: [], startId: 0, goalIds: [],
      statusMsg: 'Some Error', loading: false, mapPickActive: false, handleMapPick: vi.fn()
    });
    
    render(
      <PageLayout title="Test Title">
        <div data-testid="layout-child" />
      </PageLayout>
    );
    
    expect(screen.getByText('Some Error')).toBeInTheDocument();
  });
});
