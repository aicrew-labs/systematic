/**
 * API client for Quote Intelligence backend.
 * All calls go through Vite's proxy → http://localhost:8000
 */

const BASE = 'http://localhost:8000/api/v1';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res.json();
}

export async function getCustomers() {
  return request('/customers');
}

export async function getProducts() {
  return request('/products');
}

export async function getDailyRates() {
  return request('/rates');
}

export async function setDailyRates(rates) {
  return request('/rates', {
    method: 'POST',
    body: JSON.stringify(rates),
  });
}

export async function getQuoteSuggestion(data) {
  return request('/analyze', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
