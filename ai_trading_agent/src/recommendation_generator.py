"""
Recommendation Generator for AI Trading Agent

This module creates structured trade recommendations with confidence scores,
determines optimal position sizes, prioritizes recommendations, and provides
detailed reasoning for each recommendation.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import json
import math
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('recommendation_generator')

class RecommendationGenerator:
    """
    Creates structured trade recommendations with confidence scores,
    determines optimal position sizes, and provides detailed reasoning.
    """
    
    def __init__(self):
        """Initialize the Recommendation Generator."""
        logger.info("Initializing Recommendation Generator")
        self.recommendation_history = []
    
    def generate_recommendations(self, opportunities: List[Dict], market_data: Dict) -> List[Dict]:
        """
        Generate structured trade recommendations from opportunities.
        
        Args:
            opportunities: List of trading opportunities from AnalysisEngine
            market_data: Market data from DataCollector
            
        Returns:
            List[Dict]: Structured trade recommendations
        """
        logger.info(f"Generating recommendations from {len(opportunities)} opportunities")
        
        recommendations = []
        
        for opportunity in opportunities:
            # Skip opportunities without required fields
            if not self._validate_opportunity(opportunity):
                logger.warning(f"Skipping invalid opportunity: {opportunity.get('type', 'unknown')}")
                continue
            
            # Create recommendation
            recommendation = self._create_recommendation(opportunity, market_data)
            
            # Add to recommendations list
            recommendations.append(recommendation)
            
            # Add to history
            self.recommendation_history.append({
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat(),
                "status": "generated"
            })
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _validate_opportunity(self, opportunity: Dict) -> bool:
        """
        Validate that an opportunity has all required fields.
        
        Args:
            opportunity: Trading opportunity
            
        Returns:
            bool: True if opportunity is valid, False otherwise
        """
        required_fields = [
            "position", "current_price", "target_price", "confidence_score"
        ]
        
        for field in required_fields:
            if field not in opportunity:
                logger.warning(f"Opportunity missing required field: {field}")
                return False
        
        return True
    
    def _create_recommendation(self, opportunity: Dict, market_data: Dict) -> Dict:
        """
        Create a structured trade recommendation from an opportunity.
        
        Args:
            opportunity: Trading opportunity
            market_data: Market data from DataCollector
            
        Returns:
            Dict: Structured trade recommendation
        """
        # Extract market details
        market_details = market_data.get("market_details", {})
        ticker = market_details.get("ticker", "unknown")
        
        # Generate recommendation ID
        recommendation_id = str(uuid.uuid4())[:8]
        
        # Extract basic fields from opportunity
        position_type = opportunity.get("position")  # YES or NO
        current_price = opportunity.get("current_price")
        target_price = opportunity.get("target_price")
        confidence_score = opportunity.get("confidence_score")
        
        # Calculate stop loss (default to 33% of expected gain in opposite direction)
        price_diff = abs(target_price - current_price)
        stop_loss = current_price - (price_diff * 0.33) if position_type == "YES" else current_price + (price_diff * 0.33)
        
        # Ensure stop loss is within valid range (1-99 cents)
        stop_loss = max(1, min(99, stop_loss))
        
        # Format target exit as range
        target_exit_low = max(1, target_price - 2)
        target_exit_high = min(99, target_price + 2)
        target_exit = f"{target_exit_low}-{target_exit_high}"
        
        # Extract contracts and cost if available
        contracts = opportunity.get("contracts", 0)
        cost = opportunity.get("cost", 0)
        
        # Calculate expected return percentage
        if current_price > 0:
            expected_return = ((target_price - current_price) / current_price) * 100
        else:
            expected_return = 0
        
        # Determine time window
        time_window = opportunity.get("timeWindow", "unknown")
        if time_window == "unknown" and "close_time" in market_details:
            close_time = datetime.fromisoformat(market_details["close_time"].replace('Z', '+00:00'))
            now = datetime.now()
            time_window = f"{now.strftime('%H:%M')}-{close_time.strftime('%H:%M %Z')}"
        
        # Generate detailed reasoning
        reasoning = self._generate_reasoning(opportunity, market_data)
        
        # Create recommendation
        recommendation = {
            "id": recommendation_id,
            "asset": ticker,
            "position": position_type,
            "currentPrice": current_price,
            "entryPrice": current_price,
            "contracts": contracts,
            "cost": cost,
            "targetExit": target_exit,
            "stopLoss": round(stop_loss),
            "confidence": round(confidence_score),
            "expectedReturn": round(expected_return, 1),
            "timeWindow": time_window,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        return recommendation
    
    def _generate_reasoning(self, opportunity: Dict, market_data: Dict) -> str:
        """
        Generate detailed reasoning for a recommendation.
        
        Args:
            opportunity: Trading opportunity
            market_data: Market data from DataCollector
            
        Returns:
            str: Detailed reasoning
        """
        # Extract data for reasoning
        opportunity_type = opportunity.get("type", "unknown")
        position_type = opportunity.get("position", "unknown")
        base_reasoning = opportunity.get("reasoning", "")
        
        # Extract market details
        market_details = market_data.get("market_details", {})
        ticker = market_details.get("ticker", "unknown")
        
        # Extract price data
        current_price = opportunity.get("current_price", 0)
        target_price = opportunity.get("target_price", 0)
        
        # Extract order book data
        order_book = market_data.get("order_book", {})
        yes_bids = order_book.get("yes_bids", [])
        yes_asks = order_book.get("yes_asks", [])
        
        # Build reasoning based on opportunity type
        reasoning_parts = []
        
        # Add base reasoning if available
        if base_reasoning:
            reasoning_parts.append(base_reasoning)
        
        # Add type-specific reasoning
        if opportunity_type == "momentum":
            reasoning_parts.append(f"Market showing strong {'upward' if position_type == 'YES' else 'downward'} momentum.")
            
            # Add volume information if available
            yes_volume = market_details.get("yes_volume", 0)
            no_volume = market_details.get("no_volume", 0)
            
            if yes_volume > 0 and no_volume > 0:
                volume_ratio = yes_volume / no_volume if no_volume > 0 else float('inf')
                reasoning_parts.append(f"{volume_ratio:.1f}:1 YES:NO volume ratio suggests {'positive' if volume_ratio > 1 else 'negative'} sentiment.")
        
        elif opportunity_type == "mispricing":
            fair_value = opportunity.get("fair_value", target_price)
            reasoning_parts.append(f"Market appears {'underpriced' if position_type == 'YES' else 'overpriced'} at {current_price}¢ compared to estimated fair value of {fair_value}¢.")
        
        elif opportunity_type == "technical_pattern":
            pattern = opportunity.get("pattern", "technical")
            reasoning_parts.append(f"{pattern.capitalize()} pattern detected, suggesting {'upward' if position_type == 'YES' else 'downward'} price movement.")
        
        elif opportunity_type == "market_psychology":
            reasoning_parts.append(f"Market sentiment and order book analysis suggest {'positive' if position_type == 'YES' else 'negative'} price movement.")
        
        # Add order book analysis
        if yes_bids and yes_asks:
            bid_volume = sum(order.get("size", 0) for order in yes_bids)
            ask_volume = sum(order.get("size", 0) for order in yes_asks)
            
            if bid_volume > 0 and ask_volume > 0:
                if position_type == "YES" and bid_volume > ask_volume:
                    reasoning_parts.append(f"Order book shows {bid_volume}/{ask_volume} bid/ask volume ratio, indicating buying pressure.")
                elif position_type == "NO" and ask_volume > bid_volume:
                    reasoning_parts.append(f"Order book shows {bid_volume}/{ask_volume} bid/ask volume ratio, indicating selling pressure.")
        
        # Add expected return information
        price_diff = abs(target_price - current_price)
        price_change_pct = (price_diff / current_price) * 100 if current_price > 0 else 0
        
        reasoning_parts.append(f"Target exit at {target_price}¢ represents a {price_change_pct:.1f}% {'increase' if target_price > current_price else 'decrease'} from current price.")
        
        # Combine reasoning parts
        reasoning = " ".join(reasoning_parts)
        
        return reasoning
    
    def prioritize_recommendations(self, recommendations: List[Dict], max_count: int = 10) -> List[Dict]:
        """
        Prioritize recommendations based on confidence and expected return.
        
        Args:
            recommendations: List of trade recommendations
            max_count: Maximum number of recommendations to return
            
        Returns:
            List[Dict]: Prioritized recommendations
        """
        logger.info(f"Prioritizing {len(recommendations)} recommendations")
        
        # Define scoring function
        def score_recommendation(recommendation):
            confidence = recommendation.get("confidence", 0)
            expected_return = recommendation.get("expectedReturn", 0)
            
            # Weight confidence more heavily than expected return
            return (confidence * 0.7) + (expected_return * 0.3)
        
        # Score and sort recommendations
        for recommendation in recommendations:
            recommendation["priority_score"] = score_recommendation(recommendation)
        
        prioritized = sorted(recommendations, key=lambda x: x.get("priority_score", 0), reverse=True)
        
        # Limit to max count
        return prioritized[:max_count]
    
    def format_recommendation_for_display(self, recommendation: Dict) -> Dict:
        """
        Format a recommendation for display in the UI.
        
        Args:
            recommendation: Trade recommendation
            
        Returns:
            Dict: Formatted recommendation for display
        """
        # Create a copy to avoid modifying the original
        display_rec = recommendation.copy()
        
        # Format prices as strings with % symbol
        display_rec["currentPrice"] = f"{display_rec.get('currentPrice', 0)}¢"
        display_rec["entryPrice"] = f"{display_rec.get('entryPrice', 0)}¢"
        display_rec["stopLoss"] = f"{display_rec.get('stopLoss', 0)}¢"
        
        # Format cost as currency
        display_rec["cost"] = f"${display_rec.get('cost', 0):.2f}"
        
        # Format expected return with % symbol
        display_rec["expectedReturn"] = f"{display_rec.get('expectedReturn', 0):.1f}%"
        
        # Format confidence with % symbol
        display_rec["confidence"] = f"{display_rec.get('confidence', 0)}%"
        
        return display_rec
    
    def update_recommendation_status(self, recommendation_id: str, status: str, 
                                    execution_details: Dict = None) -> bool:
        """
        Update the status of a recommendation in the history.
        
        Args:
            recommendation_id: Unique identifier for the recommendation
            status: New status (e.g., "executed", "rejected", "expired")
            execution_details: Optional details about execution
            
        Returns:
            bool: True if status updated successfully, False otherwise
        """
        logger.info(f"Updating recommendation {recommendation_id} status to {status}")
        
        # Find recommendation in history
        for entry in self.recommendation_history:
            if entry["recommendation"].get("id") == recommendation_id:
                # Update status
                entry["recommendation"]["status"] = status
                
                # Add execution details if provided
                if execution_details:
                    entry["execution_details"] = execution_details
                
                # Add timestamp
                entry["status_updated_at"] = datetime.now().isoformat()
                
                logger.info(f"Recommendation {recommendation_id} status updated to {status}")
                return True
        
        logger.error(f"Recommendation {recommendation_id} not found in history")
        return False
    
    def get_recommendation_history(self, limit: int = 100, 
                                  status_filter: str = None) -> List[Dict]:
        """
        Get recommendation history.
        
        Args:
            limit: Maximum number of recommendations to return
            status_filter: Filter by status (e.g., "executed", "rejected")
            
        Returns:
            List[Dict]: Recommendation history
        """
        # Apply status filter if provided
        if status_filter:
            filtered_history = [
                entry for entry in self.recommendation_history
                if entry["recommendation"].get("status") == status_filter
            ]
        else:
            filtered_history = self.recommendation_history
        
        # Sort by timestamp (newest first)
        sorted_history = sorted(
            filtered_history,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        # Limit results
        return sorted_history[:limit]
    
    def get_recommendation_by_id(self, recommendation_id: str) -> Dict:
        """
        Get a recommendation by ID.
        
        Args:
            recommendation_id: Unique identifier for the recommendation
            
        Returns:
            Dict: Recommendation details
        """
        for entry in self.recommendation_history:
            if entry["recommendation"].get("id") == recommendation_id:
                return entry
        
        return {}
    
    def generate_daily_report(self) -> Dict:
        """
        Generate a daily report of recommendations and performance.
        
        Returns:
            Dict: Daily report
        """
        logger.info("Generating daily report")
        
        # Get today's date
        today = datetime.now().date()
        
        # Filter recommendations from today
        today_recommendations = [
            entry for entry in self.recommendation_history
            if datetime.fromisoformat(entry.get("timestamp", "")).date() == today
        ]
        
        # Count recommendations by status
        status_counts = {}
        for entry in today_recommendations:
            status = entry["recommendation"].get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate performance metrics for executed recommendations
        executed_recommendations = [
            entry for entry in today_recommendations
            if entry["recommendation"].get("status") == "executed" and "execution_details" in entry
        ]
        
        total_cost = sum(entry["recommendation"].get("cost", 0) for entry in executed_recommendations)
        total_profit = sum(entry.get("execution_details", {}).get("profit_loss", 0) for entry in executed_recommendations)
        
        win_count = sum(1 for entry in executed_recommendations if entry.get("execution_details", {}).get("profit_loss", 0) > 0)
        loss_count = len(executed_recommendations) - win_count
        
        win_rate = (win_count / len(executed_recommendations)) * 100 if executed_recommendations else 0
        roi = (total_profit / total_cost) * 100 if total_cost > 0 else 0
        
        # Generate report
        report = {
            "date": today.isoformat(),
            "total_recommendations": len(today_recommendations),
            "status_counts": status_counts,
            "executed_count": len(executed_recommendations),
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "roi": roi,
            "top_recommendations": self.prioritize_recommendations(
                [entry["recommendation"] for entry in today_recommendations], 5
            )
        }
        
        return report


# Example usage
if __name__ == "__main__":
    # Create recommendation generator
    generator = RecommendationGenerator()
    
    # Example opportunities
    opportunities = [
        {
            "type": "momentum",
            "position": "YES",
            "current_price": 33,
            "target_price": 48,
            "confidence_score": 82,
            "contracts": 7,
            "cost": 2.31,
            "timeWindow": "11:00-12:00 EDT",
            "reasoning": "BTC showing strong upward momentum"
        },
        {
            "type": "mispricing",
            "position": "NO",
            "current_price": 67,
            "target_price": 52,
            "confidence_score": 75,
            "contracts": 5,
            "cost": 3.35,
            "timeWindow": "11:00-12:00 EDT",
            "reasoning": "Market appears overpriced"
        }
    ]
    
    # Example market data
    market_data = {
        "market_details": {
            "ticker": "BTC-83750-83999-12PM",
            "yes_bid": 33,
            "no_bid": 67,
            "volume": 10000,
            "yes_volume": 6000,
            "no_volume": 4000,
            "close_time": (datetime.now() + timedelta(hours=1)).isoformat() + "Z"
        },
        "order_book": {
            "yes_bids": [{"price": 33, "size": 500}, {"price": 32, "size": 700}],
            "yes_asks": [{"price": 34, "size": 300}, {"price": 35, "size": 400}]
        }
    }
    
    # Generate recommendations
    recommendations = generator.generate_recommendations(opportunities, market_data)
    
    # Print recommendations
    for recommendation in recommendations:
        print(f"Recommendation for {recommendation['asset']}:")
        print(f"Position: {recommendation['position']} at {recommendation['entryPrice']}¢")
        print(f"Contracts: {recommendation['contracts']}, Cost: ${recommendation['cost']:.2f}")
        print(f"Target exit: {recommendation['targetExit']}¢, Stop loss: {recommendation['stopLoss']}¢")
        print(f"Confidence: {recommendation['confidence']}%, Expected return: {recommendation['expectedReturn']}%")
        print(f"Time window: {recommendation['timeWindow']}")
        print(f"Reasoning: {recommendation['reasoning']}")
        print()
