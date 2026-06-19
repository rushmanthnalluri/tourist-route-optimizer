import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../src/App';
import { describe, it, expect, vi } from 'vitest';

vi.mock('../src/utils/api', () => ({
  api: {
    getAttractions: vi.fn().mockResolvedValue([]),
    getGraph: vi.fn().mockResolvedValue({ nodes: [], edges: [] }),
    runSearch: vi.fn().mockResolvedValue({ success: true, path: [1, 2] }),
    scheduleCSP: vi.fn().mockResolvedValue({ success: true, schedule: [] }),
    computeUtility: vi.fn().mockResolvedValue({ utility: 100 }),
    runMinimax: vi.fn().mockResolvedValue({ recommendation: 1 }),
    expectedUtility: vi.fn().mockResolvedValue({ expected_utility: 50 }),
    bayesUpdate: vi.fn().mockResolvedValue({ crowd_level: 'High' }),
    infer: vi.fn().mockResolvedValue({ satisfaction: 0.9 }),
    hmmTrack: vi.fn().mockResolvedValue({ state: 'moving' }),
    hybridPlan: vi.fn().mockResolvedValue({ success: true, path: [1, 2] })
  }
}));

describe('App Test', () => {
  it('renders without crashing', async () => {
    await act(async () => {
      render(
        <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }} initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );
    });
    expect(screen.getAllByText(/HydAI/i)[0]).toBeInTheDocument();
  });
});
