"""
Financial Guardrails Module
Comprehensive security and safety measures for financial applications
"""

import re
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class GuardrailViolationType(Enum):
    RATE_LIMIT = "rate_limit"
    INVESTMENT_ADVICE = "investment_advice"
    HIGH_RISK_CONTENT = "high_risk_content"
    INVALID_SYMBOL = "invalid_symbol"
    CODE_INJECTION = "code_injection"
    EXCESSIVE_REQUEST = "excessive_request"
    BLOCKED_CONTENT = "blocked_content"

@dataclass
class GuardrailViolation:
    violation_type: GuardrailViolationType
    message: str
    risk_level: RiskLevel
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[Dict] = None

@dataclass
class RateLimitTracker:
    """Track API call rates per user/session"""
    calls_per_minute: int = 0
    calls_per_hour: int = 0
    calls_per_day: int = 0
    last_reset_minute: datetime = field(default_factory=datetime.now)
    last_reset_hour: datetime = field(default_factory=datetime.now)
    last_reset_day: datetime = field(default_factory=datetime.now)
    violations: List[GuardrailViolation] = field(default_factory=list)

class FinancialGuardrails:
    """
    Comprehensive guardrails system for financial applications.
    Can be used by both client and server components.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.rate_limiters: Dict[str, RateLimitTracker] = {}
        self.blocked_symbols: Set[str] = set(self.config.get('blocked_symbols', []))
        self.session_data: Dict[str, Dict] = {}
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "rate_limiting": {
                "max_calls_per_minute": 10,
                "max_calls_per_hour": 100,
                "max_calls_per_day": 1000,
                "min_request_interval_seconds": 1,
                "burst_allowance": 3
            },
            "content_filtering": {
                "blocked_keywords": [
                    "pump and dump", "insider trading", "market manipulation",
                    "guaranteed returns", "risk-free investment", "get rich quick",
                    "sure thing", "hot tip", "insider info"
                ],
                "high_risk_terms": [
                    "options", "derivatives", "leverage", "margin", "short selling",
                    "penny stocks", "crypto", "forex", "day trading", "swing trading",
                    "futures", "commodities", "warrants", "cfds"
                ],
                "investment_advice_patterns": [
                    r"\b(should\s+i\s+buy|should\s+i\s+sell|what\s+should\s+i\s+invest)",
                    r"\b(recommend\s+(buying|selling|investing))",
                    r"\b(investment\s+advice|trading\s+advice|financial\s+advice)",
                    r"\b(stock\s+tip|hot\s+stock|next\s+big\s+thing)",
                    r"\b(buy\s+now|sell\s+now|act\s+fast)",
                ]
            },
            "symbol_validation": {
                "max_symbols_per_request": 10,
                "blocked_symbols": ["SCAM", "FAKE", "TEST"],
                "allowed_symbol_pattern": r"^[A-Za-z0-9\._\-\^]{1,10}$",
                "require_major_exchanges": True
            },
            "data_access": {
                "max_historical_period_days": 1825,  # 5 years
                "allowed_intervals": ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"],
                "max_data_points": 10000,
                "max_symbols_in_comparison": 10
            },
            "security": {
                "sanitize_inputs": True,
                "max_input_length": 1000,
                "timeout_seconds": 30,
                "log_violations": True
            },
            "response_filtering": {
                "add_disclaimers": True,
                "max_response_length": 10000,
                "include_risk_warnings": True
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    self._deep_merge(default_config, user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching"""
        self.investment_advice_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.config["content_filtering"]["investment_advice_patterns"]
        ]
        
        self.symbol_pattern = re.compile(
            self.config["symbol_validation"]["allowed_symbol_pattern"]
        )
        
        # Code injection patterns
        self.injection_patterns = [
            re.compile(r'["\'].*["\'].*[;]'),  # SQL injection
            re.compile(r'<script.*</script>', re.IGNORECASE),  # XSS
            re.compile(r'(union|select|insert|update|delete|drop)\s+', re.IGNORECASE),
            re.compile(r'(system|exec|eval|import)\s*\(', re.IGNORECASE),
            re.compile(r'(__.*__|\.\.\/)', re.IGNORECASE),  # Path traversal
        ]
    
    def get_session_id(self, identifier: str = "default") -> str:
        """Generate session ID for tracking"""
        return hashlib.md5(f"{identifier}_{datetime.now().date()}".encode()).hexdigest()[:16]
    
    def validate_query(self, query: str, session_id: str = "default") -> Tuple[bool, Optional[GuardrailViolation], RiskLevel]:
        """
        Comprehensive query validation
        
        Returns:
            (is_valid, violation_or_none, risk_level)
        """
        if not query or len(query.strip()) == 0:
            return True, None, RiskLevel.LOW
        
        # Check input length
        if len(query) > self.config["security"]["max_input_length"]:
            violation = GuardrailViolation(
                violation_type=GuardrailViolationType.EXCESSIVE_REQUEST,
                message=f"Query too long (max {self.config['security']['max_input_length']} chars)",
                risk_level=RiskLevel.MEDIUM
            )
            return False, violation, RiskLevel.MEDIUM
        
        query_lower = query.lower()
        
        # 1. Check for code injection attempts
        for pattern in self.injection_patterns:
            if pattern.search(query):
                violation = GuardrailViolation(
                    violation_type=GuardrailViolationType.CODE_INJECTION,
                    message="Potential security threat detected in query",
                    risk_level=RiskLevel.CRITICAL,
                    details={"pattern": pattern.pattern}
                )
                return False, violation, RiskLevel.CRITICAL
        
        # 2. Check for investment advice requests
        for pattern in self.investment_advice_patterns:
            if pattern.search(query):
                violation = GuardrailViolation(
                    violation_type=GuardrailViolationType.INVESTMENT_ADVICE,
                    message="I cannot provide investment advice. I can only provide factual information about stocks and markets. Please consult a licensed financial advisor for investment decisions.",
                    risk_level=RiskLevel.HIGH
                )
                return False, violation, RiskLevel.HIGH
        
        # 3. Check for blocked keywords
        blocked_keywords = self.config["content_filtering"]["blocked_keywords"]
        for keyword in blocked_keywords:
            if keyword.lower() in query_lower:
                violation = GuardrailViolation(
                    violation_type=GuardrailViolationType.BLOCKED_CONTENT,
                    message=f"Query contains blocked content related to: {keyword}",
                    risk_level=RiskLevel.HIGH,
                    details={"blocked_keyword": keyword}
                )
                return False, violation, RiskLevel.HIGH
        
        # 4. Assess risk level based on high-risk terms
        risk_level = self._assess_risk_level(query_lower)
        if risk_level == RiskLevel.CRITICAL:
            violation = GuardrailViolation(
                violation_type=GuardrailViolationType.HIGH_RISK_CONTENT,
                message="This query involves extremely high-risk financial concepts. Please exercise extreme caution and consult professionals.",
                risk_level=RiskLevel.CRITICAL
            )
            return False, violation, RiskLevel.CRITICAL
        
        return True, None, risk_level
    
    def validate_symbols(self, symbols: List[str]) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate stock symbols
        
        Returns:
            (is_valid, error_message, clean_symbols)
        """
        if not symbols:
            return True, None, []
        
        max_symbols = self.config["symbol_validation"]["max_symbols_per_request"]
        if len(symbols) > max_symbols:
            return False, f"Too many symbols. Maximum {max_symbols} allowed.", []
        
        clean_symbols = []
        invalid_symbols = []
        
        for symbol in symbols:
            if not symbol or not isinstance(symbol, str):
                invalid_symbols.append(str(symbol))
                continue
                
            symbol = symbol.strip().upper()
            
            # Check format
            if not self.symbol_pattern.match(symbol):
                invalid_symbols.append(f"{symbol} (invalid format)")
                continue
            
            # Check if blocked
            if symbol in self.blocked_symbols:
                invalid_symbols.append(f"{symbol} (blocked)")
                continue
            
            clean_symbols.append(symbol)
        
        if invalid_symbols:
            return False, f"Invalid symbols: {', '.join(invalid_symbols)}", clean_symbols
        
        return True, None, clean_symbols
    
    def check_rate_limit(self, session_id: str = "default") -> Tuple[bool, Optional[str]]:
        """Check if request is within rate limits"""
        if session_id not in self.rate_limiters:
            self.rate_limiters[session_id] = RateLimitTracker()
        
        tracker = self.rate_limiters[session_id]
        now = datetime.now()
        config = self.config["rate_limiting"]
        
        # Reset counters if needed
        if (now - tracker.last_reset_minute).total_seconds() >= 60:
            tracker.calls_per_minute = 0
            tracker.last_reset_minute = now
        
        if (now - tracker.last_reset_hour).total_seconds() >= 3600:
            tracker.calls_per_hour = 0
            tracker.last_reset_hour = now
        
        if (now - tracker.last_reset_day).total_seconds() >= 86400:
            tracker.calls_per_day = 0
            tracker.last_reset_day = now
        
        # Check limits
        if tracker.calls_per_minute >= config["max_calls_per_minute"]:
            return False, f"Rate limit exceeded: {config['max_calls_per_minute']} calls per minute"
        
        if tracker.calls_per_hour >= config["max_calls_per_hour"]:
            return False, f"Rate limit exceeded: {config['max_calls_per_hour']} calls per hour"
        
        if tracker.calls_per_day >= config["max_calls_per_day"]:
            return False, f"Rate limit exceeded: {config['max_calls_per_day']} calls per day"
        
        return True, None
    
    def record_request(self, session_id: str = "default") -> None:
        """Record a successful request for rate limiting"""
        if session_id not in self.rate_limiters:
            self.rate_limiters[session_id] = RateLimitTracker()
        
        tracker = self.rate_limiters[session_id]
        tracker.calls_per_minute += 1
        tracker.calls_per_hour += 1
        tracker.calls_per_day += 1
    
    def validate_tool_call(self, tool_name: str, tool_args: Dict) -> Tuple[bool, Optional[str]]:
        """Validate specific tool calls and their arguments"""
        try:
            # Validate symbols in arguments
            if 'symbol' in tool_args:
                is_valid, error_msg, _ = self.validate_symbols([tool_args['symbol']])
                if not is_valid:
                    return False, error_msg
            
            if 'symbols' in tool_args:
                is_valid, error_msg, _ = self.validate_symbols(tool_args['symbols'])
                if not is_valid:
                    return False, error_msg
            
            # Tool-specific validations
            if tool_name == 'get_historical_data':
                period = tool_args.get('period', '1mo')
                interval = tool_args.get('interval', '1d')
                
                # Validate period
                if not self._is_valid_period(period):
                    return False, f"Invalid or excessive period: {period}"
                
                # Validate interval
                allowed_intervals = self.config["data_access"]["allowed_intervals"]
                if interval not in allowed_intervals:
                    return False, f"Invalid interval. Allowed: {', '.join(allowed_intervals)}"
            
            elif tool_name == 'compare_stocks':
                symbols = tool_args.get('symbols', [])
                max_compare = self.config["data_access"]["max_symbols_in_comparison"]
                if len(symbols) > max_compare:
                    return False, f"Too many symbols for comparison. Maximum: {max_compare}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Tool validation error: {e}")
            return False, f"Validation error: {str(e)}"
    
    def sanitize_input(self, input_str: str) -> str:
        """Sanitize user input"""
        if not self.config["security"]["sanitize_inputs"]:
            return input_str
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>"\';\\]', '', input_str)
        
        # Limit length
        max_length = self.config["security"]["max_input_length"]
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    def add_disclaimer(self, response: str, risk_level: RiskLevel) -> str:
        """Add appropriate disclaimers based on risk level"""
        if not self.config["response_filtering"]["add_disclaimers"]:
            return response
        
        disclaimers = {
            RiskLevel.LOW: "\n\n📋 Note: This information is for educational purposes only and should not be considered as investment advice.",
            RiskLevel.MEDIUM: "\n\n⚠️ Disclaimer: This data is for informational purposes only and not investment advice. Market conditions can change rapidly. Please consult a financial advisor.",
            RiskLevel.HIGH: "\n\n🚨 Important: This involves high-risk financial concepts. Please consult a licensed financial advisor before making any investment decisions. Past performance does not guarantee future results.",
            RiskLevel.CRITICAL: "\n\n🛑 Critical Warning: This involves extremely high-risk financial instruments that can result in significant losses. Seek professional advice and understand all risks before proceeding. Only invest what you can afford to lose."
        }
        
        return response + disclaimers.get(risk_level, disclaimers[RiskLevel.LOW])
    
    def log_violation(self, violation: GuardrailViolation, session_id: str = "default") -> None:
        """Log security violations"""
        if self.config["security"]["log_violations"]:
            logger.warning(f"Guardrail violation [{session_id}]: {violation.violation_type.value} - {violation.message}")
            
        # Store in session data for monitoring
        if session_id not in self.session_data:
            self.session_data[session_id] = {"violations": []}
        
        self.session_data[session_id]["violations"].append({
            "type": violation.violation_type.value,
            "message": violation.message,
            "risk_level": violation.risk_level.value,
            "timestamp": violation.timestamp.isoformat(),
            "details": violation.details
        })
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session"""
        stats = {
            "session_id": session_id,
            "rate_limits": {},
            "violations": [],
            "total_requests": 0
        }
        
        if session_id in self.rate_limiters:
            tracker = self.rate_limiters[session_id]
            stats["rate_limits"] = {
                "calls_per_minute": tracker.calls_per_minute,
                "calls_per_hour": tracker.calls_per_hour,
                "calls_per_day": tracker.calls_per_day
            }
            stats["total_requests"] = tracker.calls_per_day
        
        if session_id in self.session_data:
            stats["violations"] = self.session_data[session_id].get("violations", [])
        
        return stats
    
    def _assess_risk_level(self, query: str) -> RiskLevel:
        """Assess the risk level of a query"""
        high_risk_terms = self.config["content_filtering"]["high_risk_terms"]
        high_risk_count = sum(1 for term in high_risk_terms if term.lower() in query)
        
        if high_risk_count >= 3:
            return RiskLevel.CRITICAL
        elif high_risk_count >= 2:
            return RiskLevel.HIGH
        elif high_risk_count == 1:
            return RiskLevel.MEDIUM
        elif any(word in query for word in ['volatile', 'risky', 'speculation', 'gamble']):
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _is_valid_period(self, period: str) -> bool:
        """Check if historical data period is reasonable"""
        max_days = self.config["data_access"]["max_historical_period_days"]
        
        # Convert period to days
        period_map = {
            '1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '6mo': 180,
            '1y': 365, '2y': 730, '5y': 1825, '10y': 3650, 'max': 7300
        }
        
        days = period_map.get(period.lower(), 0)
        return 0 < days <= max_days

# Convenience functions for easy import
def create_guardrails(config_path: Optional[str] = None) -> FinancialGuardrails:
    """Create a new guardrails instance"""
    return FinancialGuardrails(config_path)

def validate_financial_query(query: str, guardrails: Optional[FinancialGuardrails] = None) -> Tuple[bool, str, RiskLevel]:
    """Quick validation function"""
    if guardrails is None:
        guardrails = FinancialGuardrails()
    
    is_valid, violation, risk_level = guardrails.validate_query(query)
    message = violation.message if violation else ""
    return is_valid, message, risk_level
