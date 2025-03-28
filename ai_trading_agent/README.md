# Madison's Market Maven AI Trading Agent

## Overview

The AI Trading Agent is the core intelligence component of Madison's Market Maven platform. It analyzes Kalshi prediction markets, generates trade recommendations, and executes trades based on user-defined strategies with a focus on short-term opportunities (typically 1-hour windows) for consistent small gains (5-20%).

## Features

- **Market Analysis**: Continuously monitors Kalshi markets to identify mispriced contracts and trading opportunities
- **Pattern Recognition**: Identifies momentum, mean reversion, and other profitable patterns
- **Market Psychology**: Analyzes order book imbalances and trade flow to gauge market sentiment
- **Confidence Scoring**: Sophisticated system to quantify certainty about trading opportunities
- **Strategy Customization**: Adapts to different trading strategies based on risk tolerance and profit goals
- **Position Sizing**: Intelligent position sizing based on confidence and strategy parameters
- **Execution Modes**: Supports both manual and automatic (YOLO) execution modes

## Architecture

The AI Trading Agent consists of five core components:

1. **Data Collection Module**: Interfaces with Kalshi API to retrieve market data
2. **Analysis Engine**: Processes market data to identify patterns and opportunities
3. **Strategy Processor**: Interprets user-defined strategy parameters
4. **Recommendation Generator**: Creates structured trade recommendations with confidence scores
5. **Execution Manager**: Handles trade execution with psychological insights

## Installation

```bash
# Clone the repository
git clone https://github.com/MadisonSNYC/market-maven-ai-agent.git
cd market-maven-ai-agent

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from ai_trading_agent import AITradingAgent

# Initialize agent with Kalshi credentials
agent = AITradingAgent(email="your_email@example.com", password="your_password")

# Initialize components
if agent.initialize():
    # Add a trading strategy
    strategy = {
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
        "executionMode": "manual"
    }
    
    agent.add_strategy("my_strategy", strategy)
    
    # Get recommendations
    recommendations = agent.get_recommendations("my_strategy")
    
    # Execute a recommendation
    if recommendations:
        result = agent.execute_recommendation(recommendations[0])
        print(f"Execution result: {result['status']}")
```

### Testing with Mock API

For testing without real Kalshi credentials, use the provided mock API client:

```python
from src.mock_kalshi_api_client import MockKalshiAPIClient
from ai_trading_agent import AITradingAgent

# Create a custom agent with mock client
api_client = MockKalshiAPIClient()
agent = AITradingAgent(api_client=api_client)

# Continue as with the real agent
```

## Strategy Configuration

Strategies can be customized with the following parameters:

| Parameter | Description | Example Values |
|-----------|-------------|---------------|
| budget | Total budget for this strategy | 100.00 |
| targetProfit | Target profit percentage | 15 |
| categories | Market categories to focus on | ["crypto", "finance", "sports"] |
| timeHorizon | Time window for opportunities | "1h", "4h", "1d" |
| maxSimultaneousPositions | Maximum number of positions | 3 |
| riskLevel | Risk tolerance (1-10) | 5 (moderate), 8 (aggressive) |
| minConfidence | Minimum confidence threshold | 60 |
| positionSizing | Position sizing parameters | {"maxPerTrade": 20, "scaling": "confidence"} |
| executionMode | Execution mode | "manual" or "yolo" |

## Market Analysis Process

The AI Trading Agent analyzes markets through several stages:

1. **Data Collection**: Gathers market details, order book, price history, and recent trades
2. **Price Pattern Analysis**: Identifies trends, momentum, and mean reversion patterns
3. **Market Psychology Analysis**: Analyzes order book imbalances and trade flow
4. **Opportunity Identification**: Combines technical and psychological factors to identify opportunities
5. **Strategy Application**: Filters opportunities based on user-defined strategy parameters
6. **Recommendation Generation**: Creates actionable trade recommendations with detailed parameters

## Confidence Scoring System

The confidence scoring system quantifies certainty about trading opportunities:

- **Base Confidence**: Derived from pattern strength
- **Market Psychology Adjustments**: Based on sentiment alignment
- **Time-Based Adjustments**: Higher confidence near market close
- **Order Book Analysis**: Imbalances affect confidence
- **Trade Flow Analysis**: Recent trading activity influences confidence
- **Volatility Adjustment**: Higher volatility reduces confidence

## Example Trading Strategies

### Conservative Strategy

```python
conservative_strategy = {
    "budget": 100.00,
    "targetProfit": 10,
    "categories": ["finance"],
    "timeHorizon": "1h",
    "maxSimultaneousPositions": 2,
    "riskLevel": 3,
    "minConfidence": 80,
    "positionSizing": {
        "maxPerTrade": 20,
        "scaling": "fixed"
    },
    "executionMode": "manual"
}
```

### Aggressive Strategy

```python
aggressive_strategy = {
    "budget": 200.00,
    "targetProfit": 25,
    "categories": ["crypto", "sports"],
    "timeHorizon": "2h",
    "maxSimultaneousPositions": 5,
    "riskLevel": 8,
    "minConfidence": 60,
    "positionSizing": {
        "maxPerTrade": 50,
        "scaling": "confidence"
    },
    "executionMode": "yolo"
}
```

## Case Studies

### Case 1: Momentum Trading
- Market: "Bitcoin price between $83,750-$83,999.99 at 12pm EDT"
- Strategy: Enter early (11:05am) when confidence is high
- Position: Buy YES on $83,750-83,999.99 range at 33¢
- Exit: Sell when price reaches 48-50¢
- Stop Loss: Sell if price drops to 22¢

### Case 2: Multi-Market Hedging
- Markets: Related USD/JPY price ranges
- Strategy: Take opposite positions in adjacent ranges
- Position 1: Buy YES on 143.000 or above at 65¢
- Position 2: Buy YES on 148.999 or below at 72¢
- Exit: Hold until near expiration if both remain profitable

### Case 3: Event-Based Momentum Trading
- Market: "Nasdaq price today at 10am EDT"
- Strategy: Enter position based on pre-market momentum
- Position: Buy YES on 19,800 or above at 7¢
- Confidence: 68% based on overnight futures and Asian market performance
- Exit: Take profit at 15¢ or hold until expiration if momentum continues

## Success Metrics

The AI Trading Agent's performance is measured by:

1. **Win Rate**: Percentage of trades that achieve profit targets
2. **Average Return**: Mean percentage return across all trades
3. **Risk-Adjusted Return**: Return relative to maximum drawdown
4. **Execution Accuracy**: Percentage of trades executed at or better than recommended prices
5. **Strategy Alignment**: How well trade selections align with specified strategies
6. **Confidence Score Accuracy**: Correlation between confidence scores and trade outcomes

## Integration with Madison's Market Maven

To integrate with the Madison's Market Maven platform:

1. Import the AITradingAgent class in your backend code
2. Initialize it with Kalshi credentials
3. Set up strategies based on user preferences
4. Call get_recommendations() to generate trade recommendations
5. Display recommendations in the UI
6. Handle trade execution based on user actions

## License

Proprietary - All rights reserved by Madison's Market Maven.

## Contact

For support or inquiries, contact support@madisonsmarketmaven.com
