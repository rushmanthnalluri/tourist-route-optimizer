import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useApp } from '../src/context/AppContext';
import { AppProvider } from '../src/context/AppProvider';
import { api } from '../src/utils/api.js';

vi.mock('../src/utils/api.js', () => ({
  api: {
    getAttractions: vi.fn(),
    getGraph: vi.fn(),
  }
}));

const TestComponent = () => {
  const ctx = useApp();
  return (
    <div>
      <span data-testid="status">{ctx.statusMsg}</span>
      <span data-testid="backendOk">{ctx.backendOk === null ? 'null' : String(ctx.backendOk)}</span>
      <span data-testid="attractions-len">{ctx.attractions.length}</span>
      <button onClick={() => ctx.toggleGoal(2)}>Toggle Goal 2</button>
      <button onClick={() => {
        const id = ctx.addCustomPlace({ name: 'Custom', lat: 10, lng: 20 });
        ctx.toggleGoal(id);
      }}>Add Custom</button>
      <button onClick={() => ctx.removeCustomPlace(1000)}>Remove Custom 1000</button>
      <button onClick={() => ctx.startMapPick(vi.fn())}>Start Map Pick</button>
      <button onClick={() => ctx.handleMapPick(10, 20)}>Pick</button>
      <button onClick={() => ctx.cancelMapPick()}>Cancel Pick</button>
      <button onClick={() => ctx.setStartId(1000)}>Set Start</button>
      <span data-testid="resolved">{JSON.stringify(ctx.routingPayload())}</span>
    </div>
  );
};

const ErrorComponent = () => {
  useApp();
  return null;
};

describe('AppContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('throws error if used outside provider', () => {
    const originalError = console.error;
    console.error = vi.fn();
    expect(() => render(<ErrorComponent />)).toThrow('useApp must be used within AppProvider');
    console.error = originalError;
  });

  it('loads successfully', async () => {
    api.getAttractions.mockResolvedValue([{ id: 1, name: 'A', lat: 0, lng: 0 }]);
    api.getGraph.mockResolvedValue({ nodes: [1] });

    await act(async () => {
      render(
        <AppProvider>
          <TestComponent />
        </AppProvider>
      );
    });

    expect(screen.getByTestId('status').textContent).toBe('Ready');
    expect(screen.getByTestId('backendOk').textContent).toBe('true');
    expect(screen.getByTestId('attractions-len').textContent).toBe('1');
  });

  it('handles load error', async () => {
    api.getAttractions.mockRejectedValue(new Error('fail'));
    
    await act(async () => {
      render(
        <AppProvider>
          <TestComponent />
        </AppProvider>
      );
    });

    expect(screen.getByTestId('backendOk').textContent).toBe('false');
  });

  it('manipulates state properly', async () => {
    api.getAttractions.mockResolvedValue([{ id: 1, name: 'A', lat: 0, lng: 0 }]);
    api.getGraph.mockResolvedValue({ nodes: [1] });
    
    localStorage.setItem('hydai-custom-places', JSON.stringify([{ id: 999, name: 'Old', lat: 0, lng: 0 }]));

    await act(async () => {
      render(
        <AppProvider>
          <TestComponent />
        </AppProvider>
      );
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Toggle Goal 2'));
    });
    
    await act(async () => {
      fireEvent.click(screen.getByText('Add Custom'));
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Set Start'));
    });
    
    expect(screen.getByTestId('resolved').textContent).toContain('"start_id":1');

    await act(async () => {
      fireEvent.click(screen.getByText('Toggle Goal 2')); 
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Start Map Pick'));
    });
    await act(async () => {
      fireEvent.click(screen.getByText('Pick'));
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Start Map Pick'));
    });
    await act(async () => {
      fireEvent.click(screen.getByText('Cancel Pick'));
    });
    
    await act(async () => {
      fireEvent.click(screen.getByText('Remove Custom 1000'));
    });
  });

  it('handles bad local storage', async () => {
    api.getAttractions.mockResolvedValue([]);
    api.getGraph.mockResolvedValue({});
    localStorage.setItem('hydai-custom-places', '{bad}');
    await act(async () => {
      render(
        <AppProvider>
          <TestComponent />
        </AppProvider>
      );
    });
    expect(screen.getByTestId('attractions-len').textContent).toBe('0');
  });

  it('handles non-array local storage', async () => {
    api.getAttractions.mockResolvedValue([]);
    api.getGraph.mockResolvedValue({});
    localStorage.setItem('hydai-custom-places', JSON.stringify({ id: 1000, name: 'Bad shape' }));
    await act(async () => {
      render(
        <AppProvider>
          <TestComponent />
        </AppProvider>
      );
    });
    expect(screen.getByTestId('attractions-len').textContent).toBe('0');
  });
});
