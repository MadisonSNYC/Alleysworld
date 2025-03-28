"""
Mock Kalshi API Client for testing

This module provides a mock client for testing the AI Trading Agent
without requiring actual Kalshi API credentials.
"""

import logging
import time
import json
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mock_kalshi_api_client')

class MockKalshiAPIClient:
    """
    Mock client for testing the AI Trading Agent without requiring
    actual Kalshi API credentials.
    """
    
    def __init__(self, email: str = "test@example.com", password: str = "password", demo: bool = True):
        """
        Initialize the Mock Kalshi API client.
        
        Args:
            email: Dummy email (not used)
            password: Dummy password (not used)
            demo: Dummy parameter (not used)
        """
        self.email = email
        self.password = password
        
        # Initialize mock data
        self._initialize_mock_data()
        
        logger.info("Mock Kalshi API client initialized")
    
    def _initialize_mock_data(self):
        """Initialize mock data for testing."""
        # Create mock markets
        self.markets = [
            {
                "ticker": "BTC-83750-83999-12PM",
                "title": "Bitcoin price between $83,750-$83,999.99 at 12pm EDT",
                "category": "crypto",
                "status": "active",
                "close_time": (datetime.now() + timedelta(hours=1)).isoformat() + "Z",
                "yes_bid": 33,
                "yes_ask": 35,
                "no_bid": 65,
                "no_ask": 67,
                "volume": 10000,
                "yes_volume": 6000,
                "no_volume": 4000
            },
            {
                "ticker": "USD-JPY-143-ABOVE-10AM",
                "title": "USD/JPY price 143.000 or above at 10am EDT",
                "category": "finance",
                "status": "active",
                "close_time": (datetime.now() + timedelta(minutes=30)).isoformat() + "Z",
                "yes_bid": 65,
                "yes_ask": 67,
                "no_bid": 33,
                "no_ask": 35,
                "volume": 8000,
                "yes_volume": 5000,
                "no_volume": 3000
            },
            {
                "ticker": "USD-JPY-148-BELOW-10AM",
                "title": "USD/JPY price 148.999 or below at 10am EDT",
                "category": "finance",
                "status": "active",
                "close_time": (datetime.now() + timedelta(minutes=30)).isoformat() + "Z",
                "yes_bid": 72,
                "yes_ask": 74,
                "no_bid": 26,
                "no_ask": 28,
                "volume": 7500,
                "yes_volume": 5500,
                "no_volume": 2000
            },
            {
                "ticker": "NASDAQ-19800-ABOVE-10AM",
                "title": "Nasdaq price 19,800 or above at 10am EDT",
                "category": "finance",
                "status": "active",
                "close_time": (datetime.now() + timedelta(minutes=45)).isoformat() + "Z",
                "yes_bid": 7,
                "yes_ask": 9,
                "no_bid": 91,
                "no_ask": 93,
                "volume": 12000,
                "yes_volume": 2000,
                "no_volume": 10000
            },
            {
                "ticker": "EUR-USD-1.058-ABOVE-10AM",
                "title": "EUR/USD price 1.05800 or above at 10am EDT",
                "category": "finance",
                "status": "active",
                "close_time": (datetime.now() + timedelta(minutes=55)).isoformat() + "Z",
                "yes_bid": 61,
                "yes_ask": 63,
                "no_bid": 37,
                "no_ask": 39,
                "volume": 9000,
                "yes_volume": 6000,
                "no_volume": 3000
            }
        ]
        
        # Create mock order books
        self.order_books = {}
        for market in self.markets:
            ticker = market["ticker"]
            yes_bid = market["yes_bid"]
            yes_ask = market["yes_ask"]
            no_bid = market["no_bid"]
            no_ask = market["no_ask"]
            
            self.order_books[ticker] = {
                "yes_bids": [
                    {"price": yes_bid, "size": 500},
                    {"price": yes_bid - 1, "size": 700},
                    {"price": yes_bid - 2, "size": 900}
                ],
                "yes_asks": [
                    {"price": yes_ask, "size": 300},
                    {"price": yes_ask + 1, "size": 400},
                    {"price": yes_ask + 2, "size": 500}
                ],
                "no_bids": [
                    {"price": no_bid, "size": 400},
                    {"price": no_bid - 1, "size": 600},
                    {"price": no_bid - 2, "size": 800}
                ],
                "no_asks": [
                    {"price": no_ask, "size": 200},
                    {"price": no_ask + 1, "size": 300},
                    {"price": no_ask + 2, "size": 400}
                ]
            }
        
        # Create mock market histories
        self.market_histories = {}
        for market in self.markets:
            ticker = market["ticker"]
            yes_bid = market["yes_bid"]
            
            # Create price points over the last 24 hours
            history = []
            for i in range(24):
                time_point = datetime.now() - timedelta(hours=24-i)
                # Add some random variation to price
                price = max(1, min(99, yes_bid + random.randint(-5, 5)))
                
                history.append({
                    "time": time_point.isoformat() + "Z",
                    "yes_price": price,
                    "no_price": 100 - price,
                    "volume": random.randint(100, 1000)
                })
            
            self.market_histories[ticker] = {"history": history}
        
        # Create mock trades
        self.trades = {}
        for market in self.markets:
            ticker = market["ticker"]
            yes_bid = market["yes_bid"]
            
            # Create recent trades
            recent_trades = []
            for i in range(20):
                time_point = datetime.now() - timedelta(minutes=random.randint(1, 60))
                # Add some random variation to price
                price = max(1, min(99, yes_bid + random.randint(-3, 3)))
                
                recent_trades.append({
                    "trade_id": f"trade-{ticker}-{i}",
                    "ticker": ticker,
                    "time": time_point.isoformat() + "Z",
                    "price": price,
                    "count": random.randint(10, 100),
                    "side": "buy" if random.random() > 0.5 else "sell",
                    "type": "yes" if random.random() > 0.5 else "no"
                })
            
            # Sort by time (most recent first)
            recent_trades.sort(key=lambda x: x["time"], reverse=True)
            self.trades[ticker] = {"trades": recent_trades}
        
        # Initialize mock orders and positions
        self.orders = []
        self.positions = []
        self.next_order_id = 1000
    
    def login(self) -> bool:
        """
        Mock login function.
        
        Returns:
            bool: Always returns True
        """
        logger.info(f"Mock login successful for {self.email}")
        return True
    
    def get_markets(self, status: str = "active", limit: int = 100, 
                   cursor: str = None, category: str = None) -> Dict:
        """
        Get mock list of markets.
        
        Args:
            status: Market status filter (not used in mock)
            limit: Maximum number of markets to return
            cursor: Pagination cursor (not used in mock)
            category: Market category filter
            
        Returns:
            Dict: Markets response
        """
        logger.info(f"Getting mock markets with category={category}")
        
        # Filter by category if specified
        if category:
            filtered_markets = [
                market for market in self.markets
                if market.get("category") == category
            ]
        else:
            filtered_markets = self.markets
        
        # Limit results
        limited_markets = filtered_markets[:limit]
        
        return {"markets": limited_markets}
    
    def get_market(self, ticker: str) -> Dict:
        """
        Get mock market details.
        
        Args:
            ticker: Market ticker
            
        Returns:
            Dict: Market details
        """
        logger.info(f"Getting mock market details for {ticker}")
        
        # Find market by ticker
        for market in self.markets:
            if market["ticker"] == ticker:
                return {"market": market}
        
        return {"market": {}}
    
    def get_market_details(self, ticker: str) -> Dict:
        """
        Get mock market details (alias for get_market).
        
        Args:
            ticker: Market ticker
            
        Returns:
            Dict: Market details
        """
        logger.info(f"Getting mock market details for {ticker}")
        
        # Find market by ticker
        for market in self.markets:
            if market["ticker"] == ticker:
                return market
        
        return {}
    
    def get_order_book(self, ticker: str) -> Dict:
        """
        Get mock market order book.
        
        Args:
            ticker: Market ticker
            
        Returns:
            Dict: Order book
        """
        logger.info(f"Getting mock order book for {ticker}")
        
        # Return order book if exists
        if ticker in self.order_books:
            return self.order_books[ticker]
        
        # Return empty order book
        return {"yes_bids": [], "yes_asks": [], "no_bids": [], "no_asks": []}
    
    def get_market_history(self, ticker: str, limit: int = 100) -> Dict:
        """
        Get mock market price history.
        
        Args:
            ticker: Market ticker
            limit: Maximum number of history points to return
            
        Returns:
            Dict: Market history
        """
        logger.info(f"Getting mock market history for {ticker}")
        
        # Return history if exists
        if ticker in self.market_histories:
            history = self.market_histories[ticker]
            # Limit history points
            history["history"] = history["history"][-limit:]
            return history
        
        # Return empty history
        return {"history": []}
    
    def get_trades(self, ticker: str, limit: int = 20) -> Dict:
        """
        Get mock recent trades for a market.
        
        Args:
            ticker: Market ticker
            limit: Maximum number of trades to return
            
        Returns:
            Dict: Recent trades
        """
        logger.info(f"Getting mock trades for {ticker}")
        
        # Return trades if exists
        if ticker in self.trades:
            trades = self.trades[ticker]
            # Limit trades
            trades["trades"] = trades["trades"][:limit]
            return trades
        
        # Return empty trades
        return {"trades": []}
    
    def place_order(self, ticker: str, side: str, type: str, 
                   price: int, size: int) -> Dict:
        """
        Place a mock order.
        
        Args:
            ticker: Market ticker
            side: Order side (buy or sell)
            type: Position type (yes or no)
            price: Order price in cents (1-99)
            size: Order size in contracts
            
        Returns:
            Dict: Order result
        """
        logger.info(f"Placing mock {side} {type} order for {ticker}: {size} contracts at {price}¢")
        
        # Validate parameters
        if side not in ["buy", "sell"]:
            logger.error(f"Invalid order side: {side}")
            return {"status": "error", "message": "Invalid order side"}
            
        if type not in ["yes", "no"]:
            logger.error(f"Invalid position type: {type}")
            return {"status": "error", "message": "Invalid position type"}
            
        if not 1 <= price <= 99:
            logger.error(f"Invalid price: {price}")
            return {"status": "error", "message": "Invalid price"}
            
        if size <= 0:
            logger.error(f"Invalid size: {size}")
            return {"status": "error", "message": "Invalid size"}
        
        # Create mock order
        order_id = f"order-{self.next_order_id}"
        self.next_order_id += 1
        
        order = {
            "order_id": order_id,
            "ticker": ticker,
            "side": side,
            "type": type,
            "price": price,
            "size": size,
            "status": "filled",  # Assume order is filled immediately for testing
            "created_time": datetime.now().isoformat() + "Z"
        }
        
        # Add to orders
        self.orders.append(order)
        
        # Create position if buy order
        if side == "buy":
            position = {
                "position_id": f"position-{order_id}",
                "ticker": ticker,
                "type": type,
                "count": size,
                "price": price,
                "created_time": datetime.now().isoformat() + "Z"
            }
            
            self.positions.append(position)
        
        return {
            "status": "success",
            "order_id": order_id,
            "message": "Order filled successfully"
        }
    
    def get_positions(self) -> Dict:
        """
        Get mock user positions.
        
        Returns:
            Dict: User positions
        """
        logger.info("Getting mock positions")
        return {"positions": self.positions}
    
    def get_orders(self, status: str = "active") -> Dict:
        """
        Get mock user orders.
        
        Args:
            status: Order status filter (not used in mock)
            
        Returns:
            Dict: User orders
        """
        logger.info(f"Getting mock orders with status={status}")
        return {"orders": self.orders}
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel a mock order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Dict: Cancel result
        """
        logger.info(f"Cancelling mock order {order_id}")
        
        # Find order by ID
        for order in self.orders:
            if order["order_id"] == order_id:
                order["status"] = "cancelled"
                return {
                    "status": "success",
                    "message": "Order cancelled successfully"
                }
        
        return {
            "status": "error",
            "message": "Order not found"
        }
