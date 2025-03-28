"""
Analysis Engine for AI Trading Agent

This module provides market data analysis functionality for the AI Trading Agent.
It identifies trading opportunities based on price patterns, market psychology,
and other factors.
"""

import logging
import math
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('analysis_engine')

class AnalysisEngine:
    """
    Analysis Engine for AI Trading Agent.
    
    This engine processes market data to identify trading opportunities
    based on price patterns, market psychology, and other factors.
    """
    
    def __init__(self):
        """Initialize the Analysis Engine."""
        logger.info("Initializing Analysis Engine")
        
        # Initialize state
        self.market_cache = {}
    
    def process_market_data(self, market_data: Dict) -> Dict:
        """
        Process market data to identify trading opportunities.
        
        Args:
            market_data: Comprehensive market data bundle
            
        Returns:
            Dict: Analysis results including opportunities
        """
        ticker = market_data.get("ticker", "unknown")
        logger.info(f"Processing market data for {ticker}")
        
        # Initialize results
        analysis_results = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "opportunities": []
        }
        
        try:
            # Perform price analysis
            logger.info("Performing price analysis")
            analysis_results["price_analysis"] = self.analyze_price_patterns(market_data)
        except Exception as e:
            logger.error(f"Error in price analysis: {str(e)}")
        
        try:
            # Analyze market psychology
            logger.info("Analyzing market psychology")
            analysis_results["market_psychology"] = self.analyze_market_psychology(
                market_data.get("order_book", {}),
                market_data.get("recent_trades", []),
                market_data.get("history", [])
            )
        except Exception as e:
            logger.error(f"Error in market psychology analysis: {str(e)}")
            analysis_results["market_psychology"] = {
                "sentiment": "neutral",
                "confidence": 50,
                "factors": []
            }
        
        try:
            # Identify opportunities
            opportunities = self.identify_opportunities(
                market_data,
                analysis_results.get("price_analysis", {}),
                analysis_results.get("market_psychology", {})
            )
            
            analysis_results["opportunities"] = opportunities
        except Exception as e:
            logger.error(f"Error identifying opportunities: {str(e)}")
        
        return analysis_results
    
    def analyze_price_patterns(self, market_data: Dict) -> Dict:
        """
        Analyze price patterns to identify trends and reversals.
        
        Args:
            market_data: Market data bundle
            
        Returns:
            Dict: Price analysis results
        """
        # Extract history data
        history = market_data.get("history", [])
        
        # Not enough data for analysis
        if len(history) < 5:
            return {
                "trend": "unknown",
                "strength": 0,
                "patterns": []
            }
        
        # Extract yes prices from history (most recent first)
        prices = []
        for point in history:
            if "yes_price" in point:
                prices.append(point["yes_price"])
        
        # Reverse to get chronological order
        prices.reverse()
        
        # Calculate trend
        trend = "neutral"
        strength = 0
        
        if len(prices) >= 10:
            # Simple moving averages
            sma5 = sum(prices[-5:]) / 5
            sma10 = sum(prices[-10:]) / 10
            
            if sma5 > sma10:
                trend = "bullish"
                strength = min(100, int((sma5 - sma10) / sma10 * 1000))
            elif sma5 < sma10:
                trend = "bearish"
                strength = min(100, int((sma10 - sma5) / sma10 * 1000))
        
        # Identify patterns
        patterns = []
        
        # Current market data
        current_price = market_data.get("yes_bid", 0)
        
        # Check for momentum
        if len(prices) >= 5 and all(prices[i] < prices[i+1] for i in range(len(prices)-5, len(prices)-1)):
            patterns.append({
                "name": "momentum",
                "direction": "up",
                "strength": min(100, int((prices[-1] - prices[-5]) / prices[-5] * 100))
            })
        elif len(prices) >= 5 and all(prices[i] > prices[i+1] for i in range(len(prices)-5, len(prices)-1)):
            patterns.append({
                "name": "momentum",
                "direction": "down",
                "strength": min(100, int((prices[-5] - prices[-1]) / prices[-5] * 100))
            })
        
        # Check for mean reversion
        if len(prices) >= 20:
            mean = sum(prices[-20:]) / 20
            std_dev = math.sqrt(sum((p - mean) ** 2 for p in prices[-20:]) / 20)
            
            if std_dev > 0:
                z_score = (current_price - mean) / std_dev
                
                if z_score > 1.5:
                    patterns.append({
                        "name": "mean_reversion",
                        "direction": "down",
                        "strength": min(100, int(abs(z_score) * 20))
                    })
                elif z_score < -1.5:
                    patterns.append({
                        "name": "mean_reversion",
                        "direction": "up",
                        "strength": min(100, int(abs(z_score) * 20))
                    })
        
        return {
            "trend": trend,
            "strength": strength,
            "patterns": patterns
        }
    
    def analyze_market_psychology(self, order_book: Dict, recent_trades: List, history: List) -> Dict:
        """
        Analyze market psychology based on order book and recent trades.
        
        Args:
            order_book: Market order book
            recent_trades: Recent trades
            history: Price history
            
        Returns:
            Dict: Market psychology analysis
        """
        # Default neutral sentiment
        sentiment = "neutral"
        confidence = 50
        factors = []
        
        # Analyze order book imbalance
        if order_book:
            yes_bid_volume = sum(bid.get("size", 0) for bid in order_book.get("yes_bids", []))
            yes_ask_volume = sum(ask.get("size", 0) for ask in order_book.get("yes_asks", []))
            
            if yes_bid_volume > 0 and yes_ask_volume > 0:
                ratio = yes_bid_volume / (yes_bid_volume + yes_ask_volume)
                
                if ratio > 0.6:
                    factors.append({
                        "name": "order_imbalance",
                        "direction": "bullish",
                        "strength": min(100, int(ratio * 100))
                    })
                    sentiment = "bullish"
                    confidence += 10
                elif ratio < 0.4:
                    factors.append({
                        "name": "order_imbalance",
                        "direction": "bearish",
                        "strength": min(100, int((1 - ratio) * 100))
                    })
                    sentiment = "bearish"
                    confidence += 10
        
        # Analyze recent trade direction
        if recent_trades and len(recent_trades) >= 5:
            buy_volume = 0
            sell_volume = 0
            
            for trade in recent_trades:
                if trade.get("side") == "buy" and trade.get("type") == "yes":
                    buy_volume += trade.get("count", 0)
                elif trade.get("side") == "sell" and trade.get("type") == "yes":
                    sell_volume += trade.get("count", 0)
            
            if buy_volume > 0 and sell_volume > 0:
                ratio = buy_volume / (buy_volume + sell_volume)
                
                if ratio > 0.6:
                    factors.append({
                        "name": "trade_flow",
                        "direction": "bullish",
                        "strength": min(100, int(ratio * 100))
                    })
                    
                    if sentiment == "bullish":
                        confidence += 15
                    else:
                        sentiment = "bullish"
                        confidence += 5
                elif ratio < 0.4:
                    factors.append({
                        "name": "trade_flow",
                        "direction": "bearish",
                        "strength": min(100, int((1 - ratio) * 100))
                    })
                    
                    if sentiment == "bearish":
                        confidence += 15
                    else:
                        sentiment = "bearish"
                        confidence += 5
            
            # Check for acceleration in trade frequency
            if len(recent_trades) >= 10:
                # Use "time" field instead of "timestamp"
                try:
                    # Check if trades have "time" field
                    if "time" in recent_trades[0]:
                        first_trade_time = datetime.fromisoformat(recent_trades[-1].get("time", "").replace('Z', '+00:00'))
                        last_trade_time = datetime.fromisoformat(recent_trades[0].get("time", "").replace('Z', '+00:00'))
                        
                        if first_trade_time and last_trade_time:
                            time_span = (last_trade_time - first_trade_time).total_seconds()
                            trades_per_minute = len(recent_trades) / (time_span / 60) if time_span > 0 else 0
                            
                            if trades_per_minute > 5:
                                factors.append({
                                    "name": "trade_acceleration",
                                    "direction": sentiment,
                                    "strength": min(100, int(trades_per_minute * 10))
                                })
                                confidence += 5
                except Exception as e:
                    logger.error(f"Error analyzing trade frequency: {str(e)}")
        
        # Analyze price volatility
        if history and len(history) >= 10:
            prices = []
            for point in history:
                if "yes_price" in point:
                    prices.append(point["yes_price"])
            
            if prices:
                mean = sum(prices) / len(prices)
                std_dev = math.sqrt(sum((p - mean) ** 2 for p in prices) / len(prices))
                
                if mean > 0:
                    volatility = std_dev / mean
                    
                    if volatility > 0.1:
                        factors.append({
                            "name": "high_volatility",
                            "direction": "neutral",
                            "strength": min(100, int(volatility * 500))
                        })
                        confidence -= 5
        
        # Ensure confidence is within bounds
        confidence = max(0, min(100, confidence))
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "factors": factors
        }
    
    def identify_opportunities(self, market_data: Dict, price_analysis: Dict, 
                              market_psychology: Dict) -> List:
        """
        Identify trading opportunities based on analysis results.
        
        Args:
            market_data: Market data bundle
            price_analysis: Price analysis results
            market_psychology: Market psychology analysis
            
        Returns:
            List: Trading opportunities
        """
        opportunities = []
        
        ticker = market_data.get("ticker", "unknown")
        title = market_data.get("title", "")
        yes_bid = market_data.get("yes_bid", 0)
        yes_ask = market_data.get("yes_ask", 0)
        no_bid = market_data.get("no_bid", 0)
        no_ask = market_data.get("no_ask", 0)
        close_time = market_data.get("close_time", "")
        
        # Convert close time to datetime
        try:
            if close_time:
                close_time_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
                time_to_close = (close_time_dt - datetime.now()).total_seconds() / 3600  # hours
            else:
                time_to_close = 24  # default to 24 hours
        except Exception:
            time_to_close = 24  # default to 24 hours
        
        # Extract analysis data
        trend = price_analysis.get("trend", "neutral")
        trend_strength = price_analysis.get("strength", 0)
        patterns = price_analysis.get("patterns", [])
        
        sentiment = market_psychology.get("sentiment", "neutral")
        sentiment_confidence = market_psychology.get("confidence", 50)
        
        # Identify opportunities based on patterns
        for pattern in patterns:
            pattern_name = pattern.get("name", "")
            direction = pattern.get("direction", "")
            strength = pattern.get("strength", 0)
            
            if pattern_name == "momentum" and direction == "up" and strength > 60:
                # Momentum-based YES opportunity
                confidence = min(95, 50 + strength // 2)
                
                if sentiment == "bullish":
                    confidence = min(95, confidence + sentiment_confidence // 4)
                elif sentiment == "bearish":
                    confidence = max(5, confidence - sentiment_confidence // 4)
                
                # Adjust for time to close
                if time_to_close < 1:
                    confidence = min(95, confidence + 10)  # More confident near close
                
                opportunities.append({
                    "ticker": ticker,
                    "title": title,
                    "position_type": "yes",
                    "entry_price": yes_ask,
                    "target_price": min(99, yes_ask + 10),
                    "stop_loss": max(1, yes_ask - 5),
                    "confidence": confidence,
                    "expected_return": min(99, int((min(99, yes_ask + 10) - yes_ask) / yes_ask * 100)),
                    "time_sensitivity": "high" if time_to_close < 1 else "medium",
                    "reasoning": f"Strong upward momentum detected with {strength}% strength. " +
                                f"Market sentiment is {sentiment} with {sentiment_confidence}% confidence.",
                    "pattern": pattern_name
                })
            
            elif pattern_name == "momentum" and direction == "down" and strength > 60:
                # Momentum-based NO opportunity
                confidence = min(95, 50 + strength // 2)
                
                if sentiment == "bearish":
                    confidence = min(95, confidence + sentiment_confidence // 4)
                elif sentiment == "bullish":
                    confidence = max(5, confidence - sentiment_confidence // 4)
                
                # Adjust for time to close
                if time_to_close < 1:
                    confidence = min(95, confidence + 10)  # More confident near close
                
                opportunities.append({
                    "ticker": ticker,
                    "title": title,
                    "position_type": "no",
                    "entry_price": no_ask,
                    "target_price": min(99, no_ask + 10),
                    "stop_loss": max(1, no_ask - 5),
                    "confidence": confidence,
                    "expected_return": min(99, int((min(99, no_ask + 10) - no_ask) / no_ask * 100)),
                    "time_sensitivity": "high" if time_to_close < 1 else "medium",
                    "reasoning": f"Strong downward momentum detected with {strength}% strength. " +
                                f"Market sentiment is {sentiment} with {sentiment_confidence}% confidence.",
                    "pattern": pattern_name
                })
            
            elif pattern_name == "mean_reversion" and direction == "up" and strength > 70:
                # Mean reversion YES opportunity
                confidence = min(90, 40 + strength // 2)
                
                if sentiment == "bullish":
                    confidence = min(90, confidence + sentiment_confidence // 5)
                
                opportunities.append({
                    "ticker": ticker,
                    "title": title,
                    "position_type": "yes",
                    "entry_price": yes_ask,
                    "target_price": min(99, yes_ask + 15),
                    "stop_loss": max(1, yes_ask - 7),
                    "confidence": confidence,
                    "expected_return": min(99, int((min(99, yes_ask + 15) - yes_ask) / yes_ask * 100)),
                    "time_sensitivity": "medium",
                    "reasoning": f"Price significantly below historical average, potential upward reversion. " +
                                f"Strength: {strength}%. Market sentiment: {sentiment}.",
                    "pattern": pattern_name
                })
            
            elif pattern_name == "mean_reversion" and direction == "down" and strength > 70:
                # Mean reversion NO opportunity
                confidence = min(90, 40 + strength // 2)
                
                if sentiment == "bearish":
                    confidence = min(90, confidence + sentiment_confidence // 5)
                
                opportunities.append({
                    "ticker": ticker,
                    "title": title,
                    "position_type": "no",
                    "entry_price": no_ask,
                    "target_price": min(99, no_ask + 15),
                    "stop_loss": max(1, no_ask - 7),
                    "confidence": confidence,
                    "expected_return": min(99, int((min(99, no_ask + 15) - no_ask) / no_ask * 100)),
                    "time_sensitivity": "medium",
                    "reasoning": f"Price significantly above historical average, potential downward reversion. " +
                                f"Strength: {strength}%. Market sentiment: {sentiment}.",
                    "pattern": pattern_name
                })
        
        # If no pattern-based opportunities, check for sentiment-based ones
        if not opportunities and sentiment_confidence > 70:
            if sentiment == "bullish":
                opportunities.append({
                    "ticker": ticker,
                    "title": title,
                    "position_type": "yes",
                    "entry_price": yes_ask,
                    "target_price": min(99, yes_ask + 8),
                    "stop_loss": max(1, yes_ask - 4),
                    "confidence": min(85, sentiment_confidence),
                    "expected_return": min(99, int((min(99, yes_ask + 8) - yes_ask) / yes_ask * 100)),
                    "time_sensitivity": "medium",
                    "reasoning": f"Strong bullish market sentiment with {sentiment_confidence}% confidence. " +
                                f"Order book and trade flow indicate buying pressure.",
                    "pattern": "sentiment"
                })
            elif sentiment == "bearish":
                opportunities.append({
                    "ticker": ticker,
                    "title": title,
                    "position_type": "no",
                    "entry_price": no_ask,
                    "target_price": min(99, no_ask + 8),
                    "stop_loss": max(1, no_ask - 4),
                    "confidence": min(85, sentiment_confidence),
                    "expected_return": min(99, int((min(99, no_ask + 8) - no_ask) / no_ask * 100)),
                    "time_sensitivity": "medium",
                    "reasoning": f"Strong bearish market sentiment with {sentiment_confidence}% confidence. " +
                                f"Order book and trade flow indicate selling pressure.",
                    "pattern": "sentiment"
                })
        
        return opportunities
