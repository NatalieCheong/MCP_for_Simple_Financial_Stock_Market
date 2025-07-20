import yfinance as yf
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from mcp.server.fastmcp import FastMCP
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FINANCE_DIR = "financial_data"

# Initialize FastMCP server
mcp = FastMCP("finance")

@mcp.tool()
def get_stock_info(symbol: str) -> str:
    """
    Get basic information about a stock including current price, market cap, and key metrics.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA')
        
    Returns:
        JSON string with stock information
    """
    try:
        stock = yf.Ticker(symbol.upper())
        info = stock.info
        
        # Extract key information
        stock_data = {
            'symbol': symbol.upper(),
            'name': info.get('longName', 'N/A'),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
            'previous_close': info.get('previousClose', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'volume': info.get('volume', 'N/A'),
            'average_volume': info.get('averageVolume', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'retrieved_at': datetime.now().isoformat()
        }
        
        # Save to file
        os.makedirs(FINANCE_DIR, exist_ok=True)
        filename = os.path.join(FINANCE_DIR, f"{symbol.upper()}_info.json")
        with open(filename, 'w') as f:
            json.dump(stock_data, f, indent=2)
        
        logger.info(f"Stock info for {symbol} saved to {filename}")
        return json.dumps(stock_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error fetching stock info for {symbol}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@mcp.tool()
def get_historical_data(symbol: str, period: str = "1mo", interval: str = "1d") -> str:
    """
    Get historical stock price data for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA')
        period: Time period - valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        interval: Data interval - valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        
    Returns:
        JSON string with historical price data
    """
    try:
        stock = yf.Ticker(symbol.upper())
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            return json.dumps({"error": f"No data found for symbol {symbol}"})
        
        # Convert to JSON-serializable format
        hist_data = {
            'symbol': symbol.upper(),
            'period': period,
            'interval': interval,
            'data': []
        }
        
        for date, row in hist.iterrows():
            hist_data['data'].append({
                'date': date.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0
            })
        
        # Save to file
        os.makedirs(FINANCE_DIR, exist_ok=True)
        filename = os.path.join(FINANCE_DIR, f"{symbol.upper()}_historical_{period}_{interval}.json")
        with open(filename, 'w') as f:
            json.dump(hist_data, f, indent=2)
        
        logger.info(f"Historical data for {symbol} saved to {filename}")
        return json.dumps(hist_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error fetching historical data for {symbol}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@mcp.tool()
def compare_stocks(symbols: List[str], metric: str = "current_price") -> str:
    """
    Compare multiple stocks based on a specific metric.
    
    Args:
        symbols: List of stock ticker symbols to compare
        metric: Metric to compare (current_price, market_cap, pe_ratio, volume)
        
    Returns:
        JSON string with comparison data
    """
    try:
        comparison_data = {
            'metric': metric,
            'comparison_date': datetime.now().isoformat(),
            'stocks': []
        }
        
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol.upper())
                info = stock.info
                
                stock_metric = {
                    'symbol': symbol.upper(),
                    'name': info.get('longName', 'N/A'),
                    'metric_value': info.get(metric, 'N/A')
                }
                
                # Add additional context based on metric
                if metric == 'current_price':
                    stock_metric['currency'] = info.get('currency', 'USD')
                elif metric == 'market_cap':
                    stock_metric['currency'] = info.get('currency', 'USD')
                elif metric == 'pe_ratio':
                    stock_metric['description'] = 'Price-to-Earnings Ratio'
                
                comparison_data['stocks'].append(stock_metric)
                
            except Exception as e:
                comparison_data['stocks'].append({
                    'symbol': symbol.upper(),
                    'error': str(e)
                })
        
        # Sort by metric value (handle N/A values)
        comparison_data['stocks'].sort(
            key=lambda x: x.get('metric_value', 0) if isinstance(x.get('metric_value'), (int, float)) else 0,
            reverse=True
        )
        
        # Save to file
        os.makedirs(FINANCE_DIR, exist_ok=True)
        filename = os.path.join(FINANCE_DIR, f"comparison_{metric}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filename, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        
        logger.info(f"Stock comparison saved to {filename}")
        return json.dumps(comparison_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error comparing stocks: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@mcp.tool()
def get_market_summary() -> str:
    """
    Get summary of major market indices.
    
    Returns:
        JSON string with market indices information
    """
    try:
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^RUT': 'Russell 2000',
            '^VIX': 'VIX'
        }
        
        market_data = {
            'summary_date': datetime.now().isoformat(),
            'indices': []
        }
        
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="2d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change = current_price - previous_price
                    change_percent = (change / previous_price) * 100 if previous_price != 0 else 0
                    
                    index_data = {
                        'symbol': symbol,
                        'name': name,
                        'current_price': float(current_price),
                        'change': float(change),
                        'change_percent': float(change_percent)
                    }
                    
                    market_data['indices'].append(index_data)
                    
            except Exception as e:
                market_data['indices'].append({
                    'symbol': symbol,
                    'name': name,
                    'error': str(e)
                })
        
        # Save to file
        os.makedirs(FINANCE_DIR, exist_ok=True)
        filename = os.path.join(FINANCE_DIR, f"market_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filename, 'w') as f:
            json.dump(market_data, f, indent=2)
        
        logger.info(f"Market summary saved to {filename}")
        return json.dumps(market_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error fetching market summary: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@mcp.resource("finance://portfolios")
def get_available_portfolios() -> str:
    """
    List all available saved portfolio analyses.
    
    This resource provides a list of all saved portfolio data files.
    """
    portfolios = []
    
    if os.path.exists(FINANCE_DIR):
        for file in os.listdir(FINANCE_DIR):
            if file.endswith('.json'):
                portfolios.append(file)
    
    content = "# Available Financial Data\\n\\n"
    if portfolios:
        for portfolio in sorted(portfolios):
            content += f"- {portfolio}\\n"
        content += f"\\nUse @{portfolio} to access specific financial data.\\n"
    else:
        content += "No financial data found.\\n"
    
    return content

@mcp.resource("finance://{filename}")
def get_financial_data(filename: str) -> str:
    """
    Get specific financial data from a saved file.
    
    Args:
        filename: The name of the financial data file to retrieve
    """
    file_path = os.path.join(FINANCE_DIR, filename)
    
    if not os.path.exists(file_path):
        return f"# Financial data file not found: {filename}\\n\\nAvailable files can be viewed with @portfolios"
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Create markdown content based on data type
        if 'symbol' in data and 'current_price' in data:
            # Stock info format
            content = f"# Stock Information: {data['symbol']}\\n\\n"
            content += f"**Company**: {data.get('name', 'N/A')}\\n"
            content += f"**Current Price**: ${data.get('current_price', 'N/A')}\\n"
            content += f"**Market Cap**: {data.get('market_cap', 'N/A')}\\n"
            content += f"**P/E Ratio**: {data.get('pe_ratio', 'N/A')}\\n"
            content += f"**Sector**: {data.get('sector', 'N/A')}\\n"
            content += f"**Industry**: {data.get('industry', 'N/A')}\\n"
        elif 'indices' in data:
            # Market summary format
            content = f"# Market Summary\\n\\n"
            content += f"**Date**: {data.get('summary_date', 'N/A')}\\n\\n"
            for index in data['indices']:
                content += f"## {index['name']} ({index['symbol']})\\n"
                content += f"- **Price**: {index.get('current_price', 'N/A')}\\n"
                content += f"- **Change**: {index.get('change', 'N/A')} ({index.get('change_percent', 'N/A')}%)\\n\\n"
        else:
            # Generic JSON format
            content = f"# Financial Data: {filename}\\n\\n"
            content += f"```json\\n{json.dumps(data, indent=2)}\\n```\\n"
        
        return content
        
    except json.JSONDecodeError:
        return f"# Error reading financial data: {filename}\\n\\nThe data file is corrupted."

@mcp.prompt()
def analyze_stock_prompt(symbol: str, analysis_type: str = "comprehensive") -> str:
    """Generate a prompt for comprehensive stock analysis."""
    return f"""Analyze the stock {symbol.upper()} using the available financial tools. Follow these steps:

1. **Basic Information**: Use get_stock_info('{symbol}') to get current stock information including:
   - Current price and market metrics
   - Company information and sector
   - Key financial ratios

2. **Historical Performance**: Use get_historical_data('{symbol}', period='1y') to analyze:
   - Price trends over the past year
   - Volatility patterns
   - Support and resistance levels

3. **Market Context**: Use get_market_summary() to understand:
   - Overall market conditions
   - How {symbol} might be affected by broader market trends

4. **Analysis Output**: Provide a structured analysis including:
   - **Executive Summary**: Key findings about {symbol}
   - **Financial Health**: Assessment of key metrics
   - **Technical Analysis**: Price trend and pattern analysis
   - **Market Position**: How the stock compares to market indices
   - **Risk Factors**: Potential concerns or volatility indicators
   - **Investment Considerations**: Key points for potential investors

5. **Recommendations**: Based on the data, provide:
   - Short-term outlook (1-3 months)
   - Long-term outlook (1+ years)
   - Key factors to monitor

Please ensure all analysis is based on the factual data retrieved from the tools and clearly distinguish between factual data and analytical interpretation."""

@mcp.prompt()
def portfolio_comparison_prompt(symbols: List[str], timeframe: str = "1y") -> str:
    """Generate a prompt for comparing multiple stocks in a portfolio context."""
    symbols_str = ", ".join(symbols)
    return f"""Compare and analyze the following stocks as a potential portfolio: {symbols_str}

Follow this comprehensive analysis framework:

1. **Individual Stock Analysis**: For each stock ({symbols_str}):
   - Use get_stock_info() to gather basic information
   - Use get_historical_data() with {timeframe} period for performance data

2. **Comparative Analysis**: Use compare_stocks() to compare:
   - Current valuations (P/E ratios)
   - Market capitalizations
   - Trading volumes
   - Price performance

3. **Portfolio Construction Analysis**:
   - **Diversification**: Analyze sector and industry distribution
   - **Risk Assessment**: Compare volatility patterns
   - **Correlation Analysis**: Identify how stocks move relative to each other
   - **Performance Metrics**: Calculate risk-adjusted returns where possible

4. **Market Context**: Use get_market_summary() to understand:
   - How this portfolio would perform relative to major indices
   - Market conditions affecting these sectors

5. **Portfolio Recommendations**:
   - **Optimal Weighting**: Suggest allocation percentages
   - **Risk Management**: Identify concentration risks
   - **Rebalancing Strategy**: When and how to adjust holdings
   - **Entry/Exit Points**: Optimal timing considerations

6. **Monitoring Framework**:
   - Key metrics to track regularly
   - Warning signs for each position
   - Market conditions that would trigger portfolio changes

Present your analysis in a clear, actionable format suitable for investment decision-making."""

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
