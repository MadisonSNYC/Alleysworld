"""
KalshiAPIClient for AI Trading Agent

This module provides a client for interacting with the Kalshi API.
It handles authentication, rate limiting, and provides methods for
accessing market data and executing trades.
"""

import logging
import time
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kalshi_api_client')

class KalshiAPIClient:
    """
    Client for interacting with the Kalshi API.
    
    This client handles authentication, rate limiting, and provides
    methods for accessing market data and executing trades.
    """
    
    def __init__(self, email: str, password: str, demo: bool = True):
        """
        Initialize the Kalshi API client.
        
        Args:
            email: Kalshi account email
            password: Kalshi account password
            demo: Whether to use the demo environment (default: True)
        """
        self.email = email
        self.password = password
        self.demo = demo
        
        # Set base URL based on environment
        self.base_url = "https://demo-api.kalshi.co/trade-api/v2" if demo else "https://api.kalshi.co/trade-api/v2"
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        
        # Set rate limiting parameters
        self.rate_limit_delay = 0.2  # 200ms between requests
        self.last_request_time = 0
        
        # Initialize auth token
        self.token = None
        self.token_expiry = None
    
    def login(self) -> bool:
        """
        Log in to Kalshi API and get authentication token.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        logger.info(f"Logging in to Kalshi API as {self.email}")
        
        try:
            # Prepare login payload
            payload = {
                "email": self.email,
                "password": self.password
            }
            
            # Make login request
            response = self._make_request("POST", "/login", json=payload)
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                
                # Set token in session headers
                if self.token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}"
                    })
                    
                    # Set token expiry (24 hours from now)
                    self.token_expiry = datetime.now().timestamp() + 86400
                    
                    logger.info("Login successful")
                    return True
                else:
                    logger.error("Login response did not contain token")
                    return False
            else:
                logger.error(f"Login failed with status code {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Login failed with exception: {str(e)}")
            return False
    
    def get_markets(self, status: str = "active", limit: int = 100, 
                   cursor: str = None, category: str = None) -> Dict:
        """
        Get list of markets.
        
        Args:
            status: Market status (active, settled, etc.)
            limit: Maximum number of markets to return
            cursor: Pagination cursor
            category: Market category filter
            
        Returns:
            Dict: Markets response
        """
        # Build query parameters
        params = {
            "status": status,
            "limit": limit
        }
        
        if cursor:
            params["cursor"] = cursor
            
        if category:
            params["category"] = category
        
        # Make request
        response = self._make_request("GET", "/markets", params=params)
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Get markets failed with status code {response.status_code}: {response.text}")
            return {"markets": []}
    
    def get_market(self, ticker: str) -> Dict:
        """
        Get market details.
        
        Args:
            ticker: Market ticker
            
        Returns:
            Dict: Market details
        """
        # Make request
        response = self._make_request("GET", f"/markets/{ticker}")
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Get market failed with status code {response.status_code}: {response.text}")
            return {}
    
    def get_order_book(self, ticker: str) -> Dict:
        """
        Get market order book.
        
        Args:
            ticker: Market ticker
            
        Returns:
            Dict: Order book
        """
        # Make request
        response = self._make_request("GET", f"/markets/{ticker}/order_book")
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Get order book failed with status code {response.status_code}: {response.text}")
            return {"yes_bids": [], "yes_asks": [], "no_bids": [], "no_asks": []}
    
    def get_market_history(self, ticker: str, limit: int = 100) -> Dict:
        """
        Get market price history.
        
        Args:
            ticker: Market ticker
            limit: Maximum number of history points to return
            
        Returns:
            Dict: Market history
        """
        # Build query parameters
        params = {
            "limit": limit
        }
        
        # Make request
        response = self._make_request("GET", f"/markets/{ticker}/history", params=params)
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Get market history failed with status code {response.status_code}: {response.text}")
            return {"history": []}
    
    def place_order(self, ticker: str, side: str, type: str, 
                   price: int, size: int) -> Dict:
        """
        Place an order.
        
        Args:
            ticker: Market ticker
            side: Order side (buy or sell)
            type: Position type (yes or no)
            price: Order price in cents (1-99)
            size: Order size in contracts
            
        Returns:
            Dict: Order result
        """
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
        
        # Prepare order payload
        payload = {
            "ticker": ticker,
            "side": side,
            "type": type,
            "price": price,
            "size": size,
            "time_in_force": "gtc"  # Good till cancelled
        }
        
        # Make request
        response = self._make_request("POST", "/orders", json=payload)
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Place order failed with status code {response.status_code}: {response.text}")
            return {"status": "error", "message": response.text}
    
    def get_positions(self) -> Dict:
        """
        Get user positions.
        
        Returns:
            Dict: User positions
        """
        # Make request
        response = self._make_request("GET", "/portfolio/positions")
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Get positions failed with status code {response.status_code}: {response.text}")
            return {"positions": []}
    
    def get_orders(self, status: str = "active") -> Dict:
        """
        Get user orders.
        
        Args:
            status: Order status (active, filled, etc.)
            
        Returns:
            Dict: User orders
        """
        # Build query parameters
        params = {
            "status": status
        }
        
        # Make request
        response = self._make_request("GET", "/portfolio/orders", params=params)
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Get orders failed with status code {response.status_code}: {response.text}")
            return {"orders": []}
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Dict: Cancel result
        """
        # Make request
        response = self._make_request("DELETE", f"/orders/{order_id}")
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Cancel order failed with status code {response.status_code}: {response.text}")
            return {"status": "error", "message": response.text}
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Dict = None, json: Dict = None) -> requests.Response:
        """
        Make a request to the Kalshi API with rate limiting.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON payload
            
        Returns:
            requests.Response: Response object
        """
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Build URL
        url = f"{self.base_url}{endpoint}"
        
        # Make request
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json
            )
            
            # Update last request time
            self.last_request_time = time.time()
            
            return response
            
        except Exception as e:
            logger.error(f"Request failed with exception: {str(e)}")
            
            # Create dummy response
            response = requests.Response()
            response.status_code = 500
            response._content = str(e).encode("utf-8")
            
            return response
    
    def _apply_rate_limit(self):
        """Apply rate limiting by waiting if necessary."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
    
    def _check_token_expiry(self):
        """Check if token is expired and refresh if needed."""
        if not self.token or not self.token_expiry:
            return self.login()
            
        if datetime.now().timestamp() >= self.token_expiry:
            return self.login()
            
        return True
