"""
Test script for AI Trading Agent with Mock API Client

This script demonstrates how to use the AI Trading Agent
with a mock API client for local testing without requiring
actual Kalshi API credentials.
"""

import logging
import time
from datetime import datetime

# Import the mock client instead of the real one
from src.mock_kalshi_api_client import MockKalshiAPIClient
from src.data_collector import DataCollector
from src.analysis_engine import AnalysisEngine
from src.strategy_processor import StrategyProcessor
from src.recommendation_generator import RecommendationGenerator
from src.execution_manager import ExecutionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('local_test')

class LocalAITradingAgent:
    """
    Local version of AI Trading Agent that uses a mock API client
    for testing without requiring actual Kalshi API credentials.
    """
    
    def __init__(self):
        """Initialize the Local AI Trading Agent with mock client."""
        logger.info("Initializing Local AI Trading Agent")
        
        # Initialize mock API client (no real credentials needed)
        self.api_client = MockKalshiAPIClient()
        
        # Initialize components
        self.data_collector = None
        self.analysis_engine = None
        self.strategy_processor = None
        self.recommendation_generator = None
        self.execution_manager = None
        
        # Initialize state
        self.is_initialized = False
        self.active_strategies = {}
    
    def initialize(self) -> bool:
        """
        Initialize all components with mock client.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        logger.info("Initializing components with mock client")
        
        # Login to mock API (always succeeds)
        if not self.api_client.login():
            logger.error("Failed to login to mock API")
            return False
        
        # Initialize components
        self.data_collector = DataCollector(self.api_client)
        self.analysis_engine = AnalysisEngine()
        self.strategy_processor = StrategyProcessor()
        self.recommendation_generator = RecommendationGenerator()
        self.execution_manager = ExecutionManager(self.api_client)
        
        self.is_initialized = True
        logger.info("Local AI Trading Agent initialized successfully")
        return True
    
    def add_strategy(self, strategy_id: str, strategy_params: dict) -> bool:
        """
        Add a trading strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_params: Strategy parameters
            
        Returns:
            bool: True if strategy added successfully, False otherwise
        """
        if not self.is_initialized:
            logger.error("Local AI Trading Agent not initialized")
            return False
        
        logger.info(f"Adding strategy {strategy_id}")
        
        # Load strategy in processor
        result = self.strategy_processor.load_strategy(strategy_id, strategy_params)
        
        if result:
            # Store strategy parameters
            self.active_strategies[strategy_id] = strategy_params
        
        return result
    
    def get_recommendations(self, strategy_id: str, max_markets: int = 5) -> list:
        """
        Get trade recommendations for a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            max_markets: Maximum number of markets to analyze
            
        Returns:
            List[Dict]: Trade recommendations
        """
        if not self.is_initialized:
            logger.error("Local AI Trading Agent not initialized")
            return []
        
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return []
        
        logger.info(f"Getting recommendations for strategy {strategy_id}")
        
        strategy_params = self.active_strategies[strategy_id]
        
        # Get markets based on strategy parameters
        markets = []
        
        # Get markets by categories
        categories = strategy_params.get("categories", [])
        for category in categories:
            category_markets = self.data_collector.get_markets_by_category(category)
            markets.extend(category_markets)
        
        # If no categories specified or no markets found, get all markets
        if not markets:
            markets = self.data_collector.get_markets_by_time_horizon(1)
        
        # Limit number of markets
        markets = markets[:max_markets]
        
        # Process markets
        all_opportunities = []
        market_data_map = {}
        
        for market in markets:
            ticker = market["ticker"]
            
            # Get market data
            market_data = self.data_collector.get_market_data_bundle(ticker)
            market_data_map[ticker] = market_data
            
            # Analyze market data
            analysis_results = self.analysis_engine.process_market_data(market_data)
            
            # Add opportunities
            all_opportunities.extend(analysis_results["opportunities"])
        
        # Apply strategy to opportunities
        filtered_opportunities = self.strategy_processor.apply_strategy(
            strategy_id, all_opportunities
        )
        
        # Generate recommendations
        recommendations = []
        for opportunity in filtered_opportunities:
            # Get market data for this opportunity
            ticker = opportunity.get("ticker", "unknown")
            market_data = market_data_map.get(ticker, {})
            
            # Generate recommendation
            recommendation = self.recommendation_generator.generate_recommendations(
                [opportunity], market_data
            )
            
            if recommendation:
                recommendations.extend(recommendation)
        
        # Prioritize recommendations
        prioritized_recommendations = self.recommendation_generator.prioritize_recommendations(
            recommendations
        )
        
        return prioritized_recommendations
    
    def execute_recommendation(self, recommendation: dict, execution_mode: str = None) -> dict:
        """
        Execute a trade recommendation.
        
        Args:
            recommendation: Trade recommendation
            execution_mode: Override execution mode (default: use strategy's mode)
            
        Returns:
            Dict: Execution result
        """
        if not self.is_initialized:
            logger.error("Local AI Trading Agent not initialized")
            return {"status": "failed", "error": "Agent not initialized"}
        
        logger.info(f"Executing recommendation for {recommendation.get('asset')}")
        
        # Get strategy execution mode if not specified
        if execution_mode is None:
            strategy_id = recommendation.get("strategy_id")
            if strategy_id in self.active_strategies:
                execution_mode = self.active_strategies[strategy_id].get("executionMode", "manual")
            else:
                execution_mode = "manual"
        
        # Execute trade
        result = self.execution_manager.execute_trade(recommendation, execution_mode)
        
        # Update recommendation status
        self.recommendation_generator.update_recommendation_status(
            recommendation.get("id"), result.get("status")
        )
        
        return result
    
    def get_performance_metrics(self) -> dict:
        """
        Get performance metrics.
        
        Returns:
            Dict: Performance metrics
        """
        if not self.is_initialized:
            logger.error("Local AI Trading Agent not initialized")
            return {}
        
        return self.execution_manager.get_performance_metrics()

def run_local_test():
    """Run a local test of the AI Trading Agent with mock data."""
    print("\n" + "="*80)
    print("STARTING LOCAL TEST OF AI TRADING AGENT")
    print("="*80 + "\n")
    
    # Create local agent
    agent = LocalAITradingAgent()
    
    # Initialize agent
    if not agent.initialize():
        print("Failed to initialize Local AI Trading Agent")
        return
    
    print("\n" + "-"*80)
    print("TESTING STRATEGY CONFIGURATION")
    print("-"*80 + "\n")
    
    # Add test strategies
    strategies = [
        {
            "id": "rapid_trading",
            "params": {
                "budget": 100.00,
                "targetProfit": 15,
                "categories": ["crypto"],
                "timeHorizon": "1h",
                "maxSimultaneousPositions": 3,
                "riskLevel": 7,
                "minConfidence": 70,
                "positionSizing": {
                    "maxPerTrade": 30,
                    "scaling": "confidence"
                },
                "executionMode": "manual"
            }
        },
        {
            "id": "market_psychology",
            "params": {
                "budget": 150.00,
                "targetProfit": 20,
                "categories": ["finance"],
                "timeHorizon": "2h",
                "maxSimultaneousPositions": 4,
                "riskLevel": 8,
                "minConfidence": 75,
                "positionSizing": {
                    "maxPerTrade": 25,
                    "scaling": "risk"
                },
                "executionMode": "manual"
            }
        }
    ]
    
    for strategy in strategies:
        result = agent.add_strategy(strategy["id"], strategy["params"])
        print(f"Added strategy '{strategy['id']}': {'Success' if result else 'Failed'}")
    
    print("\n" + "-"*80)
    print("TESTING RECOMMENDATION GENERATION")
    print("-"*80 + "\n")
    
    # Get recommendations for each strategy
    for strategy in strategies:
        print(f"\nGetting recommendations for strategy '{strategy['id']}':")
        recommendations = agent.get_recommendations(strategy["id"])
        
        if not recommendations:
            print(f"No recommendations generated for strategy '{strategy['id']}'")
            continue
        
        print(f"Generated {len(recommendations)} recommendations:")
        
        # Print recommendations
        for i, recommendation in enumerate(recommendations, 1):
            print(f"\nRecommendation #{i}:")
            print(f"Asset: {recommendation['asset']}")
            print(f"Position: {recommendation['position']} at {recommendation['entryPrice']}¢")
            print(f"Contracts: {recommendation['contracts']}, Cost: ${recommendation.get('cost', 0):.2f}")
            print(f"Target exit: {recommendation['targetExit']}¢, Stop loss: {recommendation['stopLoss']}¢")
            print(f"Confidence: {recommendation['confidence']}%, Expected return: {recommendation['expectedReturn']}%")
            print(f"Time window: {recommendation['timeWindow']}")
            print(f"Reasoning: {recommendation['reasoning']}")
    
    print("\n" + "-"*80)
    print("TESTING TRADE EXECUTION")
    print("-"*80 + "\n")
    
    # Get recommendations for the first strategy
    recommendations = agent.get_recommendations(strategies[0]["id"])
    
    if recommendations:
        # Execute the first recommendation
        recommendation = recommendations[0]
        print(f"Executing recommendation for {recommendation['asset']}:")
        
        # Test manual execution
        manual_result = agent.execute_recommendation(recommendation, "manual")
        print(f"Manual execution result: {manual_result['status']}")
        
        # Test YOLO execution
        yolo_result = agent.execute_recommendation(recommendation, "yolo")
        print(f"YOLO execution result: {yolo_result['status']}")
        
        # Get performance metrics
        performance = agent.get_performance_metrics()
        print("\nPerformance metrics:")
        for key, value in performance.items():
            print(f"{key}: {value}")
    else:
        print("No recommendations available for execution testing")
    
    print("\n" + "="*80)
    print("LOCAL TEST COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_local_test()
