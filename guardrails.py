"""
Financial Data Guardrails and Validation Module

This module provides safety checks and validation for financial data operations
to ensure data integrity and prevent common errors.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)

class FinancialGuardrails:
    """
    Provides validation and safety checks for financial operations.
    """
    
    # Valid yfinance periods and intervals
    VALID_PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    VALID_INTERVALS = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
    
    # Rate limiting settings
    MAX_REQUESTS_PER_MINUTE = 30
    MAX_SYMBOLS_PER_REQUEST = 10
    
    def __init__(self):
        self.request_history = []
    
    def validate_stock_symbol(self, symbol: str) -> Tuple[bool, str]:
        """
        Validate a stock symbol format and existence.
        
        Args:
            symbol: Stock ticker symbol to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not symbol:
            return False, "Symbol cannot be empty"
        
        # Clean and uppercase symbol
        symbol = symbol.strip().upper()
        
        # Basic format validation
        if not re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', symbol):
            return False, f"Invalid symbol format: {symbol}. Must be 1-5 letters, optionally followed by .XX"
        
        # Check if symbol exists (with timeout protection)
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got meaningful data
            if not info or info.get('regularMarketPrice') is None and info.get('currentPrice') is None:
                return False, f"Symbol {symbol} not found or has no price data"
                
            return True, ""
            
        except Exception as e:
            logger.warning(f"Error validating symbol {symbol}: {e}")
            return False, f"Unable to validate symbol {symbol}: {str(e)}"
    
    def validate_period_interval(self, period: str, interval: str) -> Tuple[bool, str]:
        """
        Validate period and interval combination for yfinance.
        
        Args:
            period: Time period for data
            interval: Data interval
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if period not in self.VALID_PERIODS:
            return False, f"Invalid period: {period}. Valid periods: {', '.join(self.VALID_PERIODS)}"
        
        if interval not in self.VALID_INTERVALS:
            return False, f"Invalid interval: {interval}. Valid intervals: {', '.join(self.VALID_INTERVALS)}"
        
        # Check logical combinations
        incompatible_combinations = [
            # Short intervals with long periods (would create too much data)
            (['1m', '2m', '5m'], ['1y', '2y', '5y', '10y', 'max']),
            (['15m', '30m'], ['2y', '5y', '10y', 'max']),
            (['60m', '90m'], ['5y', '10y', 'max']),
            # Long intervals with short periods (insufficient data points)
            (['1d', '5d', '1wk'], ['1d']),
            (['1mo', '3mo'], ['1d', '5d', '1mo'])
        ]
        
        for intervals, periods in incompatible_combinations:
            if interval in intervals and period in periods:
                return False, f"Incompatible combination: {interval} interval with {period} period"
        
        return True, ""
    
    def validate_symbol_list(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a list of stock symbols.
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            Tuple of (valid_symbols, error_messages)
        """
        if len(symbols) > self.MAX_SYMBOLS_PER_REQUEST:
            return [], [f"Too many symbols: {len(symbols)}. Maximum allowed: {self.MAX_SYMBOLS_PER_REQUEST}"]
        
        valid_symbols = []
        errors = []
        
        for symbol in symbols:
            is_valid, error = self.validate_stock_symbol(symbol)
            if is_valid:
                valid_symbols.append(symbol.upper())
            else:
                errors.append(error)
        
        return valid_symbols, errors
    
    def check_rate_limit(self) -> Tuple[bool, str]:
        """
        Check if request is within rate limits.
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        now = datetime.now()
        
        # Remove requests older than 1 minute
        cutoff_time = now - timedelta(minutes=1)
        self.request_history = [req_time for req_time in self.request_history if req_time > cutoff_time]
        
        # Check if we're under the limit
        if len(self.request_history) >= self.MAX_REQUESTS_PER_MINUTE:
            return False, f"Rate limit exceeded: {len(self.request_history)} requests in the last minute. Maximum: {self.MAX_REQUESTS_PER_MINUTE}"
        
        # Add current request to history
        self.request_history.append(now)
        return True, ""
    
    def validate_metric(self, metric: str) -> Tuple[bool, str]:
        """
        Validate if a metric is available for comparison.
        
        Args:
            metric: Metric name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_metrics = [
            'currentPrice', 'regularMarketPrice', 'marketCap', 'trailingPE',
            'forwardPE', 'dividendYield', 'volume', 'averageVolume',
            'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', 'beta', 'profitMargins',
            'operatingMargins', 'returnOnAssets', 'returnOnEquity',
            'revenueGrowth', 'earningsGrowth', 'debtToEquity'
        ]
        
        if metric not in valid_metrics:
            return False, f"Invalid metric: {metric}. Valid metrics: {', '.join(valid_metrics)}"
        
        return True, ""
    
    def sanitize_financial_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize financial data to handle common issues.
        
        Args:
            data: Raw financial data dictionary
            
        Returns:
            Sanitized data dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            # Handle None values
            if value is None:
                sanitized[key] = "N/A"
                continue
            
            # Handle infinite values
            if isinstance(value, (int, float)):
                if value == float('inf') or value == float('-inf'):
                    sanitized[key] = "N/A"
                    continue
                
                # Round very large numbers for readability
                if isinstance(value, float) and abs(value) > 1e10:
                    sanitized[key] = f"{value:.2e}"
                elif isinstance(value, float):
                    sanitized[key] = round(value, 4)
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        
        return sanitized
    
    def validate_date_range(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate date range for historical data requests.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                if start > datetime.now():
                    return False, "Start date cannot be in the future"
            
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if end > datetime.now():
                    return False, "End date cannot be in the future"
            
            if start_date and end_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if start >= end:
                    return False, "Start date must be before end date"
                
                # Check if date range is too large
                if (end - start).days > 365 * 10:  # 10 years max
                    return False, "Date range too large (maximum 10 years)"
            
            return True, ""
            
        except ValueError as e:
            return False, f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
    
    def check_data_quality(self, data: Dict[str, Any]) -> List[str]:
        """
        Check quality of retrieved financial data and provide warnings.
        
        Args:
            data: Financial data to check
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check for missing critical data
        critical_fields = ['currentPrice', 'regularMarketPrice']
        if not any(field in data and data[field] not in [None, 'N/A'] for field in critical_fields):
            warnings.append("No current price data available")
        
        # Check for stale data
        if 'lastMarketTime' in data:
            try:
                last_update = datetime.fromtimestamp(data['lastMarketTime'])
                if (datetime.now() - last_update).days > 7:
                    warnings.append("Data may be stale (last update > 7 days ago)")
            except (ValueError, TypeError):
                pass
        
        # Check for unusual values
        if 'trailingPE' in data and isinstance(data['trailingPE'], (int, float)):
            if data['trailingPE'] < 0:
                warnings.append("Negative P/E ratio indicates losses")
            elif data['trailingPE'] > 1000:
                warnings.append("Extremely high P/E ratio - verify data accuracy")
        
        # Check market cap consistency
        if all(field in data for field in ['marketCap', 'sharesOutstanding', 'currentPrice']):
            try:
                calculated_cap = data['sharesOutstanding'] * data['currentPrice']
                if abs(calculated_cap - data['marketCap']) / data['marketCap'] > 0.1:
                    warnings.append("Market cap and share price data may be inconsistent")
            except (TypeError, ZeroDivisionError):
                pass
        
        return warnings

# Global instance for easy import
guardrails = FinancialGuardrails()

def validate_and_execute(func):
    """
    Decorator to add validation and safety checks to financial functions.
    """
    def wrapper(*args, **kwargs):
        # Rate limiting check
        allowed, error = guardrails.check_rate_limit()
        if not allowed:
            logger.warning(f"Rate limit exceeded: {error}")
            return {"error": error}
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return {"error": f"Function execution failed: {str(e)}"}
    
    return wrapper
