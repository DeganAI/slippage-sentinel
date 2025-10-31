"""Core slippage calculation logic"""
import logging
from typing import Dict, Optional
from src.pool_analyzer import PoolAnalyzer
from src.trade_history import TradeHistoryAnalyzer
from src.route_finder import RouteFinder

logger = logging.getLogger(__name__)


class SlippageCalculator:
    """Calculates safe slippage tolerance for routes"""

    def __init__(self):
        self.pool_analyzer = PoolAnalyzer()
        self.trade_analyzer = TradeHistoryAnalyzer()
        self.route_finder = RouteFinder()

    def calculate_safe_slippage(
        self,
        chain_id: int,
        token_in: str,
        token_out: str,
        amount_in: int,
        route_hint: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Calculate safe slippage tolerance for a swap

        Args:
            chain_id: Blockchain chain ID
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount to swap in wei
            route_hint: Optional DEX hint

        Returns:
            {
                "min_safe_slip_bps": int,
                "pool_depths": dict,
                "recent_trade_size_p95": int,
                "price_impact_bps": int,
                "volatility_factor": float,
                "recommended_max_trade": int,
                "route_used": str,
                "pair_address": str,
            }
        """
        try:
            # Find best route
            route = self.route_finder.find_best_route(
                chain_id, token_in, token_out, route_hint
            )

            if not route:
                logger.error(f"No route found for {token_in}/{token_out} on chain {chain_id}")
                return None

            pair_address = route["pair_address"]
            dex_name = route["dex_name"]

            # Get pool reserves
            reserves = self.pool_analyzer.get_pool_reserves(
                chain_id, pair_address, token_in, token_out
            )

            if not reserves:
                logger.error(f"Failed to get reserves for pair {pair_address}")
                return None

            reserve_in = reserves["reserve_in"]
            reserve_out = reserves["reserve_out"]

            # Calculate price impact
            price_impact_pct = self.pool_analyzer.calculate_price_impact(
                amount_in, reserve_in, reserve_out
            )
            price_impact_bps = int(price_impact_pct * 100)  # Convert to basis points

            # Get liquidity depth metrics
            liquidity_metrics = self.pool_analyzer.estimate_liquidity_depth(
                reserve_in, reserve_out
            )

            # Get trade history and volatility
            volatility_metrics = self.trade_analyzer.get_volatility_metrics(
                chain_id, pair_address, blocks_back=500
            )

            volatility_factor = volatility_metrics["volatility_factor"]
            trade_size_p95 = volatility_metrics["trade_size_p95"]

            # Calculate base slippage from price impact (with 1.5x buffer)
            base_slippage_bps = int(price_impact_bps * 1.5)

            # Add volatility buffer (scaled)
            volatility_buffer_bps = int(volatility_factor * 100)

            # Add liquidity depth buffer
            liquidity_score = liquidity_metrics["liquidity_score"]
            if liquidity_score == "low":
                liquidity_buffer_bps = 50  # 0.5%
            elif liquidity_score == "medium":
                liquidity_buffer_bps = 25  # 0.25%
            else:  # high
                liquidity_buffer_bps = 10  # 0.1%

            # MEV/frontrun buffer (minimum)
            mev_buffer_bps = 20  # 0.2%

            # Total recommended slippage
            min_safe_slip_bps = (
                base_slippage_bps
                + volatility_buffer_bps
                + liquidity_buffer_bps
                + mev_buffer_bps
            )

            # Ensure minimum of 50 bps (0.5%) and maximum of 5000 bps (50%)
            min_safe_slip_bps = max(50, min(5000, min_safe_slip_bps))

            # Pool depths for response
            pool_depths = {
                "token_in_reserve": str(reserve_in),
                "token_out_reserve": str(reserve_out),
                "reserve_in_tokens": liquidity_metrics["reserve_in_tokens"],
                "reserve_out_tokens": liquidity_metrics["reserve_out_tokens"],
                "liquidity_score": liquidity_score,
            }

            return {
                "min_safe_slip_bps": min_safe_slip_bps,
                "pool_depths": pool_depths,
                "recent_trade_size_p95": trade_size_p95,
                "price_impact_bps": price_impact_bps,
                "volatility_factor": round(volatility_factor, 4),
                "recommended_max_trade": liquidity_metrics["recommended_max_trade"],
                "route_used": dex_name,
                "pair_address": pair_address,
            }

        except Exception as e:
            logger.error(f"Error calculating slippage: {e}", exc_info=True)
            return None

    def calculate_multi_hop_slippage(
        self,
        chain_id: int,
        route: list,  # List of (token_in, token_out) tuples
        amount_in: int,
    ) -> Optional[Dict]:
        """
        Calculate cumulative slippage for multi-hop routes

        Args:
            chain_id: Blockchain chain ID
            route: List of token pairs [(token_a, token_b), (token_b, token_c)]
            amount_in: Initial amount in wei

        Returns:
            Cumulative slippage calculation
        """
        total_slippage_bps = 0
        current_amount = amount_in

        hop_details = []

        for token_in, token_out in route:
            result = self.calculate_safe_slippage(
                chain_id, token_in, token_out, current_amount
            )

            if not result:
                logger.error(f"Failed to calculate slippage for {token_in}/{token_out}")
                return None

            total_slippage_bps += result["min_safe_slip_bps"]
            hop_details.append({
                "token_in": token_in,
                "token_out": token_out,
                "slippage_bps": result["min_safe_slip_bps"],
                "pair_address": result["pair_address"],
            })

            # Update current amount for next hop (simplified)
            reserves = self.pool_analyzer.get_pool_reserves(
                chain_id, result["pair_address"], token_in, token_out
            )
            if reserves:
                current_amount = self.pool_analyzer.calculate_output_amount(
                    current_amount, reserves["reserve_in"], reserves["reserve_out"]
                )

        # Cap total slippage
        total_slippage_bps = min(5000, total_slippage_bps)

        return {
            "total_slippage_bps": total_slippage_bps,
            "num_hops": len(route),
            "hop_details": hop_details,
        }
