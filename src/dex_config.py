"""DEX configuration and ABIs"""
import os

# Supported chains configuration
CHAIN_CONFIG = {
    1: {
        "name": "Ethereum",
        "symbol": "ETH",
        "rpc_env": "ETHEREUM_RPC_URL",
        "default_rpc": "https://eth.llamarpc.com",
    },
    137: {
        "name": "Polygon",
        "symbol": "MATIC",
        "rpc_env": "POLYGON_RPC_URL",
        "default_rpc": "https://polygon.llamarpc.com",
    },
    42161: {
        "name": "Arbitrum",
        "symbol": "ETH",
        "rpc_env": "ARBITRUM_RPC_URL",
        "default_rpc": "https://arbitrum.llamarpc.com",
    },
    10: {
        "name": "Optimism",
        "symbol": "ETH",
        "rpc_env": "OPTIMISM_RPC_URL",
        "default_rpc": "https://optimism.llamarpc.com",
    },
    8453: {
        "name": "Base",
        "symbol": "ETH",
        "rpc_env": "BASE_RPC_URL",
        "default_rpc": "https://base.llamarpc.com",
    },
    56: {
        "name": "BNB Chain",
        "symbol": "BNB",
        "rpc_env": "BSC_RPC_URL",
        "default_rpc": "https://bsc.llamarpc.com",
    },
    43114: {
        "name": "Avalanche",
        "symbol": "AVAX",
        "rpc_env": "AVALANCHE_RPC_URL",
        "default_rpc": "https://avalanche.llamarpc.com",
    },
}

# Uniswap V2 Pair ABI (minimal for reserves)
UNISWAP_V2_PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

# Uniswap V2 Factory ABI (minimal for getting pair)
UNISWAP_V2_FACTORY_ABI = [
    {
        "constant": True,
        "inputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "address", "name": "", "type": "address"},
        ],
        "name": "getPair",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

# DEX Factory Addresses
DEX_FACTORIES = {
    # Ethereum
    1: {
        "uniswap_v2": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "sushiswap": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
    },
    # Polygon
    137: {
        "quickswap": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
        "sushiswap": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
    },
    # Arbitrum
    42161: {
        "sushiswap": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
        "uniswap_v2": "0xf1D7CC64Fb4452F05c498126312eBE29f30Fbcf9",
    },
    # Optimism
    10: {
        "uniswap_v2": "0x0c3c1c532F1e39EdF36BE9Fe0bE1410313E074Bf",
    },
    # Base
    8453: {
        "uniswap_v2": "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6",
    },
    # BNB Chain
    56: {
        "pancakeswap": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
        "sushiswap": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
    },
    # Avalanche
    43114: {
        "traderjoe": "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10",
        "sushiswap": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
    },
}


def get_rpc_url(chain_id: int) -> str:
    """Get RPC URL for a chain"""
    if chain_id not in CHAIN_CONFIG:
        return None

    config = CHAIN_CONFIG[chain_id]
    return os.getenv(config["rpc_env"], config["default_rpc"])


def get_chain_info(chain_id: int) -> dict:
    """Get chain information"""
    return CHAIN_CONFIG.get(chain_id)


def get_dex_factory(chain_id: int, dex_name: str) -> str:
    """Get factory address for a DEX on a chain"""
    factories = DEX_FACTORIES.get(chain_id, {})
    return factories.get(dex_name.lower())
