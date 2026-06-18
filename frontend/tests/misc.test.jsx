import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AttractionSidebar from '../src/components/AttractionSidebar.jsx';
import DestinationSearch from '../src/components/DestinationSearch.jsx';
import TraceViewer from '../src/components/TraceViewer.jsx';
import NavSidebar from '../src/components/NavSidebar.jsx';

import { MemoryRouter } from 'react-router-dom';
import { AppProvider } from '../src/context/AppProvider';

vi.mock('../src/utils/api.js', () => ({
  api: {
    getAttractions: vi.fn().mockResolvedValue([]),
    getGraph: vi.fn().mockResolvedValue({}),
  }
}));

const Wrap = ({ children }) => (
  <MemoryRouter>
    <AppProvider>
      {children}
    </AppProvider>
  </MemoryRouter>
);

describe('Misc Components', () => {
  beforeEach(() => {
    HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  describe('AttractionSidebar', () => {
    it('handles search, filter, click', () => {
      const attractions = [
        { id: 1, name: 'Charminar', category: 'historical', rating: 4, entry_cost: 0, duration_min: 30 },
        { id: 2, name: 'Golconda', category: 'historical', rating: 5, entry_cost: 100, duration_min: 60 }
      ];
      const onSetStart = vi.fn();
      const onToggleGoal = vi.fn();
      
      render(
        <AttractionSidebar 
          attractions={attractions} startId={1} goalIds={[2]} 
          onSetStart={onSetStart} onToggleGoal={onToggleGoal} 
        />
      );

      fireEvent.change(screen.getByPlaceholderText('Search...'), { target: { value: 'Golconda' } });
      fireEvent.change(screen.getByRole('combobox'), { target: { value: 'historical' } });
      fireEvent.change(screen.getByRole('combobox'), { target: { value: 'all' } });

      fireEvent.click(screen.getAllByText(/Start/i)[0]);
      fireEvent.click(screen.getAllByText(/Goal/i)[0]);
      
      expect(onSetStart).toHaveBeenCalledWith(2);
      expect(onToggleGoal).toHaveBeenCalledWith(2);
    });
  });

  describe('DestinationSearch', () => {
    it('handles actions', async () => {
      await act(async () => {
        render(<DestinationSearch />, { wrapper: Wrap });
      });

      await act(async () => {
        fireEvent.change(screen.getByPlaceholderText(/Search/i), { target: { value: 'hotel' } });
      });

      await act(async () => {
        fireEvent.keyDown(screen.getByPlaceholderText(/Search/i), { key: 'Enter' });
      });

      await act(async () => {
        fireEvent.click(screen.getByText('Add custom place'));
      });
      
      await act(async () => {
        fireEvent.click(screen.getByText('Pick on map'));
      });
      
      await act(async () => {
        fireEvent.click(screen.getByText('Cancel map pick'));
      });
    });
  });

  describe('TraceViewer', () => {
    it('renders and paginates trace', () => {
      const trace = Array.from({ length: 12 }, (_, i) => ({
        step: i, node: i, f: 1, g: 1, h: 1, queue_len: 1, action: 'expand', open_set: [1]
      }));

      render(<TraceViewer trace={trace} />);
      const buttons = screen.getAllByRole('button');
      if (buttons.length > 0) fireEvent.click(buttons[0]);
      
      render(<TraceViewer trace={[{ step: 1, state: 'x', observation: 'y', belief: {} }]} />);
    });
  });

  describe('NavSidebar', () => {
    it('renders with ok backend', async () => {
      await act(async () => {
        render(<NavSidebar />, { wrapper: Wrap });
      });
      expect(screen.getByText('Home')).toBeInTheDocument();
    });
  });
});
