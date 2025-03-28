# AI Trading Agent Architecture

## Overview

The AI Trading Agent is designed to analyze Kalshi prediction markets, generate trade recommendations, and execute trades based on user-defined strategies. The agent focuses on short-term opportunities (typically 1-hour windows) for consistent small gains (5-20%).

## Core Components

### 1. Data Collection Module
- Interfaces with Kalshi API to retrieve market data
- Monitors open markets and tracks price movements
- Collects order book data to analyze market depth
- Retrieves historical data for pattern analysis
- Monitors external data sources for relevant information

### 2. Analysis Engine
- Processes market data to identify patterns and opportunities
- Analyzes market psychology and betting patterns
- Identifies mispriced contracts based on available data
- Calculates probabilities and expected values
- Performs technical analysis on price movements

### 3. Strategy Processor
- Interprets user-defined strategy parameters
- Applies strategy constraints to identified opportunities
- Prioritizes opportunities based on strategy goals
- Adapts strategy application based on market conditions
- Manages multiple simultaneous strategies

### 4. Recommendation Generator
- Creates structured trade recommendations
- Calculates confidence scores based on multiple factors
- Determines optimal position sizes based on risk parameters
- Prioritizes recommendations based on confidence and potential return
- Provides detailed reasoning for each recommendation

### 5. Execution Manager
- Supports both manual approval and automatic (YOLO) execution modes
- Places orders on Kalshi with appropriate parameters
- Monitors open positions for exit criteria
- Executes exit orders when criteria are met
- Tracks executed trades and outcomes for performance analysis

## Data Flow

1. User provides strategy parameters
2. Data Collection Module retrieves available markets from Kalshi
3. Analysis Engine processes market data to identify opportunities
4. Strategy Processor filters opportunities based on strategy parameters
5. Recommendation Generator creates specific trade recommendations
6. Based on execution mode:
   - Manual: Recommendations presented to user for approval
   - YOLO: Execution Manager automatically places orders
7. Execution Manager monitors positions and implements exit strategies
8. Performance data is recorded for all trades

## Confidence Scoring System

The agent calculates confidence scores (0-100%) for each recommendation based on:

- **Price Analysis** (25%):
  - Current price relative to historical range
  - Recent price momentum
  - Price stability/volatility

- **Market Psychology** (25%):
  - Betting patterns and volume
  - Order book imbalances
  - Sentiment indicators

- **Time Factors** (20%):
  - Remaining time until contract expiration
  - Historical price movement patterns at similar timeframes
  - Timing relative to external events

- **Technical Indicators** (15%):
  - Pattern recognition
  - Support/resistance levels
  - Volume analysis

- **External Data** (15%):
  - Related market movements
  - News and event analysis
  - Social sentiment indicators

## Strategy Parameters

The agent accepts the following strategy parameters:

```javascript
{
  "budget": 100.00,           // Total amount to invest (USD)
  "targetProfit": 15,         // Target percentage gain
  "categories": ["crypto", "sports"], // Market categories to focus on
  "timeHorizon": "1h",        // Time horizon for trades
  "maxSimultaneousPositions": 5,  // Maximum number of concurrent trades
  "riskLevel": 6,             // Risk tolerance (1-10)
  "minConfidence": 65,        // Minimum confidence score for recommendations
  "positionSizing": {
    "maxPerTrade": 20,        // Maximum percentage of budget per trade
    "scaling": "confidence"   // Scale position size by confidence
  },
  "executionMode": "yolo"     // "manual" or "yolo"
}
```

## Trade Recommendation Format

```javascript
{
  "asset": "BTC-83750-83999-12PM",  // Kalshi market ticker
  "position": "YES",                // YES or NO position
  "currentPrice": 33,               // Current price in cents
  "entryPrice": 33,                 // Recommended entry price in cents
  "contracts": 7,                   // Number of contracts to purchase
  "cost": 2.31,                     // Total cost in USD
  "targetExit": "48-50",            // Target exit price range in cents
  "stopLoss": 22,                   // Stop loss price in cents
  "confidence": 82,                 // Confidence score (0-100)
  "expectedReturn": 45.5,           // Expected percentage return
  "timeWindow": "11:00-12:00 EDT",  // Trading window
  "reasoning": "BTC showing strong upward momentum in the last 30 minutes with support at $83,700. Order book shows thin resistance up to $84,000, increasing probability of YES outcome. 7:3 YES:NO volume ratio in last 15 minutes suggests positive sentiment."
}
```

## Implementation Considerations

### Performance Requirements
- Process market updates within 1 second
- Generate recommendations within 3 seconds of identifying an opportunity
- Execute trades within 1 second of approval/decision
- Monitor positions with ≤2 second update frequency

### Risk Management
- Implement maximum loss thresholds per trade and overall
- Apply strict position sizing rules based on confidence
- Set clear exit criteria for all positions
- Implement circuit breakers for unusual market conditions

### Learning Capability
- Record all trades and outcomes for performance analysis
- Identify patterns in successful and unsuccessful trades
- Adjust confidence scoring based on historical performance
- Refine strategy implementation based on results
