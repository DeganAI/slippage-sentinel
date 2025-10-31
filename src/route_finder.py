"""Find best route for token pair across DEXs"""
import logging
from web3 import Web3
from typing import Dict, Optional, List
from src.dex_config import (
    UNISWAP_V2_FACTORY_ABI,
    DEX_FACTORIES,
    get_rpc_url,
)

logger = logging.getLogger(__name__)


class RouteFinder:
    """Finds best trading route for a token pair"""

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

    def find_pair_on_dex(
        self, chain_id: int, dex_name: str, token_in: str, token_out: str
    ) -> Optional[str]:
        """
        Find pair address on a specific DEX

        Args:
            chain_id: Blockchain chain ID
            dex_name: DEX name (e.g., "uniswap_v2")
            token_in: Input token address
            token_out: Output token address

        Returns:
            Pair address or None if not found
        """
        try:
            w3 = self.get_w3(chain_id)
            if not w3:
                return None

            # Get factory address
            factories = DEX_FACTORIES.get(chain_id, {})
            factory_address = factories.get(dex_name.lower())

            if not factory_address:
                logger.debug(f"No factory for {dex_name} on chain {chain_id}")
                return None

            # Create factory contract instance
            factory_contract = w3.eth.contract(
                address=Web3.to_checksum_address(factory_address),
                abi=UNISWAP_V2_FACTORY_ABI,
            )

            # Get pair address
            pair_address = factory_contract.functions.getPair(
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out),
            ).call()

            # Check if pair exists (non-zero address)
            if pair_address == "0x0000000000000000000000000000000000000000":
                return None

            return pair_address

        except Exception as e:
            logger.debug(f"Error finding pair on {dex_name}: {e}")
            return None

    def find_best_route(
        self, chain_id: int, token_in: str, token_out: str, route_hint: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find best route for a token pair

        Args:
            chain_id: Blockchain chain ID
            token_in: Input token address
            token_out: Output token address
            route_hint: Optional DEX hint (e.g., "uniswap_v2")

        Returns:
            {
                "pair_address": str,
                "dex_name": str,
                "factory_address": str,
            }
        """
        # If route hint provided, try that first
        if route_hint:
            pair_address = self.find_pair_on_dex(chain_id, route_hint, token_in, token_out)
            if pair_address:
                factories = DEX_FACTORIES.get(chain_id, {})
                factory_address = factories.get(route_hint.lower())
                return {
                    "pair_address": pair_address,
                    "dex_name": route_hint,
                    "factory_address": factory_address,
                }

        # Try all DEXs on this chain
        factories = DEX_FACTORIES.get(chain_id, {})

        for dex_name, factory_address in factories.items():
            pair_address = self.find_pair_on_dex(chain_id, dex_name, token_in, token_out)
            if pair_address:
                logger.info(f"Found pair on {dex_name}: {pair_address}")
                return {
                    "pair_address": pair_address,
                    "dex_name": dex_name,
                    "factory_address": factory_address,
                }

        logger.warning(f"No pair found for {token_in}/{token_out} on chain {chain_id}")
        return None

    def find_all_routes(
        self, chain_id: int, token_in: str, token_out: str
    ) -> List[Dict]:
        """
        Find all available routes for a token pair

        Args:
            chain_id: Blockchain chain ID
            token_in: Input token address
            token_out: Output token address

        Returns:
            List of routes with pair addresses and DEX names
        """
        routes = []
        factories = DEX_FACTORIES.get(chain_id, {})

        for dex_name, factory_address in factories.items():
            pair_address = self.find_pair_on_dex(chain_id, dex_name, token_in, token_out)
            if pair_address:
                routes.append({
                    "pair_address": pair_address,
                    "dex_name": dex_name,
                    "factory_address": factory_address,
                })

        return routes
