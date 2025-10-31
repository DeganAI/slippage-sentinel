#!/bin/bash

# Slippage Sentinel - Endpoint Testing Script

BASE_URL="${BASE_URL:-https://slippage-sentinel-production.up.railway.app}"

echo "Testing Slippage Sentinel endpoints..."
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Health Check
echo "1. Testing /health (should return 200)..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BASE_URL/health"
echo ""

# Test 2: Landing Page
echo "2. Testing / (should return 200)..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BASE_URL/"
echo ""

# Test 3: Agent.json (should return 200)
echo "3. Testing /.well-known/agent.json (should return 200)..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BASE_URL/.well-known/agent.json"
echo ""

# Test 4: x402 metadata (should return 402)
echo "4. Testing /.well-known/x402 (should return 402)..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BASE_URL/.well-known/x402"
echo ""

# Test 5: Entrypoint GET (should return 402)
echo "5. Testing /entrypoints/slippage-sentinel/invoke GET (should return 402)..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BASE_URL/entrypoints/slippage-sentinel/invoke"
echo ""

# Test 6: Entrypoint HEAD (should return 402)
echo "6. Testing /entrypoints/slippage-sentinel/invoke HEAD (should return 402)..."
curl -s -o /dev/null -w "Status: %{http_code}\n" -I "$BASE_URL/entrypoints/slippage-sentinel/invoke"
echo ""

# Test 7: List chains
echo "7. Testing /chains..."
curl -s "$BASE_URL/chains" | python3 -m json.tool | head -20
echo ""

# Test 8: Main endpoint - WETH/USDC on Ethereum
echo "8. Testing /slippage/estimate (WETH/USDC on Ethereum)..."
curl -s -X POST "$BASE_URL/slippage/estimate" \
  -H "Content-Type: application/json" \
  -d '{
    "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "amount_in": "1000000000000000000",
    "chain": 1,
    "route_hint": "uniswap_v2"
  }' | python3 -m json.tool
echo ""

# Test 9: Agent.json content
echo "9. Checking agent.json structure..."
AGENT_JSON=$(curl -s "$BASE_URL/.well-known/agent.json")
echo "  - Has 'name' field: $(echo $AGENT_JSON | grep -q '\"name\"' && echo 'YES' || echo 'NO')"
echo "  - Has 'url' field with http://: $(echo $AGENT_JSON | grep -q '\"url\".*http://' && echo 'YES' || echo 'NO')"
echo "  - Has 'payments' field: $(echo $AGENT_JSON | grep -q '\"payments\"' && echo 'YES' || echo 'NO')"
echo "  - Has facilitator URL: $(echo $AGENT_JSON | grep -q 'facilitator.daydreams.systems' && echo 'YES' || echo 'NO')"
echo ""

# Test 10: x402 metadata content
echo "10. Checking x402 metadata structure..."
X402_JSON=$(curl -s "$BASE_URL/.well-known/x402")
echo "  - Has 'x402Version' field: $(echo $X402_JSON | grep -q '\"x402Version\"' && echo 'YES' || echo 'NO')"
echo "  - Has 'accepts' array: $(echo $X402_JSON | grep -q '\"accepts\"' && echo 'YES' || echo 'NO')"
echo "  - Has 'scheme' field: $(echo $X402_JSON | grep -q '\"scheme\"' && echo 'YES' || echo 'NO')"
echo "  - Has 'network' field: $(echo $X402_JSON | grep -q '\"network\"' && echo 'YES' || echo 'NO')"
echo "  - Has 'payTo' field: $(echo $X402_JSON | grep -q '\"payTo\"' && echo 'YES' || echo 'NO')"
echo "  - Has 'asset' field: $(echo $X402_JSON | grep -q '\"asset\"' && echo 'YES' || echo 'NO')"
echo ""

echo "Testing complete!"
