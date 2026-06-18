import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import MapView from '../src/components/MapView.jsx';
import AttractionSidebar from '../src/components/AttractionSidebar.jsx';
import DestinationSearch from '../src/components/DestinationSearch.jsx';
import TraceViewer from '../src/components/TraceViewer.jsx';
import NavSidebar from '../src/components/NavSidebar.jsx';
import { useApp } from '../src/context/AppContext';

vi.mock('react-leaflet', () => {
  const React = require('react');
  const div = (props) => React.createElement('div', props, props.children);
  return {
    MapContainer: div, TileLayer: div, Marker: div, Popup: div,
    Polyline: div, useMap: vi.fn(), useMapEvents: vi.fn()
  };
});

vi.mock('leaflet', () => ({
  default: {
    icon: vi.fn(),
    divIcon: vi.fn(),
    Icon: {
      Default: {
        prototype: { _getIconUrl: '' },
        mergeOptions: vi.fn()
      }
    }
  }
}));

vi.mock('../src/context/AppContext', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useApp: () => ({
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
    })
  };
});

const Wrap = ({ children }) => (
  <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>{children}</MemoryRouter>
);

describe('Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
    HTMLElement.prototype.scrollIntoView = vi.fn();
  });
  it('renders MapView', async () => {
    await act(async () => {
      render(<MapView attractions={[]} goalIds={[]} routePath={[]} onMapPick={vi.fn()} />, { wrapper: Wrap });
    });
  });

  it('renders AttractionSidebar', async () => {
    await act(async () => {
      render(<AttractionSidebar attractions={[]} goalIds={[]} routePath={[]} onSetStart={vi.fn()} onToggleGoal={vi.fn()} />, { wrapper: Wrap });
    });
  });

  it('renders DestinationSearch', async () => {
    await act(async () => {
      render(<DestinationSearch />, { wrapper: Wrap });
    });
  });

  it('renders TraceViewer', async () => {
    await act(async () => {
      render(<TraceViewer trace={[{step:1}]} />, { wrapper: Wrap });
    });
  });

  it('renders NavSidebar', async () => {
    await act(async () => {
      render(<NavSidebar />, { wrapper: Wrap });
    });
  });
});
