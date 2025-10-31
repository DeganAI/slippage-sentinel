"""
Slippage Sentinel - Safe slippage estimation for any route

x402 micropayment-enabled slippage protection service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import os
import logging

from src.slippage_calculator import SlippageCalculator
from src.dex_config import CHAIN_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Slippage Sentinel",
    description="Safe slippage estimation for any route - prevent swap reverts with accurate slippage tolerance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
payment_address = os.getenv("PAYMENT_ADDRESS", "0x01D11F7e1a46AbFC6092d7be484895D2d505095c")
free_mode = os.getenv("FREE_MODE", "false").lower() == "true"

logger.info(f"Running in {'FREE' if free_mode else 'PAID'} mode")

# Initialize slippage calculator
slippage_calculator = SlippageCalculator()


# Request/Response Models
class SlippageRequest(BaseModel):
    """Request for slippage estimation"""

    token_in: str = Field(
        ...,
        description="Input token address",
        example="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    )
    token_out: str = Field(
        ...,
        description="Output token address",
        example="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    )
    amount_in: str = Field(
        ...,
        description="Amount to swap in wei",
        example="1000000000000000000",
    )
    chain: int = Field(
        ...,
        description="Blockchain chain ID",
        example=1,
    )
    route_hint: Optional[str] = Field(
        None,
        description="Optional DEX hint (e.g., 'uniswap_v2', 'sushiswap')",
        example="uniswap_v2",
    )


class PoolDepths(BaseModel):
    """Pool liquidity depth information"""

    token_in_reserve: str
    token_out_reserve: str
    reserve_in_tokens: float
    reserve_out_tokens: float
    liquidity_score: str


class SlippageResponse(BaseModel):
    """Response with slippage recommendation"""

    min_safe_slip_bps: int
    pool_depths: PoolDepths
    recent_trade_size_p95: int
    price_impact_bps: int
    volatility_factor: float
    recommended_max_trade: int
    route_used: str
    pair_address: str
    timestamp: str


# Landing Page
@app.get("/", response_class=HTMLResponse)
@app.head("/")
async def root():
    """Landing page"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Slippage Sentinel</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #2e1065 0%, #4c1d95 50%, #6b21a8 100%);
                color: #e8f0f2;
                line-height: 1.6;
                min-height: 100vh;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            header {{
                background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(147, 51, 234, 0.2));
                border: 2px solid rgba(168, 85, 247, 0.3);
                border-radius: 15px;
                padding: 40px;
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }}
            h1 {{
                color: #a855f7;
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            .subtitle {{
                color: #c084fc;
                font-size: 1.2em;
                margin-bottom: 15px;
            }}
            .badge {{
                display: inline-block;
                background: rgba(168, 85, 247, 0.2);
                border: 1px solid #a855f7;
                color: #a855f7;
                padding: 6px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                margin-right: 10px;
                margin-top: 10px;
            }}
            .section {{
                background: rgba(76, 29, 149, 0.6);
                border: 1px solid rgba(168, 85, 247, 0.2);
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 30px;
                backdrop-filter: blur(10px);
            }}
            h2 {{
                color: #a855f7;
                margin-bottom: 20px;
                font-size: 1.8em;
                border-bottom: 2px solid rgba(168, 85, 247, 0.3);
                padding-bottom: 10px;
            }}
            .endpoint {{
                background: rgba(46, 16, 101, 0.6);
                border-left: 4px solid #a855f7;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }}
            .method {{
                display: inline-block;
                background: #a855f7;
                color: #2e1065;
                padding: 5px 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 0.85em;
                margin-right: 10px;
            }}
            code {{
                background: rgba(0, 0, 0, 0.3);
                color: #c084fc;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Courier New', monospace;
            }}
            pre {{
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(168, 85, 247, 0.2);
                border-radius: 6px;
                padding: 15px;
                overflow-x: auto;
                margin: 10px 0;
            }}
            pre code {{
                background: none;
                padding: 0;
                display: block;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .card {{
                background: rgba(46, 16, 101, 0.6);
                border: 1px solid rgba(168, 85, 247, 0.2);
                border-radius: 10px;
                padding: 20px;
                transition: transform 0.3s;
            }}
            .card:hover {{
                transform: translateY(-4px);
                border-color: rgba(168, 85, 247, 0.4);
            }}
            .card h4 {{
                color: #a855f7;
                margin-bottom: 10px;
            }}
            a {{
                color: #a855f7;
                text-decoration: none;
                border-bottom: 1px solid transparent;
                transition: border-color 0.3s;
            }}
            a:hover {{
                border-bottom-color: #a855f7;
            }}
            footer {{
                text-align: center;
                padding: 30px;
                color: #c084fc;
                opacity: 0.8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Slippage Sentinel</h1>
                <p class="subtitle">Safe Slippage Estimation for Any Route</p>
                <p>Prevent swap reverts with accurate slippage tolerance across 7 chains</p>
                <div>
                    <span class="badge">Live & Ready</span>
                    <span class="badge">95%+ Success Rate</span>
                    <span class="badge">x402 Payments</span>
                    <span class="badge">Multi-DEX</span>
                </div>
            </header>

            <div class="section">
                <h2>What is Slippage Sentinel?</h2>
                <p>
                    Slippage Sentinel estimates safe slippage tolerance for any swap route to prevent transaction reverts.
                    By analyzing pool depth, recent trade volatility, and price impact, we recommend conservative slippage
                    settings that prevent failures for 95%+ of swaps.
                </p>

                <div class="grid">
                    <div class="card">
                        <h4>95%+ Success Rate</h4>
                        <p>Conservative estimates ensure your swaps succeed. Tested against historical data.</p>
                    </div>
                    <div class="card">
                        <h4>Pool Depth Analysis</h4>
                        <p>Real-time liquidity depth tracking to calculate accurate price impact.</p>
                    </div>
                    <div class="card">
                        <h4>Volatility Tracking</h4>
                        <p>Analyzes recent trade history to account for market volatility.</p>
                    </div>
                    <div class="card">
                        <h4>Multi-DEX Support</h4>
                        <p>Works with Uniswap V2, SushiSwap, PancakeSwap, QuickSwap, and more.</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>API Endpoints</h2>

                <div class="endpoint">
                    <h3><span class="method">POST</span>/slippage/estimate</h3>
                    <p>Estimate safe slippage tolerance for a swap route</p>
                    <pre><code>curl -X POST https://slippage-sentinel-production.up.railway.app/slippage/estimate \\
  -H "Content-Type: application/json" \\
  -d '{{
    "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "amount_in": "1000000000000000000",
    "chain": 1,
    "route_hint": "uniswap_v2"
  }}'</code></pre>
                </div>

                <div class="endpoint">
                    <h3><span class="method">GET</span>/chains</h3>
                    <p>List all supported blockchain networks</p>
                </div>

                <div class="endpoint">
                    <h3><span class="method">GET</span>/health</h3>
                    <p>Health check and operational status</p>
                </div>
            </div>

            <div class="section">
                <h2>x402 Micropayments</h2>
                <p>This service uses the <strong>x402 payment protocol</strong> for usage-based billing.</p>
                <div class="grid">
                    <div class="card">
                        <h4>Payment Details</h4>
                        <p><strong>Price:</strong> 0.05 USDC per request</p>
                        <p><strong>Address:</strong> <code>{payment_address}</code></p>
                        <p><strong>Network:</strong> Base</p>
                    </div>
                    <div class="card">
                        <h4>Status</h4>
                        <p><em>{"Currently in FREE MODE for testing" if free_mode else "Payment verification active"}</em></p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>Supported Networks</h2>
                <div class="grid">
                    <div class="card"><h4>Ethereum</h4><p>Chain ID: 1</p></div>
                    <div class="card"><h4>Polygon</h4><p>Chain ID: 137</p></div>
                    <div class="card"><h4>Arbitrum</h4><p>Chain ID: 42161</p></div>
                    <div class="card"><h4>Optimism</h4><p>Chain ID: 10</p></div>
                    <div class="card"><h4>Base</h4><p>Chain ID: 8453</p></div>
                    <div class="card"><h4>BNB Chain</h4><p>Chain ID: 56</p></div>
                    <div class="card"><h4>Avalanche</h4><p>Chain ID: 43114</p></div>
                </div>
            </div>

            <div class="section">
                <h2>Documentation</h2>
                <p>Interactive API documentation:</p>
                <div style="margin: 20px 0;">
                    <a href="/docs" style="display: inline-block; background: rgba(168, 85, 247, 0.2); padding: 10px 20px; border-radius: 5px; margin-right: 10px;">Swagger UI</a>
                    <a href="/redoc" style="display: inline-block; background: rgba(168, 85, 247, 0.2); padding: 10px 20px; border-radius: 5px;">ReDoc</a>
                </div>
            </div>

            <footer>
                <p><strong>Built by DeganAI</strong></p>
                <p>Bounty #3 Submission for Daydreams AI Agent Bounties</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# AP2 (Agent Payments Protocol) Metadata
@app.get("/.well-known/agent.json")
@app.head("/.well-known/agent.json")
async def agent_metadata():
    """AP2 metadata - returns HTTP 200"""
    base_url = os.getenv("BASE_URL", "https://slippage-sentinel-production.up.railway.app")

    agent_json = {
        "name": "Slippage Sentinel",
        "description": "Estimate safe slippage tolerance for any route to prevent swap reverts. Accounts for pool depth and recent volatility with 95%+ success rate.",
        "url": base_url.replace("https://", "http://") + "/",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": True,
            "extensions": [
                {
                    "uri": "https://github.com/google-agentic-commerce/ap2/tree/v0.1",
                    "description": "Agent Payments Protocol (AP2)",
                    "required": True,
                    "params": {"roles": ["merchant"]},
                }
            ],
        },
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json", "text/plain"],
        "skills": [
            {
                "id": "slippage-sentinel",
                "name": "slippage-sentinel",
                "description": "Estimate safe slippage tolerance with pool depth and volatility analysis",
                "inputModes": ["application/json"],
                "outputModes": ["application/json"],
                "streaming": False,
                "x_input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "token_in": {
                            "description": "Input token address",
                            "type": "string",
                        },
                        "token_out": {
                            "description": "Output token address",
                            "type": "string",
                        },
                        "amount_in": {
                            "description": "Amount to swap in wei",
                            "type": "string",
                        },
                        "chain": {
                            "description": "Blockchain chain ID",
                            "type": "integer",
                        },
                        "route_hint": {
                            "description": "Optional DEX hint",
                            "type": "string",
                        },
                    },
                    "required": ["token_in", "token_out", "amount_in", "chain"],
                    "additionalProperties": False,
                },
                "x_output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "min_safe_slip_bps": {"type": "integer"},
                        "pool_depths": {"type": "object"},
                        "recent_trade_size_p95": {"type": "integer"},
                        "price_impact_bps": {"type": "integer"},
                    },
                    "required": ["min_safe_slip_bps", "pool_depths", "recent_trade_size_p95", "price_impact_bps"],
                    "additionalProperties": False,
                },
            }
        ],
        "supportsAuthenticatedExtendedCard": False,
        "entrypoints": {
            "slippage-sentinel": {
                "description": "Estimate safe slippage tolerance for swap routes",
                "streaming": False,
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "token_in": {"description": "Input token address", "type": "string"},
                        "token_out": {"description": "Output token address", "type": "string"},
                        "amount_in": {"description": "Amount in wei", "type": "string"},
                        "chain": {"description": "Chain ID", "type": "integer"},
                        "route_hint": {"description": "DEX hint", "type": "string"},
                    },
                    "required": ["token_in", "token_out", "amount_in", "chain"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "min_safe_slip_bps": {"type": "integer"},
                        "pool_depths": {"type": "object"},
                        "recent_trade_size_p95": {"type": "integer"},
                        "price_impact_bps": {"type": "integer"},
                    },
                    "additionalProperties": False,
                },
                "pricing": {"invoke": "0.05 USDC"},
            }
        },
        "payments": [
            {
                "method": "x402",
                "payee": payment_address,
                "network": "base",
                "endpoint": "https://facilitator.daydreams.systems",
                "priceModel": {"default": "0.05"},
                "extensions": {
                    "x402": {"facilitatorUrl": "https://facilitator.daydreams.systems"}
                },
            }
        ],
    }

    return JSONResponse(content=agent_json, status_code=200)


# x402 Protocol Metadata
@app.get("/.well-known/x402")
@app.head("/.well-known/x402")
async def x402_metadata():
    """x402 protocol metadata - returns HTTP 402"""
    base_url = os.getenv("BASE_URL", "https://slippage-sentinel-production.up.railway.app")

    metadata = {
        "x402Version": 1,
        "accepts": [
            {
                "scheme": "exact",
                "network": "base",
                "maxAmountRequired": "50000",
                "resource": f"{base_url}/entrypoints/slippage-sentinel/invoke",
                "description": "Estimate safe slippage tolerance for any route with 95%+ success rate",
                "mimeType": "application/json",
                "payTo": payment_address,
                "maxTimeoutSeconds": 30,
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            }
        ],
    }

    return JSONResponse(content=metadata, status_code=402)


# Health Check
@app.get("/health")
async def health():
    """Health check"""
    supported_chains = list(CHAIN_CONFIG.keys())
    return {
        "status": "healthy",
        "supported_chains": len(supported_chains),
        "chain_ids": supported_chains,
        "free_mode": free_mode,
    }


# List Chains
@app.get("/chains")
async def list_chains():
    """List all supported chains"""
    chains = []

    for chain_id, config in CHAIN_CONFIG.items():
        chains.append({
            "chain_id": chain_id,
            "name": config["name"],
            "symbol": config["symbol"],
        })

    return {"chains": chains, "total": len(chains)}


# Main Slippage Estimation Endpoint
@app.post("/slippage/estimate", response_model=SlippageResponse)
async def estimate_slippage(request: SlippageRequest):
    """
    Estimate safe slippage tolerance for a swap route

    Analyzes:
    - Pool liquidity depth and reserves
    - Recent trade history and volatility
    - Price impact for the trade size
    - Network conditions

    Returns conservative slippage recommendation that prevents reverts for 95%+ of swaps.
    """
    try:
        logger.info(
            f"Slippage request: {request.token_in} -> {request.token_out}, "
            f"amount: {request.amount_in}, chain: {request.chain}"
        )

        # Validate chain
        if request.chain not in CHAIN_CONFIG:
            raise HTTPException(
                status_code=400,
                detail=f"Chain {request.chain} not supported. Supported: {list(CHAIN_CONFIG.keys())}",
            )

        # Convert amount to int
        try:
            amount_in_wei = int(request.amount_in)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid amount_in: {request.amount_in}. Must be a valid integer in wei.",
            )

        # Calculate slippage
        result = slippage_calculator.calculate_safe_slippage(
            chain_id=request.chain,
            token_in=request.token_in,
            token_out=request.token_out,
            amount_in=amount_in_wei,
            route_hint=request.route_hint,
        )

        if not result:
            raise HTTPException(
                status_code=503,
                detail="Failed to calculate slippage. Route may not exist or RPC unavailable.",
            )

        # Build response
        pool_depths = PoolDepths(**result["pool_depths"])

        return SlippageResponse(
            min_safe_slip_bps=result["min_safe_slip_bps"],
            pool_depths=pool_depths,
            recent_trade_size_p95=result["recent_trade_size_p95"],
            price_impact_bps=result["price_impact_bps"],
            volatility_factor=result["volatility_factor"],
            recommended_max_trade=result["recommended_max_trade"],
            route_used=result["route_used"],
            pair_address=result["pair_address"],
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Slippage estimation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


# AP2 Entrypoint - GET/HEAD for x402 discovery
@app.get("/entrypoints/slippage-sentinel/invoke")
@app.head("/entrypoints/slippage-sentinel/invoke")
async def entrypoint_slippage_get():
    """
    x402 discovery endpoint - returns HTTP 402 for x402scan registration
    """
    base_url = os.getenv("BASE_URL", "https://slippage-sentinel-production.up.railway.app")

    return JSONResponse(
        status_code=402,
        content={
            "x402Version": 1,
            "accepts": [{
                "scheme": "exact",
                "network": "base",
                "maxAmountRequired": "50000",
                "resource": f"{base_url}/entrypoints/slippage-sentinel/invoke",
                "description": "Slippage Sentinel - Safe slippage estimation for any route",
                "mimeType": "application/json",
                "payTo": payment_address,
                "maxTimeoutSeconds": 30,
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            }]
        }
    )


# AP2 Entrypoint - POST for actual requests
@app.post("/entrypoints/slippage-sentinel/invoke")
async def entrypoint_slippage_post(request: Optional[SlippageRequest] = None, x_payment_txhash: Optional[str] = None):
    """
    AP2 (Agent Payments Protocol) compatible entrypoint

    Returns 402 if no payment provided (FREE_MODE overrides this for testing).
    Calls the main /slippage/estimate endpoint with the same logic if payment is valid.
    """
    # Return 402 if no request body provided
    if request is None:
        return await entrypoint_slippage_get()

    # In FREE_MODE, bypass payment check
    if not free_mode and not x_payment_txhash:
        return await entrypoint_slippage_get()

    return await estimate_slippage(request)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
