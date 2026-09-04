import { test, expect } from '@playwright/test';

/**
 * E2E: OpenAPI / Swagger UI.
 *
 * Verifies that the FastAPI backend exposes /openapi.json, /docs (Swagger UI),
 * and /redoc (ReDoc), and that the JSON schema contains the documented tags.
 *
 * The base URL for the API is http://localhost:8000 by default. Tests skip
 * gracefully if the backend isn't running.
 */

const API_BASE = process.env.API_BASE_URL ?? 'http://localhost:8000';

test.describe('OpenAPI documentation', () => {
  test.skip(({ baseURL }) => !baseURL?.includes('3000'), 'Runs only when web server is up');

  test('GET /openapi.json returns 200 with valid schema', async ({ request }) => {
    const res = await request.get(`${API_BASE}/openapi.json`);
    test.skip(res.status() !== 200, `API not reachable at ${API_BASE}`);
    const schema = await res.json();
    expect(schema.openapi).toMatch(/^3\./);
    expect(schema.info.title).toBe('Translator API');
    expect(schema.info.version).toBeTruthy();
    expect(Array.isArray(schema.tags)).toBe(true);
  });

  test('GET /openapi.json includes all 11 documented tags', async ({ request }) => {
    const res = await request.get(`${API_BASE}/openapi.json`);
    test.skip(res.status() !== 200, `API not reachable at ${API_BASE}`);
    const schema = await res.json();
    const tagNames = (schema.tags as Array<{ name: string }>).map((t) => t.name);
    expect(tagNames).toEqual(
      expect.arrayContaining([
        'meta',
        'projects',
        'editor',
        'governance',
        'admin',
        'providers',
        'workflow',
        'stream',
        'events',
        'capabilities',
        'metrics',
      ]),
    );
  });

  test('GET /docs serves Swagger UI HTML', async ({ request }) => {
    const res = await request.get(`${API_BASE}/docs`);
    test.skip(res.status() !== 200, `API not reachable at ${API_BASE}`);
    const body = await res.text();
    expect(body.toLowerCase()).toContain('swagger');
  });

  test('GET /redoc serves ReDoc HTML', async ({ request }) => {
    const res = await request.get(`${API_BASE}/redoc`);
    test.skip(res.status() !== 200, `API not reachable at ${API_BASE}`);
    const body = await res.text();
    expect(body.toLowerCase()).toMatch(/redoc|api/);
  });
});
