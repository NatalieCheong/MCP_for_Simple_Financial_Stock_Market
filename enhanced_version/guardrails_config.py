{
    "rate_limiting": {
      "max_calls_per_minute": 15,
      "max_calls_per_hour": 200,
      "max_calls_per_day": 2000,
      "min_request_interval_seconds": 1,
      "burst_allowance": 5
    },
    "content_filtering": {
      "blocked_keywords": [
        "pump and dump",
        "insider trading", 
        "market manipulation",
        "guaranteed returns",
        "risk-free investment",
        "get rich quick",
        "sure thing",
        "hot tip",
        "insider info",
        "market maker manipulation",
        "short squeeze guarantee"
      ],
      "high_risk_terms": [
        "options",
        "derivatives", 
        "leverage",
        "margin",
        "short selling",
        "penny stocks",
        "crypto",
        "cryptocurrency",
        "forex",
        "day trading",
        "swing trading",
        "futures",
        "commodities",
        "warrants",
        "cfds",
        "binary options",
        "spread betting"
      ],
      "investment_advice_patterns": [
        "should\\s+i\\s+buy",
        "should\\s+i\\s+sell", 
        "what\\s+should\\s+i\\s+invest",
        "recommend\\s+(buying|selling|investing)",
        "investment\\s+advice",
        "trading\\s+advice",
        "financial\\s+advice",
        "stock\\s+tip",
        "hot\\s+stock",
        "next\\s+big\\s+thing",
        "buy\\s+now",
        "sell\\s+now",
        "act\\s+fast"
      ]
    },
    "symbol_validation": {
      "max_symbols_per_request": 10,
      "blocked_symbols": [
        "SCAM",
        "FAKE", 
        "TEST",
        "FRAUD",
        "PONZI"
      ],
      "allowed_symbol_pattern": "^[A-Za-z0-9\\._\\-\\^]{1,10}$",
      "require_major_exchanges": true
    },
    "data_access": {
      "max_historical_period_days": 1825,
      "allowed_intervals": [
        "1m", "5m", "15m", "30m", "1h", "1d", "5d", "1wk", "1mo"
      ],
      "max_data_points": 10000,
      "max_symbols_in_comparison": 15
    },
    "security": {
      "sanitize_inputs": true,
      "max_input_length": 2000,
      "timeout_seconds": 45,
      "log_violations": true,
      "block_suspicious_patterns": true
    },
    "response_filtering": {
      "add_disclaimers": true,
      "max_response_length": 15000,
      "include_risk_warnings": true,
      "add_data_source_attribution": true
    }
  }
