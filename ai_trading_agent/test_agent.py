"""
Test script for AI Trading Agent

This script demonstrates how to use the AI Trading Agent
and tests its core functionality.
"""

import logging
import time
from ai_trading_agent import AITradingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_script')

def test_agent():
    """Test the AI Trading Agent functionality."""
    logger.info("Starting AI Trading Agent test")
    
    # Initialize agent with demo credentials
    # Replace with your Kalshi demo account credentials
    agent = AITradingAgent(email="demo_user@example.com", password="demo_password")
    
    # Initialize components
    if not agent.initialize():
        logger.error("Failed to initialize AI Trading Agent")
        return
    
    logger.info("AI Trading Agent initialized successfully")
    
    # Add test strategy
    test_strategy = {
        "budget": 100.00,
        "targetProfit": 15,
        "categories": ["crypto", "finance"],
        "timeHorizon": "1h",
        "maxSimultaneousPositions": 3,
        "riskLevel": 5,
        "minConfidence": 60,
        "positionSizing": {
            "maxPerTrade": 20,
            "scaling": "confidence"
        },
        "executionMode": "manual"  # Use manual mode for testing
    }
    
    if not agent.add_strategy("test_strategy", test_strategy):
        logger.error("Failed to add test strategy")
        return
    
    logger.info("Test strategy added successfully")
    
    # Get recommendations
    logger.info("Getting recommendations...")
    recommendations = agent.get_recommendations("test_strategy", max_markets=5)
    
    if not recommendations:
        logger.warning("No recommendations generated")
    else:
        logger.info(f"Generated {len(recommendations)} recommendations")
        
        # Print recommendations
        for recommendation in recommendations:
            print(f"\nRecommendation for {recommendation['asset']}:")
            print(f"Position: {recommendation['position']} at {recommendation['entryPrice']}¢")
            print(f"Contracts: {recommendation['contracts']}, Cost: ${recommendation.get('cost', 0):.2f}")
            print(f"Target exit: {recommendation['targetExit']}¢, Stop loss: {recommendation['stopLoss']}¢")
            print(f"Confidence: {recommendation['confidence']}%, Expected return: {recommendation['expectedReturn']}%")
            print(f"Time window: {recommendation['timeWindow']}")
            print(f"Reasoning: {recommendation['reasoning']}")
            
            # Test executing recommendation (in manual mode)
            result = agent.execute_recommendation(recommendation)
            print(f"Execution result: {result['status']}")
    
    # Test getting performance metrics
    performance = agent.get_performance_metrics()
    print("\nPerformance metrics:")
    for key, value in performance.items():
        print(f"{key}: {value}")
    
    logger.info("AI Trading Agent test completed")

if __name__ == "__main__":
    test_agent()
