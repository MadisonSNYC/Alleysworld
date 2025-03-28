"""
AI Trading Agent - Main Integration Module

This module integrates all components of the AI Trading Agent and provides
a simple interface for using the agent.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import components
from .src.data_collector import KalshiAPIClient, DataCollector
from .src.analysis_engine import AnalysisEngine
from .src.strategy_processor import StrategyProcessor
from .src.recommendation_generator import RecommendationGenerator
from .src.execution_manager import ExecutionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_trading_agent')

class AITradingAgent:
    """
    Main class that integrates all components of the AI Trading Agent.
    Provides a simple interface for using the agent.
    """
    
    def __init__(self, email: str, password: str):
        """
        Initialize the AI Trading Agent with Kalshi credentials.
        
        Args:
            email: Kalshi account email
            password: Kalshi account password
        """
        logger.info("Initializing AI Trading Agent")
        
        # Initialize API client
        self.api_client = KalshiAPIClient(email=email, password=password)
        
        # Initialize components
        self.data_collector = None
        self.analysis_engine = None
        self.strategy_processor = None
        self.recommendation_generator = None
        self.execution_manager = None
        
        # Initialize state
        self.is_initialized = False
        self.active_strategies = {}
        self.running = False
    
    def initialize(self) -> bool:
        """
        Initialize all components and log in to Kalshi API.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        logger.info("Logging in to Kalshi API")
        
        # Login to Kalshi API
        if not self.api_client.login():
            logger.error("Failed to login to Kalshi API")
            return False
        
        logger.info("Initializing components")
        
        # Initialize components
        self.data_collector = DataCollector(self.api_client)
        self.analysis_engine = AnalysisEngine()
        self.strategy_processor = StrategyProcessor()
        self.recommendation_generator = RecommendationGenerator()
        self.execution_manager = ExecutionManager(self.api_client)
        
        self.is_initialized = True
        logger.info("AI Trading Agent initialized successfully")
        return True
    
    def add_strategy(self, strategy_id: str, strategy_params: Dict) -> bool:
        """
        Add a trading strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_params: Strategy parameters
            
        Returns:
            bool: True if strategy added successfully, False otherwise
        """
        if not self.is_initialized:
            logger.error("AI Trading Agent not initialized")
            return False
        
        logger.info(f"Adding strategy {strategy_id}")
        
        # Load strategy in processor
        result = self.strategy_processor.load_strategy(strategy_id, strategy_params)
        
        if result:
            # Store strategy parameters
            self.active_strategies[strategy_id] = strategy_params
        
        return result
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """
        Remove a trading strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            
        Returns:
            bool: True if strategy removed successfully, False otherwise
        """
        if not self.is_initialized:
            logger.error("AI Trading Agent not initialized")
            return False
        
        logger.info(f"Removing strategy {strategy_id}")
        
        # Delete strategy from processor
        result = self.strategy_processor.delete_strategy(strategy_id)
        
        if result and strategy_id in self.active_strategies:
            # Remove from active strategies
            del self.active_strategies[strategy_id]
        
        return result
    
    def get_recommendations(self, strategy_id: str, max_markets: int = 10) -> List[Dict]:
        """
        Get trade recommendations for a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            max_markets: Maximum number of markets to analyze
            
        Returns:
            List[Dict]: Trade recommendations
        """
        if not self.is_initialized:
            logger.error("AI Trading Agent not initialized")
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
        
        # If no categories specified or no markets found, get markets by time horizon
        if not markets:
            time_horizon = strategy_params.get("timeHorizon", "1h")
            hours = 1  # Default to 1 hour
            
            if time_horizon.endswith("h"):
                hours = int(time_horizon[:-1])
            elif time_horizon.endswith("m"):
                hours = int(time_horizon[:-1]) / 60
            
            markets = self.data_collector.get_markets_by_time_horizon(hours)
        
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
    
    def execute_recommendation(self, recommendation: Dict, execution_mode: str = None) -> Dict:
        """
        Execute a trade recommendation.
        
        Args:
            recommendation: Trade recommendation
            execution_mode: Override execution mode (default: use strategy's mode)
            
        Returns:
            Dict: Execution result
        """
        if not self.is_initialized:
            logger.error("AI Trading Agent not initialized")
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
    
    def start_trading(self, check_interval: int = 60) -> None:
        """
        Start automated trading loop.
        
        Args:
            check_interval: Interval between checks in seconds
        """
        if not self.is_initialized:
            logger.error("AI Trading Agent not initialized")
            return
        
        logger.info("Starting automated trading loop")
        
        self.running = True
        
        try:
            while self.running:
                # Process each strategy
                for strategy_id, strategy_params in self.active_strategies.items():
                    # Get recommendations
                    recommendations = self.get_recommendations(strategy_id)
                    
                    # Execute recommendations if in YOLO mode
                    if strategy_params.get("executionMode") == "yolo":
                        for recommendation in recommendations:
                            self.execute_recommendation(recommendation, "yolo")
                
                # Monitor positions
                self._monitor_positions()
                
                # Wait for next check
                logger.info(f"Waiting {check_interval} seconds until next check")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Trading loop stopped by user")
        except Exception as e:
            logger.error(f"Error in trading loop: {str(e)}")
        finally:
            self.running = False
    
    def stop_trading(self) -> None:
        """Stop automated trading loop."""
        logger.info("Stopping automated trading loop")
        self.running = False
    
    def _monitor_positions(self) -> None:
        """Monitor active positions and execute exits if needed."""
        if not self.execution_manager.active_positions:
            return
        
        logger.info(f"Monitoring {len(self.execution_manager.active_positions)} active positions")
        
        # Collect market data for active positions
        market_data = {}
        for position_id, position in self.execution_manager.active_positions.items():
            ticker = position.get("ticker")
            market_data[ticker] = self.data_collector.get_market_data_bundle(ticker)
        
        # Monitor positions
        actions = self.execution_manager.monitor_positions(market_data)
        
        # Log actions
        for action in actions:
            logger.info(f"Position action: {action.get('action')} for {action.get('position_id')}")
    
    def get_performance_metrics(self) -> Dict:
        """
        Get performance metrics.
        
        Returns:
            Dict: Performance metrics
        """
        if not self.is_initialized:
            logger.error("AI Trading Agent not initialized")
            return {}
        
        return self.execution_manager.get_performance_metrics()
    
    def get_active_positions(self) -> Dict:
        """
        Get active positions.
        
        Returns:
            Dict: Active positions
        """
        if not self.is_initialized:
            logger.error("AI Trading Agent not initialized")
            return {}
        
        return self.execution_manager.active_positions
    
    def get_recommendation_history(self, limit: int = 100) -> List[Dict]:
        """
        Get recommendation history.
        
        Args:
            limit: Maximum number of recommendations to return
            
        Returns:
            List[Dict]: Recommendation history
        """
        if not self.is_initialized:
            logger.error("AI Trading Agent not initialized")
            return []
        
        return self.recommendation_generator.get_recommendation_history(limit)


# Example usage
if __name__ == "__main__":
    # Create agent
    agent = AITradingAgent(email="example@example.com", password="password")
    
    # Initialize agent
    if agent.initialize():
        # Add strategy
        strategy_params = {
            "budget": 100.00,
            "targetProfit": 15,
            "categories": ["crypto", "sports"],
            "timeHorizon": "1h",
            "maxSimultaneousPositions": 5,
            "riskLevel": 6,
            "minConfidence": 65,
            "positionSizing": {
                "maxPerTrade": 20,
                "scaling": "confidence"
            },
            "executionMode": "manual"  # or "yolo" for automatic execution
        }
        
        agent.add_strategy("my_strategy", strategy_params)
        
        # Get recommendations
        recommendations = agent.get_recommendations("my_strategy")
        
        # Print recommendations
        for recommendation in recommendations:
            print(f"Recommendation for {recommendation['asset']}:")
            print(f"Position: {recommendation['position']} at {recommendation['entryPrice']}¢")
            print(f"Confidence: {recommendation['confidence']}%, Expected return: {recommendation['expectedReturn']}%")
            print(f"Reasoning: {recommendation['reasoning']}")
            print()
            
            # Execute recommendation (manual mode)
            result = agent.execute_recommendation(recommendation)
            print(f"Execution result: {result['status']}")
        
        # Start automated trading (uncomment to run)
        # agent.start_trading(check_interval=60)
        
        # Get performance metrics
        performance = agent.get_performance_metrics()
        print(f"Performance metrics: {performance}")
    else:
        print("Failed to initialize AI Trading Agent")
