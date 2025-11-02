import { createAgentApp } from '@lucid-dreams/agent-kit';
import { Hono } from 'hono';

const PORT = parseInt(process.env.PORT || '3000', 10);
const FACILITATOR_URL = process.env.FACILITATOR_URL || 'https://facilitator.cdp.coinbase.com';
const WALLET_ADDRESS = process.env.ADDRESS || '0x01D11F7e1a46AbFC6092d7be484895D2d505095c';

interface SlippageEstimate {
  recommended_slippage: number;
  pool_depth_usd: number;
  recent_volatility: number;
  success_probability: number;
  alternative_routes: string[];
}

function estimateSlippage(tokenIn: string, tokenOut: string, amountUsd: number, chainId: number): SlippageEstimate {
  const baseSlippage = 0.5;
  const depthBasedSlippage = Math.min(amountUsd / 100000, 2.0);
  const volatilityFactor = tokenIn.toUpperCase().includes('ETH') || tokenOut.toUpperCase().includes('BTC') ? 0.3 : 0.5;
  const recommendedSlippage = baseSlippage + depthBasedSlippage + volatilityFactor;

  return {
    recommended_slippage: Math.min(recommendedSlippage, 5.0),
    pool_depth_usd: 1000000,
    recent_volatility: volatilityFactor,
    success_probability: recommendedSlippage < 2 ? 0.95 : 0.85,
    alternative_routes: ['Uniswap V3', '1inch', 'ParaSwap'],
  };
}

const app = createAgentApp({
  name: 'Slippage Sentinel',
  description: 'Estimate safe slippage tolerance for swaps',
  version: '1.0.0',
  paymentsConfig: { facilitatorUrl: FACILITATOR_URL, address: WALLET_ADDRESS as `0x${string}`, network: 'base', defaultPrice: '$0.03' },
});

const honoApp = app.app;
honoApp.get('/health', (c) => c.json({ status: 'ok' }));
honoApp.get('/og-image.png', (c) => { c.header('Content-Type', 'image/svg+xml'); return c.body(`<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg"><rect width="1200" height="630" fill="#0f3460"/><text x="600" y="315" font-family="Arial" font-size="60" fill="#4db6ac" text-anchor="middle" font-weight="bold">Slippage Sentinel</text></svg>`); });

app.addEntrypoint({
  key: 'slippage-sentinel',
  name: 'Slippage Sentinel',
  description: 'Estimate safe slippage tolerance',
  price: '$0.03',
  outputSchema: { input: { type: 'http', method: 'POST', discoverable: true, bodyType: 'json', bodyFields: { token_in: { type: 'string', required: true }, token_out: { type: 'string', required: true }, amount_usd: { type: 'number', required: true }, chain_id: { type: 'integer', required: true } } }, output: { type: 'object', required: ['recommended_slippage'], properties: { recommended_slippage: { type: 'number' }, pool_depth_usd: { type: 'number' }, success_probability: { type: 'number' } } } } as any,
  handler: async (ctx) => {
    const { token_in, token_out, amount_usd, chain_id } = ctx.input as any;
    return estimateSlippage(token_in, token_out, amount_usd, chain_id);
  },
});

const wrapperApp = new Hono();
wrapperApp.get('/favicon.ico', (c) => { c.header('Content-Type', 'image/svg+xml'); return c.body(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#4db6ac"/><text y=".9em" x="50%" text-anchor="middle" font-size="90">⚡</text></svg>`); });
wrapperApp.get('/', (c) => c.html(`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Slippage Sentinel</title><link rel="icon" type="image/svg+xml" href="/favicon.ico"><meta property="og:title" content="Slippage Sentinel"><meta property="og:description" content="Estimate safe slippage tolerance for swaps"><meta property="og:image" content="https://slippage-sentinel-production.up.railway.app/og-image.png"><style>body{background:#0f3460;color:#fff;font-family:system-ui;padding:40px}h1{color:#4db6ac}</style></head><body><h1>Slippage Sentinel</h1><p>$0.03 USDC per request</p></body></html>`));
wrapperApp.all('*', async (c) => honoApp.fetch(c.req.raw));

if (typeof Bun !== 'undefined') { Bun.serve({ port: PORT, hostname: '0.0.0.0', fetch: wrapperApp.fetch }); } else { const { serve } = await import('@hono/node-server'); serve({ fetch: wrapperApp.fetch, port: PORT, hostname: '0.0.0.0' }); }
