import { describe, it, expect, vi } from 'vitest';
import React from 'react';

vi.mock('react-dom/client', () => ({
  default: {
    createRoot: vi.fn().mockReturnValue({ render: vi.fn() })
  }
}));

vi.mock('../src/App.jsx', () => ({ default: () => <div>App</div> }));

describe('main.jsx', () => {
  it('renders root', async () => {
    const root = document.createElement('div');
    root.id = 'root';
    document.body.appendChild(root);

    await import('../src/main.jsx');
    
    expect(root).toBeInTheDocument();
  });
});
