import { describe, it, expect, vi, beforeEach } from 'vitest';
import { haversineKm, nearestAttractionId } from '../src/utils/geo.js';
import { api } from '../src/utils/api.js';

describe('geo.js', () => {
  it('haversineKm works', () => {
    const d = haversineKm(0, 0, 0, 1);
    expect(d).toBeGreaterThan(0);
  });

  it('nearestAttractionId works with empty array', () => {
    expect(nearestAttractionId(0, 0, [])).toBe(0);
  });

  it('nearestAttractionId works with items', () => {
    const attractions = [
      { id: 1, lat: 0, lng: 0, isCustom: true },
      { id: 2, lat: 0, lng: 1, isCustom: false },
      { id: 3, lat: 0, lng: 5, isCustom: false }
    ];
    expect(nearestAttractionId(0, 0.5, attractions)).toBe(2);
  });
});
