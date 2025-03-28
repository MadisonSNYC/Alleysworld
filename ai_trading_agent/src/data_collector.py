"""
Data Collection Module for AI Trading Agent

This module interfaces with the Kalshi API to retrieve market data, monitor open markets,
track price movements, and collect order book data for analysis.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_collector')

class KalshiAPIClient:
    """Client for interacting with the Kalshi API."""
    
    BASE_URL = "https://trading-api.kalshi.com/v1"
    
    def __init__(self, email: str, password: str):
        """
        Initialize the Kalshi API client.
        
        Args:
            email: User email for Kalshi account
            password: User password for Kalshi account
        """
        self.email = email
        self.password = password
        self.token = None
        self.user_id = None
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 0.2  # 200ms between requests to avoid rate limiting
    
    def _rate_limit(self):
        """Implement rate limiting to avoid API throttling."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def login(self) -> bool:
        """
        Log in to Kalshi API and get authentication token.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        self._rate_limit()
        
        login_url = f"{self.BASE_URL}/login"
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        try:
            response = self.session.post(login_url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get('token')
            self.user_id = data.get('member_id')
            
            if self.token:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                logger.info(f"Successfully logged in as user {self.user_id}")
                return True
            else:
                logger.error("Login failed: No token received")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def get_markets(self, status: str = "open", limit: int = 100, 
                   cursor: str = None, series_ticker: str = None,
                   event_ticker: str = None, category: str = None) -> Dict:
        """
        Get markets from Kalshi API with various filters.
        
        Args:
            status: Market status (open, closed, settled)
            limit: Maximum number of markets to return
            cursor: Pagination cursor
            series_ticker: Filter by series ticker
            event_ticker: Filter by event ticker
            category: Filter by category
            
        Returns:
            Dict containing markets data
        """
        self._rate_limit()
        
        markets_url = f"{self.BASE_URL}/markets"
        params = {
            "status": status,
            "limit": limit
        }
        
        if cursor:
            params["cursor"] = cursor
        if series_ticker:
            params["series_ticker"] = series_ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if category:
            params["category"] = category
            
        try:
            response = self.session.get(markets_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get markets: {str(e)}")
            return {"markets": [], "cursor": None}
    
    def get_market_details(self, ticker: str) -> Dict:
        """
        Get detailed information about a specific market.
        
        Args:
            ticker: Market ticker symbol
            
        Returns:
            Dict containing market details
        """
        self._rate_limit()
        
        market_url = f"{self.BASE_URL}/markets/{ticker}"
        
        try:
            response = self.session.get(market_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get market details for {ticker}: {str(e)}")
            return {}
    
    def get_order_book(self, ticker: str) -> Dict:
        """
        Get order book for a specific market.
        
        Args:
            ticker: Market ticker symbol
            
        Returns:
            Dict containing order book data
        """
        self._rate_limit()
        
        order_book_url = f"{self.BASE_URL}/markets/{ticker}/order_book"
        
        try:
            response = self.session.get(order_book_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get order book for {ticker}: {str(e)}")
            return {"yes_bids": [], "yes_asks": [], "no_bids": [], "no_asks": []}
    
    def get_market_history(self, ticker: str, limit: int = 100) -> Dict:
        """
        Get price history for a specific market.
        
        Args:
            ticker: Market ticker symbol
            limit: Maximum number of history points to return
            
        Returns:
            Dict containing market history data
        """
        self._rate_limit()
        
        history_url = f"{self.BASE_URL}/markets/{ticker}/history"
        params = {"limit": limit}
        
        try:
            response = self.session.get(history_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get market history for {ticker}: {str(e)}")
            return {"history": []}
    
    def get_trades(self, ticker: str, limit: int = 100) -> Dict:
        """
        Get recent trades for a specific market.
        
        Args:
            ticker: Market ticker symbol
            limit: Maximum number of trades to return
            
        Returns:
            Dict containing trades data
        """
        self._rate_limit()
        
        trades_url = f"{self.BASE_URL}/markets/{ticker}/trades"
        params = {"limit": limit}
        
        try:
            response = self.session.get(trades_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get trades for {ticker}: {str(e)}")
            return {"trades": []}


class DataCollector:
    """
    Collects and processes market data from Kalshi API.
    Monitors open markets, tracks price movements, and collects order book data.
    """
    
    def __init__(self, api_client: KalshiAPIClient):
        """
        Initialize the DataCollector.
        
        Args:
            api_client: Authenticated Kalshi API client
        """
        self.api_client = api_client
        self.markets_cache = {}
        self.order_books_cache = {}
        self.market_history_cache = {}
        self.last_update_time = {}
        self.update_interval = 60  # Default update interval in seconds
    
    def set_update_interval(self, seconds: int):
        """
        Set the update interval for market data.
        
        Args:
            seconds: Update interval in seconds
        """
        self.update_interval = seconds
        logger.info(f"Update interval set to {seconds} seconds")
    
    def get_markets_by_category(self, category: str, force_refresh: bool = False) -> List[Dict]:
        """
        Get markets filtered by category.
        
        Args:
            category: Market category (e.g., 'crypto', 'sports')
            force_refresh: Force refresh of cached data
            
        Returns:
            List of market dictionaries
        """
        cache_key = f"category_{category}"
        current_time = time.time()
        
        # Check if we need to refresh the cache
        if (force_refresh or 
            cache_key not in self.last_update_time or 
            current_time - self.last_update_time.get(cache_key, 0) > self.update_interval):
            
            logger.info(f"Fetching markets for category: {category}")
            result = self.api_client.get_markets(status="open", category=category)
            markets = result.get("markets", [])
            
            self.markets_cache[cache_key] = markets
            self.last_update_time[cache_key] = current_time
            
            # Also cache individual markets
            for market in markets:
                market_ticker = market.get("ticker")
                if market_ticker:
                    self.markets_cache[market_ticker] = market
                    self.last_update_time[market_ticker] = current_time
            
            return markets
        
        return self.markets_cache.get(cache_key, [])
    
    def get_markets_by_time_horizon(self, hours: int, force_refresh: bool = False) -> List[Dict]:
        """
        Get markets filtered by time horizon (expiration within specified hours).
        
        Args:
            hours: Number of hours from now
            force_refresh: Force refresh of cached data
            
        Returns:
            List of market dictionaries
        """
        cache_key = f"horizon_{hours}"
        current_time = time.time()
        
        # Check if we need to refresh the cache
        if (force_refresh or 
            cache_key not in self.last_update_time or 
            current_time - self.last_update_time.get(cache_key, 0) > self.update_interval):
            
            logger.info(f"Fetching markets with time horizon: {hours} hours")
            result = self.api_client.get_markets(status="open")
            markets = result.get("markets", [])
            
            # Filter markets by expiration time
            cutoff_time = datetime.now() + timedelta(hours=hours)
            filtered_markets = []
            
            for market in markets:
                close_time_str = market.get("close_time")
                if close_time_str:
                    close_time = datetime.fromisoformat(close_time_str.replace('Z', '+00:00'))
                    if close_time <= cutoff_time:
                        filtered_markets.append(market)
            
            self.markets_cache[cache_key] = filtered_markets
            self.last_update_time[cache_key] = current_time
            
            return filtered_markets
        
        return self.markets_cache.get(cache_key, [])
    
    def get_market_details(self, ticker: str, force_refresh: bool = False) -> Dict:
        """
        Get detailed information about a specific market.
        
        Args:
            ticker: Market ticker symbol
            force_refresh: Force refresh of cached data
            
        Returns:
            Dict containing market details
        """
        current_time = time.time()
        
        # Check if we need to refresh the cache
        if (force_refresh or 
            ticker not in self.markets_cache or 
            current_time - self.last_update_time.get(ticker, 0) > self.update_interval):
            
            logger.info(f"Fetching details for market: {ticker}")
            market_details = self.api_client.get_market_details(ticker)
            
            if market_details:
                self.markets_cache[ticker] = market_details
                self.last_update_time[ticker] = current_time
            
            return market_details
        
        return self.markets_cache.get(ticker, {})
    
    def get_order_book(self, ticker: str, force_refresh: bool = False) -> Dict:
        """
        Get order book for a specific market.
        
        Args:
            ticker: Market ticker symbol
            force_refresh: Force refresh of cached data
            
        Returns:
            Dict containing order book data
        """
        cache_key = f"order_book_{ticker}"
        current_time = time.time()
        
        # Check if we need to refresh the cache
        if (force_refresh or 
            cache_key not in self.order_books_cache or 
            current_time - self.last_update_time.get(cache_key, 0) > self.update_interval):
            
            logger.info(f"Fetching order book for market: {ticker}")
            order_book = self.api_client.get_order_book(ticker)
            
            self.order_books_cache[cache_key] = order_book
            self.last_update_time[cache_key] = current_time
            
            return order_book
        
        return self.order_books_cache.get(cache_key, {})
    
    def get_market_history(self, ticker: str, force_refresh: bool = False) -> List[Dict]:
        """
        Get price history for a specific market.
        
        Args:
            ticker: Market ticker symbol
            force_refresh: Force refresh of cached data
            
        Returns:
            List of history data points
        """
        cache_key = f"history_{ticker}"
        current_time = time.time()
        
        # Check if we need to refresh the cache
        if (force_refresh or 
            cache_key not in self.market_history_cache or 
            current_time - self.last_update_time.get(cache_key, 0) > self.update_interval):
            
            logger.info(f"Fetching history for market: {ticker}")
            result = self.api_client.get_market_history(ticker)
            history = result.get("history", [])
            
            self.market_history_cache[cache_key] = history
            self.last_update_time[cache_key] = current_time
            
            return history
        
        return self.market_history_cache.get(cache_key, [])
    
    def get_recent_trades(self, ticker: str) -> List[Dict]:
        """
        Get recent trades for a specific market.
        
        Args:
            ticker: Market ticker symbol
            
        Returns:
            List of recent trades
        """
        logger.info(f"Fetching recent trades for market: {ticker}")
        result = self.api_client.get_trades(ticker)
        return result.get("trades", [])
    
    def get_markets_by_criteria(self, categories: List[str] = None, 
                               time_horizon: int = None, 
                               min_volume: float = None) -> List[Dict]:
        """
        Get markets filtered by multiple criteria.
        
        Args:
            categories: List of market categories
            time_horizon: Time horizon in hours
            min_volume: Minimum trading volume
            
        Returns:
            List of market dictionaries
        """
        markets = []
        
        # Get markets by categories
        if categories:
            for category in categories:
                category_markets = self.get_markets_by_category(category)
                markets.extend(category_markets)
        else:
            # Get all open markets if no categories specified
            result = self.api_client.get_markets(status="open")
            markets = result.get("markets", [])
        
        # Filter by time horizon if specified
        if time_horizon is not None:
            cutoff_time = datetime.now() + timedelta(hours=time_horizon)
            markets = [
                market for market in markets 
                if datetime.fromisoformat(market.get("close_time", "").replace('Z', '+00:00')) <= cutoff_time
            ]
        
        # Filter by minimum volume if specified
        if min_volume is not None:
            markets = [
                market for market in markets 
                if float(market.get("volume", 0)) >= min_volume
            ]
        
        return markets
    
    def get_market_data_bundle(self, ticker: str) -> Dict:
        """
        Get comprehensive data bundle for a specific market.
        
        Args:
            ticker: Market ticker symbol
            
        Returns:
            Dict containing all relevant market data
        """
        logger.info(f"Collecting comprehensive data for market: {ticker}")
        
        # Get market details
        market_details = self.get_market_details(ticker, force_refresh=True)
        
        # Get order book
        order_book = self.get_order_book(ticker, force_refresh=True)
        
        # Get price history
        history = self.get_market_history(ticker, force_refresh=True)
        
        # Get recent trades
        trades = self.get_recent_trades(ticker)
        
        # Bundle all data
        data_bundle = {
            "market_details": market_details,
            "order_book": order_book,
            "price_history": history,
            "recent_trades": trades,
            "timestamp": datetime.now().isoformat()
        }
        
        return data_bundle
    
    def monitor_markets(self, tickers: List[str], interval: int = 60, callback=None):
        """
        Continuously monitor specified markets at regular intervals.
        
        Args:
            tickers: List of market ticker symbols to monitor
            interval: Monitoring interval in seconds
            callback: Function to call with updated market data
        """
        logger.info(f"Starting market monitoring for {len(tickers)} markets")
        
        try:
            while True:
                for ticker in tickers:
                    data_bundle = self.get_market_data_bundle(ticker)
                    
                    if callback:
                        callback(ticker, data_bundle)
                    
                    # Small delay between markets to avoid API rate limiting
                    time.sleep(0.5)
                
                logger.info(f"Completed monitoring cycle, sleeping for {interval} seconds")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Market monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in market monitoring: {str(e)}")


# Example usage
if __name__ == "__main__":
    # This is just for demonstration, replace with actual credentials
    api_client = KalshiAPIClient(email="example@example.com", password="password")
    
    # Login to Kalshi API
    if api_client.login():
        # Create data collector
        collector = DataCollector(api_client)
        
        # Get crypto markets
        crypto_markets = collector.get_markets_by_category("crypto")
        print(f"Found {len(crypto_markets)} crypto markets")
        
        # Get markets expiring within 1 hour
        short_term_markets = collector.get_markets_by_time_horizon(1)
        print(f"Found {len(short_term_markets)} markets expiring within 1 hour")
        
        # Get data for a specific market
        if short_term_markets:
            sample_ticker = short_term_markets[0]["ticker"]
            data_bundle = collector.get_market_data_bundle(sample_ticker)
            print(f"Collected data bundle for {sample_ticker}")
            
            # Example of monitoring callback
            def print_market_update(ticker, data):
                print(f"Market update for {ticker}: Current price = {data['market_details'].get('yes_bid', 'N/A')}")
            
            # Monitor a few markets (commented out to avoid running indefinitely)
            # collector.monitor_markets([market["ticker"] for market in short_term_markets[:3]], 
            #                          interval=30, callback=print_market_update)
    else:
        print("Failed to login to Kalshi API")
