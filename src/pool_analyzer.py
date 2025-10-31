"""Pool depth and liquidity analysis"""
import logging
from web3 import Web3
from typing import Dict, Optional, Tuple
from src.dex_config import UNISWAP_V2_PAIR_ABI, get_rpc_url

logger = logging.getLogger(__name__)


class PoolAnalyzer:
    """Analyzes pool liquidity depth and reserves"""

    def __init__(self):
        self.w3_connections = {}

    def get_w3(self, chain_id: int) -> Optional[Web3]:
        """Get Web3 connection for a chain"""
        if chain_id in self.w3_connections:
            return self.w3_connections[chain_id]

        rpc_url = get_rpc_url(chain_id)
        if not rpc_url:
            logger.error(f"No RPC URL for chain {chain_id}")
            return None

        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                self.w3_connections[chain_id] = w3
                return w3
            else:
                logger.error(f"Failed to connect to chain {chain_id}")
                return None
        except Exception as e:
            logger.error(f"Error connecting to chain {chain_id}: {e}")
            return None

    def get_pool_reserves(
        self, chain_id: int, pair_address: str, token_in: str, token_out: str
    ) -> Optional[Dict]:
        """
        Get pool reserves and calculate liquidity depth

        Returns:
            {
                "reserve_in": int,
                "reserve_out": int,
                "token_in_address": str,
                "token_out_address": str,
                "k": int  # constant product
            }
        """
        try:
            w3 = self.get_w3(chain_id)
            if not w3:
                return None

            # Create pair contract instance
            pair_contract = w3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=UNISWAP_V2_PAIR_ABI,
            )

            # Get reserves
            reserves = pair_contract.functions.getReserves().call()
            reserve0, reserve1, _ = reserves

            # Get token addresses from pair
            token0 = pair_contract.functions.token0().call()
            token1 = pair_contract.functions.token1().call()

            # Normalize addresses
            token_in_checksum = Web3.to_checksum_address(token_in)
            token_out_checksum = Web3.to_checksum_address(token_out)

            # Determine which reserve is which
            if token0.lower() == token_in_checksum.lower():
                reserve_in = reserve0
                reserve_out = reserve1
            elif token1.lower() == token_in_checksum.lower():
                reserve_in = reserve1
                reserve_out = reserve0
            else:
                logger.error(f"Token {token_in} not found in pair {pair_address}")
                return None

            # Calculate constant product k
            k = reserve_in * reserve_out

            return {
                "reserve_in": reserve_in,
                "reserve_out": reserve_out,
                "token_in_address": token_in_checksum,
                "token_out_address": token_out_checksum,
                "k": k,
            }

        except Exception as e:
            logger.error(f"Error getting reserves for pair {pair_address}: {e}")
            return None

    def calculate_output_amount(
        self, amount_in: int, reserve_in: int, reserve_out: int, fee_bps: int = 30
    ) -> int:
        """
        Calculate output amount using constant product formula with fees

        Args:
            amount_in: Input amount in wei
            reserve_in: Input token reserve
            reserve_out: Output token reserve
            fee_bps: Fee in basis points (default 30 = 0.3%)

        Returns:
            Output amount in wei
        """
        # Apply fee: amount_in_with_fee = amount_in * (10000 - fee_bps) / 10000
        amount_in_with_fee = amount_in * (10000 - fee_bps)

        # Uniswap V2 formula: amount_out = (amount_in_with_fee * reserve_out) / (reserve_in * 10000 + amount_in_with_fee)
        numerator = amount_in_with_fee * reserve_out
        denominator = (reserve_in * 10000) + amount_in_with_fee

        amount_out = numerator // denominator

        return amount_out

    def calculate_price_impact(
        self, amount_in: int, reserve_in: int, reserve_out: int
    ) -> float:
        """
        Calculate price impact as a percentage

        Args:
            amount_in: Input amount in wei
            reserve_in: Input token reserve
            reserve_out: Output token reserve

        Returns:
            Price impact as percentage (e.g., 1.5 for 1.5%)
        """
        if reserve_in == 0:
            return 100.0

        # Price impact = (amount_in / reserve_in) * 100
        price_impact = (amount_in / reserve_in) * 100

        return price_impact

    def estimate_liquidity_depth(
        self, reserve_in: int, reserve_out: int, decimals_in: int = 18, decimals_out: int = 18
    ) -> Dict:
        """
        Estimate liquidity depth metrics

        Args:
            reserve_in: Input token reserve
            reserve_out: Output token reserve
            decimals_in: Input token decimals
            decimals_out: Output token decimals

        Returns:
            {
                "reserve_in_tokens": float,
                "reserve_out_tokens": float,
                "liquidity_score": str,  # "low", "medium", "high"
                "recommended_max_trade": int  # in wei for <1% impact
            }
        """
        # Convert to token units
        reserve_in_tokens = reserve_in / (10 ** decimals_in)
        reserve_out_tokens = reserve_out / (10 ** decimals_out)

        # Calculate recommended max trade for <1% impact
        # amount_in / reserve_in = 0.01 => amount_in = reserve_in * 0.01
        recommended_max_trade = int(reserve_in * 0.01)

        # Liquidity scoring based on USD equivalent (simplified)
        # Assume reserve_in is in ETH equivalent for scoring
        liquidity_score = "low"
        if reserve_in_tokens > 100:
            liquidity_score = "high"
        elif reserve_in_tokens > 10:
            liquidity_score = "medium"

        return {
            "reserve_in_tokens": reserve_in_tokens,
            "reserve_out_tokens": reserve_out_tokens,
            "liquidity_score": liquidity_score,
            "recommended_max_trade": recommended_max_trade,
        }
