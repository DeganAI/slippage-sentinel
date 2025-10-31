"""Trade history analysis for volatility estimation"""
import logging
from web3 import Web3
from typing import Dict, List, Optional
import numpy as np
from src.dex_config import get_rpc_url

logger = logging.getLogger(__name__)


# Swap event signature for Uniswap V2 pairs
SWAP_EVENT_SIGNATURE = Web3.keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex()


class TradeHistoryAnalyzer:
    """Analyzes recent trade history to estimate volatility"""

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

    def get_recent_swaps(
        self, chain_id: int, pair_address: str, blocks_back: int = 1000
    ) -> List[Dict]:
        """
        Get recent swap events from a pair

        Args:
            chain_id: Blockchain chain ID
            pair_address: Pair contract address
            blocks_back: How many blocks to look back

        Returns:
            List of swap events with trade sizes
        """
        try:
            w3 = self.get_w3(chain_id)
            if not w3:
                return []

            # Get current block
            current_block = w3.eth.block_number

            # Calculate from block (ensure it's not negative)
            from_block = max(0, current_block - blocks_back)

            # Get Swap events
            filter_params = {
                "address": Web3.to_checksum_address(pair_address),
                "fromBlock": from_block,
                "toBlock": current_block,
                "topics": [SWAP_EVENT_SIGNATURE],
            }

            logs = w3.eth.get_logs(filter_params)

            swaps = []
            for log in logs:
                try:
                    # Parse swap data from log
                    # Swap event: Swap(address indexed sender, uint amount0In, uint amount1In, uint amount0Out, uint amount1Out, address indexed to)
                    # Topics: [event_sig, sender, to]
                    # Data: amount0In, amount1In, amount0Out, amount1Out

                    data = log["data"]
                    # Decode data (4 uint256 values)
                    amount0In = int(data[2:66], 16)
                    amount1In = int(data[66:130], 16)
                    amount0Out = int(data[130:194], 16)
                    amount1Out = int(data[194:258], 16)

                    # Calculate trade size (input amount)
                    trade_size = amount0In + amount1In

                    swaps.append({
                        "block": log["blockNumber"],
                        "amount0In": amount0In,
                        "amount1In": amount1In,
                        "amount0Out": amount0Out,
                        "amount1Out": amount1Out,
                        "trade_size": trade_size,
                    })

                except Exception as e:
                    logger.debug(f"Error parsing swap log: {e}")
                    continue

            logger.info(f"Found {len(swaps)} swaps in last {blocks_back} blocks for {pair_address}")
            return swaps

        except Exception as e:
            logger.error(f"Error getting recent swaps: {e}")
            return []

    def analyze_trade_sizes(self, swaps: List[Dict]) -> Dict:
        """
        Analyze trade sizes to calculate percentiles and volatility

        Args:
            swaps: List of swap events

        Returns:
            {
                "trade_size_p50": int,
                "trade_size_p95": int,
                "trade_size_p99": int,
                "volatility_factor": float,
                "total_swaps": int,
            }
        """
        if not swaps:
            return {
                "trade_size_p50": 0,
                "trade_size_p95": 0,
                "trade_size_p99": 0,
                "volatility_factor": 0.0,
                "total_swaps": 0,
            }

        # Extract trade sizes
        trade_sizes = [swap["trade_size"] for swap in swaps if swap["trade_size"] > 0]

        if not trade_sizes:
            return {
                "trade_size_p50": 0,
                "trade_size_p95": 0,
                "trade_size_p99": 0,
                "volatility_factor": 0.0,
                "total_swaps": len(swaps),
            }

        # Calculate percentiles
        trade_size_p50 = int(np.percentile(trade_sizes, 50))
        trade_size_p95 = int(np.percentile(trade_sizes, 95))
        trade_size_p99 = int(np.percentile(trade_sizes, 99))

        # Calculate volatility (coefficient of variation)
        mean_size = np.mean(trade_sizes)
        std_size = np.std(trade_sizes)
        volatility_factor = std_size / mean_size if mean_size > 0 else 0.0

        return {
            "trade_size_p50": trade_size_p50,
            "trade_size_p95": trade_size_p95,
            "trade_size_p99": trade_size_p99,
            "volatility_factor": volatility_factor,
            "total_swaps": len(swaps),
        }

    def get_volatility_metrics(
        self, chain_id: int, pair_address: str, blocks_back: int = 1000
    ) -> Dict:
        """
        Get comprehensive volatility metrics for a pair

        Args:
            chain_id: Blockchain chain ID
            pair_address: Pair contract address
            blocks_back: How many blocks to analyze

        Returns:
            Volatility metrics including trade sizes and volatility factor
        """
        swaps = self.get_recent_swaps(chain_id, pair_address, blocks_back)
        metrics = self.analyze_trade_sizes(swaps)

        return metrics
