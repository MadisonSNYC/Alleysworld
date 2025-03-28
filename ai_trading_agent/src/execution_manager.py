"""
Execution Manager for AI Trading Agent

This module handles trade execution based on recommendations, monitors positions,
implements exit strategies, and tracks performance. It incorporates insights from
trading psychology, sports betting, and online prediction markets.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid
import time

logger = logging.getLogger('execution_manager')

class ExecutionManager:
    """Manages trade execution, monitoring, and exit strategies with psychological insights."""
    
    def __init__(self, api_client):
        """Initialize with API client for trade execution."""
        self.api_client = api_client
        self.active_positions = {}
        self.execution_history = []
        self.psychological_factors = {
            "market_sentiment": 0.5,  # 0-1 scale (fear to greed)
            "crowd_behavior": 0.5,    # 0-1 scale (contrarian to momentum)
            "recency_bias": 0.5       # 0-1 scale (weak to strong)
        }
    
    def execute_trade(self, recommendation: Dict, execution_mode: str = "manual") -> Dict:
        """Execute trade based on recommendation and execution mode."""
        logger.info(f"Executing trade for {recommendation.get('asset')} in {execution_mode} mode")
        
        # Skip execution in manual mode (return pending status)
        if execution_mode == "manual":
            return {
                "status": "pending_approval",
                "recommendation_id": recommendation.get("id"),
                "timestamp": datetime.now().isoformat()
            }
        
        # Execute trade in YOLO mode
        try:
            # Extract trade parameters
            ticker = recommendation.get("asset")
            position_type = recommendation.get("position")  # YES or NO
            contracts = recommendation.get("contracts", 0)
            price = recommendation.get("entryPrice", 0)
            
            # Apply psychological adjustments to position size
            contracts = self._adjust_position_size(recommendation, contracts)
            
            # Place order via API client
            order_result = self.api_client.place_order(
                ticker=ticker,
                side="buy",
                type=position_type.lower(),
                price=price,
                size=contracts
            )
            
            # Create position record
            position_id = str(uuid.uuid4())[:8]
            position = {
                "position_id": position_id,
                "recommendation_id": recommendation.get("id"),
                "ticker": ticker,
                "position_type": position_type,
                "contracts": contracts,
                "entry_price": price,
                "entry_time": datetime.now().isoformat(),
                "target_exit": recommendation.get("targetExit"),
                "stop_loss": recommendation.get("stopLoss"),
                "status": "active",
                "order_id": order_result.get("order_id")
            }
            
            # Store position
            self.active_positions[position_id] = position
            
            # Record execution
            execution_record = {
                "type": "entry",
                "position_id": position_id,
                "recommendation_id": recommendation.get("id"),
                "ticker": ticker,
                "position_type": position_type,
                "contracts": contracts,
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "order_result": order_result
            }
            
            self.execution_history.append(execution_record)
            
            return {
                "status": "executed",
                "position_id": position_id,
                "order_id": order_result.get("order_id"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Trade execution failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "recommendation_id": recommendation.get("id"),
                "timestamp": datetime.now().isoformat()
            }
    
    def _adjust_position_size(self, recommendation: Dict, base_size: int) -> int:
        """Adjust position size based on psychological factors and market conditions."""
        # Get confidence score
        confidence = recommendation.get("confidence", 50) / 100
        
        # Apply market sentiment adjustment
        # In high fear markets, reduce size for YES positions and increase for NO
        sentiment_factor = self.psychological_factors["market_sentiment"]
        position_type = recommendation.get("position")
        
        if position_type == "YES":
            sentiment_adjustment = 1 + (sentiment_factor - 0.5)
        else:  # NO position
            sentiment_adjustment = 1 + (0.5 - sentiment_factor)
        
        # Apply crowd behavior adjustment
        # For contrarian strategies, go against the crowd
        crowd_factor = self.psychological_factors["crowd_behavior"]
        crowd_adjustment = 1 + (0.2 * (confidence - 0.5) * crowd_factor)
        
        # Calculate adjusted size
        adjusted_size = int(base_size * sentiment_adjustment * crowd_adjustment)
        
        # Ensure minimum size of 1 contract
        return max(1, adjusted_size)
    
    def monitor_positions(self, market_data: Dict) -> List[Dict]:
        """Monitor active positions and implement exit strategies."""
        logger.info(f"Monitoring {len(self.active_positions)} active positions")
        
        actions = []
        
        for position_id, position in list(self.active_positions.items()):
            ticker = position.get("ticker")
            
            # Skip if market data doesn't contain this ticker
            if ticker not in market_data:
                continue
            
            # Get current market prices
            current_data = market_data[ticker]
            current_yes_price = current_data.get("yes_price", 0)
            current_no_price = current_data.get("no_price", 0)
            
            # Determine relevant price based on position type
            position_type = position.get("position_type")
            current_price = current_yes_price if position_type == "YES" else current_no_price
            
            # Check exit conditions
            target_exit_range = position.get("target_exit", "").split("-")
            stop_loss = position.get("stop_loss", 0)
            
            # Parse target exit range
            if len(target_exit_range) == 2:
                target_low = float(target_exit_range[0])
                target_high = float(target_exit_range[1])
                
                # Check if price is within target range
                if target_low <= current_price <= target_high:
                    # Execute exit at target
                    exit_result = self._execute_exit(position_id, current_price, "target_reached")
                    actions.append(exit_result)
                    continue
            
            # Check stop loss
            if (position_type == "YES" and current_price <= stop_loss) or \
               (position_type == "NO" and current_price >= stop_loss):
                # Execute exit at stop loss
                exit_result = self._execute_exit(position_id, current_price, "stop_loss")
                actions.append(exit_result)
                continue
            
            # Check time-based exit (if close to expiration)
            if "close_time" in current_data:
                close_time = datetime.fromisoformat(current_data["close_time"].replace('Z', '+00:00'))
                time_to_close = (close_time - datetime.now()).total_seconds() / 60  # minutes
                
                if time_to_close <= 5:  # 5 minutes to expiration
                    # Execute exit before expiration
                    exit_result = self._execute_exit(position_id, current_price, "expiration")
                    actions.append(exit_result)
                    continue
            
            # Apply dynamic exit strategy based on price movement
            entry_price = position.get("entry_price", 0)
            if entry_price > 0:
                price_change_pct = (current_price - entry_price) / entry_price
                
                # Exit if significant adverse movement (dynamic stop loss)
                if (position_type == "YES" and price_change_pct < -0.15) or \
                   (position_type == "NO" and price_change_pct > 0.15):
                    exit_result = self._execute_exit(position_id, current_price, "dynamic_stop")
                    actions.append(exit_result)
                    continue
                
                # Take partial profits if significant favorable movement
                if ((position_type == "YES" and price_change_pct > 0.25) or \
                    (position_type == "NO" and price_change_pct < -0.25)) and \
                   position.get("contracts", 0) > 2:
                    
                    # Take profit on half of position
                    partial_contracts = position.get("contracts", 0) // 2
                    exit_result = self._execute_partial_exit(
                        position_id, current_price, partial_contracts, "partial_profit"
                    )
                    actions.append(exit_result)
        
        return actions
    
    def _execute_exit(self, position_id: str, price: float, reason: str) -> Dict:
        """Execute complete exit for a position."""
        position = self.active_positions.get(position_id)
        if not position:
            return {"status": "failed", "error": "Position not found"}
        
        try:
            # Place sell order
            order_result = self.api_client.place_order(
                ticker=position.get("ticker"),
                side="sell",
                type=position.get("position_type").lower(),
                price=price,
                size=position.get("contracts", 0)
            )
            
            # Calculate profit/loss
            entry_price = position.get("entry_price", 0)
            contracts = position.get("contracts", 0)
            
            if position.get("position_type") == "YES":
                profit_loss = ((price - entry_price) / 100) * contracts  # Convert cents to dollars
            else:  # NO position
                profit_loss = ((entry_price - price) / 100) * contracts  # Convert cents to dollars
            
            # Update position status
            position["status"] = "closed"
            position["exit_price"] = price
            position["exit_time"] = datetime.now().isoformat()
            position["exit_reason"] = reason
            position["profit_loss"] = profit_loss
            
            # Record execution
            execution_record = {
                "type": "exit",
                "position_id": position_id,
                "ticker": position.get("ticker"),
                "position_type": position.get("position_type"),
                "contracts": position.get("contracts", 0),
                "price": price,
                "reason": reason,
                "profit_loss": profit_loss,
                "timestamp": datetime.now().isoformat(),
                "order_result": order_result
            }
            
            self.execution_history.append(execution_record)
            
            # Remove from active positions
            del self.active_positions[position_id]
            
            # Update psychological factors based on outcome
            self._update_psychological_factors(profit_loss > 0)
            
            return {
                "status": "executed",
                "action": "exit",
                "position_id": position_id,
                "price": price,
                "reason": reason,
                "profit_loss": profit_loss,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Exit execution failed: {str(e)}")
            return {
                "status": "failed",
                "action": "exit",
                "position_id": position_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_partial_exit(self, position_id: str, price: float, 
                             contracts: int, reason: str) -> Dict:
        """Execute partial exit for a position."""
        position = self.active_positions.get(position_id)
        if not position:
            return {"status": "failed", "error": "Position not found"}
        
        try:
            # Place sell order for partial position
            order_result = self.api_client.place_order(
                ticker=position.get("ticker"),
                side="sell",
                type=position.get("position_type").lower(),
                price=price,
                size=contracts
            )
            
            # Calculate profit/loss for partial exit
            entry_price = position.get("entry_price", 0)
            
            if position.get("position_type") == "YES":
                profit_loss = ((price - entry_price) / 100) * contracts  # Convert cents to dollars
            else:  # NO position
                profit_loss = ((entry_price - price) / 100) * contracts  # Convert cents to dollars
            
            # Update position
            position["contracts"] -= contracts
            
            # Record execution
            execution_record = {
                "type": "partial_exit",
                "position_id": position_id,
                "ticker": position.get("ticker"),
                "position_type": position.get("position_type"),
                "contracts": contracts,
                "remaining_contracts": position["contracts"],
                "price": price,
                "reason": reason,
                "profit_loss": profit_loss,
                "timestamp": datetime.now().isoformat(),
                "order_result": order_result
            }
            
            self.execution_history.append(execution_record)
            
            # Update psychological factors based on outcome
            self._update_psychological_factors(profit_loss > 0)
            
            return {
                "status": "executed",
                "action": "partial_exit",
                "position_id": position_id,
                "contracts": contracts,
                "remaining_contracts": position["contracts"],
                "price": price,
                "reason": reason,
                "profit_loss": profit_loss,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Partial exit execution failed: {str(e)}")
            return {
                "status": "failed",
                "action": "partial_exit",
                "position_id": position_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _update_psychological_factors(self, win: bool):
        """Update psychological factors based on trade outcomes."""
        # Update market sentiment based on recent wins/losses
        if win:
            # Winning increases greed sentiment
            self.psychological_factors["market_sentiment"] = min(
                1.0, self.psychological_factors["market_sentiment"] + 0.05
            )
        else:
            # Losing increases fear sentiment
            self.psychological_factors["market_sentiment"] = max(
                0.0, self.psychological_factors["market_sentiment"] - 0.05
            )
        
        # Update recency bias (stronger after consecutive similar outcomes)
        self.psychological_factors["recency_bias"] = min(
            1.0, self.psychological_factors["recency_bias"] + 0.1
        )
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics from execution history."""
        # Filter completed trades
        completed_trades = [
            record for record in self.execution_history
            if record.get("type") == "exit"
        ]
        
        # Calculate metrics
        total_trades = len(completed_trades)
        winning_trades = sum(1 for trade in completed_trades if trade.get("profit_loss", 0) > 0)
        losing_trades = total_trades - winning_trades
        
        total_profit = sum(trade.get("profit_loss", 0) for trade in completed_trades)
        
        # Calculate win rate and average profit
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "average_profit": avg_profit,
            "psychological_factors": self.psychological_factors
        }
