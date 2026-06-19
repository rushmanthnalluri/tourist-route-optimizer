import { describe, it, expect, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const mockUse = vi.fn();
  const mockGet = vi.fn().mockResolvedValue({ data: 'get_data' });
  const mockPost = vi.fn().mockResolvedValue({ data: 'post_data' });
  const mockCreate = vi.fn().mockReturnValue({
    interceptors: {
      response: { use: mockUse }
    },
    get: mockGet,
    post: mockPost
  });

  const mockAxiosRetry = vi.fn();
  mockAxiosRetry.exponentialDelay = vi.fn();
  mockAxiosRetry.isNetworkOrIdempotentRequestError = vi.fn().mockReturnValue(false);

  return { mockCreate, mockUse, mockAxiosRetry };
});

vi.mock('axios', () => {
  return {
    default: {
      create: mocks.mockCreate
    }
  };
});

vi.mock('axios-retry', () => {
  return {
    default: Object.assign(mocks.mockAxiosRetry, {
      exponentialDelay: mocks.mockAxiosRetry.exponentialDelay,
      isNetworkOrIdempotentRequestError: mocks.mockAxiosRetry.isNetworkOrIdempotentRequestError
    })
  };
});

import { api } from '../src/utils/api.js';

describe('api.js', () => {
  it('calls all endpoints correctly', async () => {
    expect(await api.getAttractions()).toBe('get_data');
    expect(await api.getGraph()).toBe('get_data');
    expect(await api.runSearch({})).toBe('post_data');
    expect(await api.compareSearch({})).toBe('post_data');
    expect(await api.scheduleCSP({})).toBe('post_data');
    expect(await api.computeUtility({})).toBe('post_data');
    expect(await api.runMinimax({})).toBe('post_data');
    expect(await api.expectedUtility({})).toBe('post_data');
    expect(await api.bayesUpdate({})).toBe('post_data');
    expect(await api.infer({})).toBe('post_data');
    expect(await api.hmmTrack({})).toBe('post_data');
    expect(await api.hybridPlan({})).toBe('post_data');
  });

  it('tests interceptors', () => {
    const successHandler = mocks.mockUse.mock.calls[0][0];
    const errorHandler = mocks.mockUse.mock.calls[0][1];

    expect(successHandler('ok')).toBe('ok');

    expect(() => errorHandler({ response: { data: { message: 'err' }, status: 400 } })).toThrow('err');
    expect(() => errorHandler({ response: { status: 500 } })).toThrow('API Error 500');
    expect(() => errorHandler({ request: {} })).toThrow('Network error or request timeout');
    expect(() => errorHandler({ message: 'other' })).toThrow('other');
  });

  it('tests axios-retry condition', () => {
    const retryOpts = mocks.mockAxiosRetry.mock.calls[0][1];
    const cond = retryOpts.retryCondition;
    
    expect(cond({})).toBe(false);
    expect(cond({ config: { method: 'get' }, response: { status: 429 } })).toBe(true);
    
    mocks.mockAxiosRetry.isNetworkOrIdempotentRequestError.mockReturnValueOnce(true);
    expect(cond({ config: { method: 'get' } })).toBe(true);
  });
});
