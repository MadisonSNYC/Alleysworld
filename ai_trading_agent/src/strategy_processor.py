"""
Strategy Processor for AI Trading Agent

This module interprets user-defined strategy parameters, applies strategy constraints
to identified opportunities, prioritizes opportunities based on strategy goals,
and adapts strategy application based on market conditions.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import json
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('strategy_processor')

class StrategyProcessor:
    """
    Interprets user-defined strategy parameters and applies them to identified opportunities.
    Prioritizes opportunities based on strategy goals and adapts to market conditions.
    """
    
    def __init__(self):
        """Initialize the Strategy Processor."""
        logger.info("Initializing Strategy Processor")
        self.active_strategies = {}
    
    def load_strategy(self, strategy_id: str, strategy_params: Dict) -> bool:
        """
        Load a trading strategy with specified parameters.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_params: Dictionary containing strategy parameters
            
        Returns:
            bool: True if strategy loaded successfully, False otherwise
        """
        logger.info(f"Loading strategy {strategy_id}")
        
        # Validate required parameters
        required_params = [
            "budget", "targetProfit", "categories", "timeHorizon", 
            "maxSimultaneousPositions", "riskLevel", "minConfidence"
        ]
        
        for param in required_params:
            if param not in strategy_params:
                logger.error(f"Missing required parameter: {param}")
                return False
        
        # Validate parameter types and values
        try:
            # Budget must be positive number
            budget = float(strategy_params["budget"])
            if budget <= 0:
                logger.error("Budget must be positive")
                return False
            
            # Target profit must be positive number
            target_profit = float(strategy_params["targetProfit"])
            if target_profit <= 0:
                logger.error("Target profit must be positive")
                return False
            
            # Categories must be list
            categories = strategy_params["categories"]
            if not isinstance(categories, list):
                logger.error("Categories must be a list")
                return False
            
            # Time horizon must be string with number and unit
            time_horizon = strategy_params["timeHorizon"]
            if not isinstance(time_horizon, str):
                logger.error("Time horizon must be a string")
                return False
            
            # Max simultaneous positions must be positive integer
            max_positions = int(strategy_params["maxSimultaneousPositions"])
            if max_positions <= 0:
                logger.error("Max simultaneous positions must be positive")
                return False
            
            # Risk level must be 1-10
            risk_level = int(strategy_params["riskLevel"])
            if risk_level < 1 or risk_level > 10:
                logger.error("Risk level must be between 1 and 10")
                return False
            
            # Min confidence must be 0-100
            min_confidence = float(strategy_params["minConfidence"])
            if min_confidence < 0 or min_confidence > 100:
                logger.error("Minimum confidence must be between 0 and 100")
                return False
            
            # Position sizing is optional, but if present must have maxPerTrade
            if "positionSizing" in strategy_params:
                position_sizing = strategy_params["positionSizing"]
                if not isinstance(position_sizing, dict):
                    logger.error("Position sizing must be a dictionary")
                    return False
                
                if "maxPerTrade" not in position_sizing:
                    logger.error("Position sizing must include maxPerTrade")
                    return False
                
                max_per_trade = float(position_sizing["maxPerTrade"])
                if max_per_trade <= 0 or max_per_trade > 100:
                    logger.error("Max per trade must be between 0 and 100")
                    return False
            
            # Execution mode must be "manual" or "yolo"
            execution_mode = strategy_params.get("executionMode", "manual")
            if execution_mode not in ["manual", "yolo"]:
                logger.error("Execution mode must be 'manual' or 'yolo'")
                return False
            
        except (ValueError, TypeError) as e:
            logger.error(f"Parameter validation error: {str(e)}")
            return False
        
        # Store strategy with additional metadata
        self.active_strategies[strategy_id] = {
            "params": strategy_params,
            "created_at": datetime.now().isoformat(),
            "active_positions": [],
            "completed_positions": [],
            "performance": {
                "win_count": 0,
                "loss_count": 0,
                "total_profit": 0.0,
                "total_investment": 0.0
            }
        }
        
        logger.info(f"Strategy {strategy_id} loaded successfully")
        return True
    
    def update_strategy(self, strategy_id: str, strategy_params: Dict) -> bool:
        """
        Update an existing strategy with new parameters.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_params: Dictionary containing updated strategy parameters
            
        Returns:
            bool: True if strategy updated successfully, False otherwise
        """
        logger.info(f"Updating strategy {strategy_id}")
        
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
        
        # Keep track of active positions and performance
        active_positions = self.active_strategies[strategy_id]["active_positions"]
        completed_positions = self.active_strategies[strategy_id]["completed_positions"]
        performance = self.active_strategies[strategy_id]["performance"]
        
        # Load new strategy
        if not self.load_strategy(strategy_id, strategy_params):
            return False
        
        # Restore active positions and performance
        self.active_strategies[strategy_id]["active_positions"] = active_positions
        self.active_strategies[strategy_id]["completed_positions"] = completed_positions
        self.active_strategies[strategy_id]["performance"] = performance
        
        logger.info(f"Strategy {strategy_id} updated successfully")
        return True
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        Delete a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            
        Returns:
            bool: True if strategy deleted successfully, False otherwise
        """
        logger.info(f"Deleting strategy {strategy_id}")
        
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
        
        # Check if strategy has active positions
        if self.active_strategies[strategy_id]["active_positions"]:
            logger.warning(f"Strategy {strategy_id} has active positions")
        
        # Delete strategy
        del self.active_strategies[strategy_id]
        
        logger.info(f"Strategy {strategy_id} deleted successfully")
        return True
    
    def get_strategy(self, strategy_id: str) -> Dict:
        """
        Get strategy details.
        
        Args:
            strategy_id: Unique identifier for the strategy
            
        Returns:
            Dict: Strategy details
        """
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return {}
        
        return self.active_strategies[strategy_id]
    
    def list_strategies(self) -> List[Dict]:
        """
        List all active strategies.
        
        Returns:
            List[Dict]: List of strategy details
        """
        return [
            {
                "strategy_id": strategy_id,
                "params": strategy["params"],
                "created_at": strategy["created_at"],
                "active_positions_count": len(strategy["active_positions"]),
                "completed_positions_count": len(strategy["completed_positions"]),
                "performance": strategy["performance"]
            }
            for strategy_id, strategy in self.active_strategies.items()
        ]
    
    def apply_strategy(self, strategy_id: str, opportunities: List[Dict]) -> List[Dict]:
        """
        Apply strategy parameters to filter and prioritize opportunities.
        
        Args:
            strategy_id: Unique identifier for the strategy
            opportunities: List of trading opportunities
            
        Returns:
            List[Dict]: Filtered and prioritized opportunities
        """
        logger.info(f"Applying strategy {strategy_id} to {len(opportunities)} opportunities")
        
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return []
        
        strategy = self.active_strategies[strategy_id]
        params = strategy["params"]
        
        # Filter opportunities based on strategy parameters
        filtered_opportunities = self._filter_opportunities(opportunities, params)
        
        # Calculate position sizes
        sized_opportunities = self._calculate_position_sizes(filtered_opportunities, params)
        
        # Prioritize opportunities
        prioritized_opportunities = self._prioritize_opportunities(sized_opportunities, params)
        
        # Limit to max simultaneous positions
        max_positions = int(params["maxSimultaneousPositions"])
        active_positions_count = len(strategy["active_positions"])
        available_slots = max(0, max_positions - active_positions_count)
        
        final_opportunities = prioritized_opportunities[:available_slots]
        
        logger.info(f"Strategy {strategy_id} applied, {len(final_opportunities)} opportunities selected")
        return final_opportunities
    
    def _filter_opportunities(self, opportunities: List[Dict], strategy_params: Dict) -> List[Dict]:
        """
        Filter opportunities based on strategy parameters.
        
        Args:
            opportunities: List of trading opportunities
            strategy_params: Strategy parameters
            
        Returns:
            List[Dict]: Filtered opportunities
        """
        filtered = []
        
        # Get strategy parameters
        min_confidence = float(strategy_params["minConfidence"])
        categories = strategy_params["categories"]
        time_horizon = strategy_params["timeHorizon"]
        
        # Convert time horizon to hours
        time_hours = self._parse_time_horizon(time_horizon)
        
        for opportunity in opportunities:
            # Filter by confidence score
            if opportunity.get("confidence_score", 0) < min_confidence:
                continue
            
            # Filter by category (if market category is available)
            if "market_category" in opportunity and categories:
                if opportunity["market_category"] not in categories:
                    continue
            
            # Filter by time window (if time window is available)
            if "timeWindow" in opportunity and time_hours is not None:
                # Parse time window
                try:
                    window_parts = opportunity["timeWindow"].split("-")
                    if len(window_parts) == 2:
                        start_time_str, end_time_str = window_parts
                        
                        # Simple parsing for HH:MM format
                        end_time_parts = end_time_str.strip().split(":")
                        if len(end_time_parts) == 2:
                            end_hour = int(end_time_parts[0])
                            
                            # Get current hour
                            current_hour = datetime.now().hour
                            
                            # Calculate hours difference
                            hours_diff = (end_hour - current_hour) % 24
                            
                            # Filter if outside time horizon
                            if hours_diff > time_hours:
                                continue
                except Exception as e:
                    logger.warning(f"Error parsing time window: {str(e)}")
            
            # Add opportunity to filtered list
            filtered.append(opportunity)
        
        return filtered
    
    def _calculate_position_sizes(self, opportunities: List[Dict], strategy_params: Dict) -> List[Dict]:
        """
        Calculate position sizes for opportunities based on strategy parameters.
        
        Args:
            opportunities: List of trading opportunities
            strategy_params: Strategy parameters
            
        Returns:
            List[Dict]: Opportunities with position sizes
        """
        # Get strategy parameters
        budget = float(strategy_params["budget"])
        
        # Get position sizing parameters
        position_sizing = strategy_params.get("positionSizing", {})
        max_per_trade = float(position_sizing.get("maxPerTrade", 20))
        scaling = position_sizing.get("scaling", "equal")
        
        # Calculate max amount per trade
        max_amount = budget * (max_per_trade / 100)
        
        # Apply position sizing
        for opportunity in opportunities:
            if scaling == "confidence":
                # Scale position size by confidence score
                confidence = opportunity.get("confidence_score", 50) / 100
                position_size = max_amount * confidence
            elif scaling == "risk":
                # Scale position size inversely by risk (higher risk = smaller position)
                risk_score = 1 - (opportunity.get("confidence_score", 50) / 100)
                position_size = max_amount * (1 - (risk_score * 0.8))
            else:
                # Equal position sizing
                position_size = max_amount
            
            # Calculate number of contracts based on current price
            current_price = opportunity.get("current_price", 0.5)
            if current_price > 0:
                contracts = math.floor(position_size / (current_price / 100))  # Price in cents
            else:
                contracts = 0
            
            # Ensure at least 1 contract
            contracts = max(1, contracts)
            
            # Calculate total cost
            cost = (contracts * current_price) / 100  # Convert cents to dollars
            
            # Update opportunity with position size information
            opportunity["contracts"] = contracts
            opportunity["cost"] = cost
            
            # Calculate expected return
            target_price = opportunity.get("target_price", current_price)
            if current_price > 0:
                expected_return_pct = ((target_price - current_price) / current_price) * 100
                expected_return = cost * (expected_return_pct / 100)
                
                opportunity["expectedReturn"] = expected_return_pct
                opportunity["expectedReturnAmount"] = expected_return
        
        return opportunities
    
    def _prioritize_opportunities(self, opportunities: List[Dict], strategy_params: Dict) -> List[Dict]:
        """
        Prioritize opportunities based on strategy parameters.
        
        Args:
            opportunities: List of trading opportunities
            strategy_params: Strategy parameters
            
        Returns:
            List[Dict]: Prioritized opportunities
        """
        # Get strategy parameters
        risk_level = int(strategy_params["riskLevel"])
        target_profit = float(strategy_params["targetProfit"])
        
        # Define scoring function based on strategy parameters
        def score_opportunity(opportunity):
            confidence = opportunity.get("confidence_score", 0)
            expected_return = opportunity.get("expectedReturn", 0)
            
            # Higher risk level means more weight on expected return vs. confidence
            confidence_weight = 1 - (risk_level / 10)
            return_weight = risk_level / 10
            
            # Calculate score
            score = (confidence * confidence_weight) + (expected_return * return_weight)
            
            # Bonus for opportunities close to target profit
            if abs(expected_return - target_profit) < 5:
                score *= 1.2
            
            return score
        
        # Score and sort opportunities
        for opportunity in opportunities:
            opportunity["priority_score"] = score_opportunity(opportunity)
        
        prioritized = sorted(opportunities, key=lambda x: x.get("priority_score", 0), reverse=True)
        
        return prioritized
    
    def _parse_time_horizon(self, time_horizon: str) -> Optional[float]:
        """
        Parse time horizon string to hours.
        
        Args:
            time_horizon: Time horizon string (e.g., "1h", "30m", "2d")
            
        Returns:
            float: Time horizon in hours, or None if parsing fails
        """
        try:
            # Extract number and unit
            if time_horizon.endswith("m"):
                minutes = float(time_horizon[:-1])
                return minutes / 60
            elif time_horizon.endswith("h"):
                return float(time_horizon[:-1])
            elif time_horizon.endswith("d"):
                days = float(time_horizon[:-1])
                return days * 24
            else:
                # Try to parse as hours
                return float(time_horizon)
        except ValueError:
            logger.warning(f"Could not parse time horizon: {time_horizon}")
            return None
    
    def record_position(self, strategy_id: str, position: Dict) -> bool:
        """
        Record a new active position for a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            position: Position details
            
        Returns:
            bool: True if position recorded successfully, False otherwise
        """
        logger.info(f"Recording position for strategy {strategy_id}")
        
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
        
        # Add position ID and timestamp if not present
        if "position_id" not in position:
            position["position_id"] = f"pos_{len(self.active_strategies[strategy_id]['active_positions']) + 1}_{int(datetime.now().timestamp())}"
        
        if "timestamp" not in position:
            position["timestamp"] = datetime.now().isoformat()
        
        # Add position to active positions
        self.active_strategies[strategy_id]["active_positions"].append(position)
        
        logger.info(f"Position {position.get('position_id')} recorded for strategy {strategy_id}")
        return True
    
    def update_position(self, strategy_id: str, position_id: str, updates: Dict) -> bool:
        """
        Update an active position for a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            position_id: Unique identifier for the position
            updates: Position updates
            
        Returns:
            bool: True if position updated successfully, False otherwise
        """
        logger.info(f"Updating position {position_id} for strategy {strategy_id}")
        
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
        
        # Find position
        for i, position in enumerate(self.active_strategies[strategy_id]["active_positions"]):
            if position.get("position_id") == position_id:
                # Update position
                self.active_strategies[strategy_id]["active_positions"][i].update(updates)
                
                logger.info(f"Position {position_id} updated for strategy {strategy_id}")
                return True
        
        logger.error(f"Position {position_id} not found for strategy {strategy_id}")
        return False
    
    def close_position(self, strategy_id: str, position_id: str, exit_price: float, 
                      exit_timestamp: str = None, profit_loss: float = None) -> bool:
        """
        Close an active position and move it to completed positions.
        
        Args:
            strategy_id: Unique identifier for the strategy
            position_id: Unique identifier for the position
            exit_price: Exit price
            exit_timestamp: Exit timestamp (default: current time)
            profit_loss: Profit/loss amount (default: calculated from position)
            
        Returns:
            bool: True if position closed successfully, False otherwise
        """
        logger.info(f"Closing position {position_id} for strategy {strategy_id}")
        
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
        
        # Find position
        position_index = None
        position = None
        
        for i, pos in enumerate(self.active_strategies[strategy_id]["active_positions"]):
            if pos.get("position_id") == position_id:
                position_index = i
                position = pos
                break
        
        if position_index is None:
            logger.error(f"Position {position_id} not found for strategy {strategy_id}")
            return False
        
        # Set exit details
        position["exit_price"] = exit_price
        position["exit_timestamp"] = exit_timestamp or datetime.now().isoformat()
        
        # Calculate profit/loss if not provided
        if profit_loss is None:
            entry_price = position.get("current_price", 0)
            contracts = position.get("contracts", 0)
            
            if position.get("position") == "YES":
                profit_loss = ((exit_price - entry_price) / 100) * contracts  # Convert cents to dollars
            else:  # NO position
                profit_loss = ((entry_price - exit_price) / 100) * contracts  # Convert cents to dollars
        
        position["profit_loss"] = profit_loss
        
        # Calculate return percentage
        cost = position.get("cost", 0)
        if cost > 0:
            position["return_percentage"] = (profit_loss / cost) * 100
        
        # Update strategy performance
        if profit_loss > 0:
            self.active_strategies[strategy_id]["performance"]["win_count"] += 1
        else:
            self.active_strategies[strategy_id]["performance"]["loss_count"] += 1
        
        self.active_strategies[strategy_id]["performance"]["total_profit"] += profit_loss
        self.active_strategies[strategy_id]["performance"]["total_investment"] += cost
        
        # Move position from active to completed
        self.active_strategies[strategy_id]["completed_positions"].append(position)
        del self.active_strategies[strategy_id]["active_positions"][position_index]
        
        logger.info(f"Position {position_id} closed for strategy {strategy_id} with P/L: ${profit_loss:.2f}")
        return True
    
    def get_active_positions(self, strategy_id: str) -> List[Dict]:
        """
        Get active positions for a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            
        Returns:
            List[Dict]: Active positions
        """
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return []
        
        return self.active_strategies[strategy_id]["active_positions"]
    
    def get_completed_positions(self, strategy_id: str) -> List[Dict]:
        """
        Get completed positions for a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            
        Returns:
            List[Dict]: Completed positions
        """
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return []
        
        return self.active_strategies[strategy_id]["completed_positions"]
    
    def get_strategy_performance(self, strategy_id: str) -> Dict:
        """
        Get performance metrics for a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            
        Returns:
            Dict: Performance metrics
        """
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return {}
        
        performance = self.active_strategies[strategy_id]["performance"]
        
        # Calculate additional metrics
        total_trades = performance["win_count"] + performance["loss_count"]
        win_rate = (performance["win_count"] / total_trades) * 100 if total_trades > 0 else 0
        
        total_investment = performance["total_investment"]
        total_profit = performance["total_profit"]
        roi = (total_profit / total_investment) * 100 if total_investment > 0 else 0
        
        return {
            "win_count": performance["win_count"],
            "loss_count": performance["loss_count"],
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "total_investment": total_investment,
            "roi": roi
        }
    
    def adapt_strategy(self, strategy_id: str, market_conditions: Dict) -> Dict:
        """
        Adapt strategy parameters based on market conditions.
        
        Args:
            strategy_id: Unique identifier for the strategy
            market_conditions: Dictionary of market condition indicators
            
        Returns:
            Dict: Updated strategy parameters
        """
        logger.info(f"Adapting strategy {strategy_id} based on market conditions")
        
        if strategy_id not in self.active_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return {}
        
        strategy = self.active_strategies[strategy_id]
        params = strategy["params"].copy()
        
        # Extract market condition indicators
        volatility = market_conditions.get("volatility", 0.5)  # 0-1 scale
        trend_strength = market_conditions.get("trend_strength", 0.5)  # 0-1 scale
        liquidity = market_conditions.get("liquidity", 0.5)  # 0-1 scale
        
        # Adapt risk level based on volatility
        # Higher volatility -> lower risk level
        risk_level = int(params["riskLevel"])
        if volatility > 0.7:
            risk_level = max(1, risk_level - 2)
        elif volatility < 0.3:
            risk_level = min(10, risk_level + 1)
        
        params["riskLevel"] = risk_level
        
        # Adapt position sizing based on trend strength
        # Stronger trend -> larger positions
        position_sizing = params.get("positionSizing", {}).copy()
        max_per_trade = float(position_sizing.get("maxPerTrade", 20))
        
        if trend_strength > 0.7:
            max_per_trade = min(50, max_per_trade * 1.2)
        elif trend_strength < 0.3:
            max_per_trade = max(5, max_per_trade * 0.8)
        
        position_sizing["maxPerTrade"] = max_per_trade
        params["positionSizing"] = position_sizing
        
        # Adapt minimum confidence based on liquidity
        # Lower liquidity -> higher minimum confidence
        min_confidence = float(params["minConfidence"])
        
        if liquidity < 0.3:
            min_confidence = min(90, min_confidence + 10)
        elif liquidity > 0.7:
            min_confidence = max(50, min_confidence - 5)
        
        params["minConfidence"] = min_confidence
        
        # Update strategy parameters
        self.update_strategy(strategy_id, params)
        
        logger.info(f"Strategy {strategy_id} adapted: risk={risk_level}, max_per_trade={max_per_trade}, min_confidence={min_confidence}")
        return params


# Example usage
if __name__ == "__main__":
    # Create strategy processor
    processor = StrategyProcessor()
    
    # Example strategy parameters
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
        "executionMode": "yolo"
    }
    
    # Load strategy
    processor.load_strategy("strategy1", strategy_params)
    
    # Example opportunities
    opportunities = [
        {
            "type": "momentum",
            "position": "YES",
            "current_price": 33,
            "target_price": 48,
            "confidence_score": 82,
            "market_category": "crypto",
            "timeWindow": "11:00-12:00 EDT",
            "reasoning": "BTC showing strong upward momentum"
        },
        {
            "type": "mispricing",
            "position": "NO",
            "current_price": 67,
            "target_price": 52,
            "confidence_score": 75,
            "market_category": "crypto",
            "timeWindow": "11:00-12:00 EDT",
            "reasoning": "Market appears overpriced"
        },
        {
            "type": "technical_pattern",
            "position": "YES",
            "current_price": 25,
            "target_price": 35,
            "confidence_score": 60,
            "market_category": "sports",
            "timeWindow": "14:00-15:00 EDT",
            "reasoning": "Double bottom pattern detected"
        }
    ]
    
    # Apply strategy
    filtered_opportunities = processor.apply_strategy("strategy1", opportunities)
    
    # Print results
    print(f"Filtered opportunities: {len(filtered_opportunities)}")
    for opportunity in filtered_opportunities:
        print(f"Position: {opportunity['position']} at {opportunity['current_price']}")
        print(f"Contracts: {opportunity.get('contracts')}, Cost: ${opportunity.get('cost'):.2f}")
        print(f"Expected return: {opportunity.get('expectedReturn'):.2f}%")
        print(f"Priority score: {opportunity.get('priority_score'):.2f}")
        print()
