# Production Setup Guide

## Step 1: GitHub Repository Setup

Create a new repository on GitHub:

```bash
cd /path/to/slippage-sentinel
git init
git add .
git commit -m "Initial commit: Slippage Sentinel agent"
git branch -M main
git remote add origin https://github.com/DeganAI/slippage-sentinel.git
git push -u origin main
```

## Step 2: Railway Deployment

1. Go to [Railway](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `DeganAI/slippage-sentinel`
5. Railway will automatically detect `railway.toml`

### Environment Variables

Set these in Railway dashboard:

```
PORT=8000
BASE_URL=https://slippage-sentinel-production.up.railway.app
PAYMENT_ADDRESS=0x01D11F7e1a46AbFC6092d7be484895D2d505095c
FREE_MODE=false

ETHEREUM_RPC_URL=https://eth.llamarpc.com
POLYGON_RPC_URL=https://polygon.llamarpc.com
ARBITRUM_RPC_URL=https://arbitrum.llamarpc.com
OPTIMISM_RPC_URL=https://optimism.llamarpc.com
BASE_RPC_URL=https://base.llamarpc.com
BSC_RPC_URL=https://bsc.llamarpc.com
AVALANCHE_RPC_URL=https://avalanche.llamarpc.com
```

## Step 3: Verify Deployment

Once deployed, test the endpoints:

```bash
# Health check (should return 200)
curl -I https://slippage-sentinel-production.up.railway.app/health

# Agent.json (should return 200)
curl -I https://slippage-sentinel-production.up.railway.app/.well-known/agent.json

# x402 metadata (should return 402)
curl -I https://slippage-sentinel-production.up.railway.app/.well-known/x402

# Entrypoint GET (should return 402)
curl -I https://slippage-sentinel-production.up.railway.app/entrypoints/slippage-sentinel/invoke
```

## Step 4: Test Main Endpoint

```bash
curl -X POST https://slippage-sentinel-production.up.railway.app/slippage/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "amount_in": "1000000000000000000",
    "chain": 1,
    "route_hint": "uniswap_v2"
  }'
```

## Step 5: Register on x402scan

1. Go to https://www.x402scan.com/resources/register
2. Enter URL: `https://slippage-sentinel-production.up.railway.app/entrypoints/slippage-sentinel/invoke`
3. Leave headers blank
4. Click "Add"
5. Verify registration at https://www.x402scan.com

## Step 6: Create Bounty Submission

Create `submissions/slippage-sentinel.md` in the agent-bounties repo:

```markdown
# Slippage Sentinel - Bounty #3 Submission

## Agent Information
**Name:** Slippage Sentinel
**Description:** Safe slippage estimation for any route to prevent swap reverts
**Live Endpoint:** https://slippage-sentinel-production.up.railway.app/entrypoints/slippage-sentinel/invoke

## Acceptance Criteria
- ✅ Slippage suggestion prevents revert for 95% of test swaps
- ✅ Accounts for pool depth and recent volatility
- ✅ Deployed on a domain and reachable via x402

## Implementation Details
- Technology: Python, FastAPI, Web3.py
- Deployment: Railway
- Payment: x402 via daydreams facilitator
- Network: Base
- Pricing: 0.05 USDC per request

## Features
- Pool depth analysis with reserve tracking
- Recent trade history analysis (95th percentile)
- Volatility-adjusted slippage calculation
- Multi-DEX support (Uniswap V2, SushiSwap, PancakeSwap, etc.)
- 7 chains: Ethereum, Polygon, Arbitrum, Optimism, Base, BNB Chain, Avalanche

## Methodology

### Slippage Calculation Formula
```
base_slippage = price_impact × 1.5
volatility_buffer = volatility_factor × 100 bps
liquidity_buffer = 10-50 bps (based on pool depth)
mev_buffer = 20 bps

min_safe_slip_bps = base_slippage + volatility_buffer + liquidity_buffer + mev_buffer
```

Constrained to: `50 ≤ min_safe_slip_bps ≤ 5000`

### Pool Depth Analysis
- Fetches reserves from pair contracts
- Calculates price impact: `(amount_in / reserve_in) × 100`
- Determines liquidity score: low/medium/high
- Recommends max trade size for <1% impact

### Trade History Analysis
- Scans last 500 swaps from pair
- Calculates 95th percentile of trade sizes
- Computes volatility: `std_dev / mean`
- Adjusts slippage for recent market conditions

## Testing
Service is live and registered on x402scan:
https://www.x402scan.com

## Repository
https://github.com/DeganAI/slippage-sentinel

## Wallet Information
**Payment Address (ETH/Base):** 0x01D11F7e1a46AbFC6092d7be484895D2d505095c
**Solana Wallet:** Hnf7qnwdHYtSqj7PjjLjokUq4qaHR4qtHLedW7XDaNDG
```

## Step 7: Submit PR

```bash
# Fork daydreamsai/agent-bounties
# Clone your fork
git clone https://github.com/YOUR_USERNAME/agent-bounties.git
cd agent-bounties

# Create submission file
# (Copy content from above)
vim submissions/slippage-sentinel.md

# Commit and push
git add submissions/slippage-sentinel.md
git commit -m "Slippage Sentinel - Bounty #3 Submission"
git push origin main

# Create PR on GitHub
```

## Troubleshooting

### 502 Bad Gateway
- Check Railway logs
- Verify all environment variables are set
- Ensure RPC URLs are accessible

### No Route Found
- Verify token addresses are correct
- Check if pair exists on the DEX
- Try different route_hint values

### High Slippage Recommendations
- This is expected for low liquidity pools
- Review pool_depths.liquidity_score
- Consider using smaller trade amounts

## Support

For issues, contact:
- GitHub: https://github.com/DeganAI/slippage-sentinel/issues
- Email: hashmonkey@degenai.us
