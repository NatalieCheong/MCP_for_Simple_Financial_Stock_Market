# Financial MCP Project

A Model Context Protocol (MCP) implementation demonstrating **financial data analysis as a use case**, built with yfinance and featuring a comprehensive server with tools, resources, and prompts for stock market analysis. **Now enhanced with enterprise-grade guardrails for security, compliance, and safety.** This project was inspired after I enrolled in the [MCP Course](https://learn.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic/lesson/fkbhh/introduction) offered by DeepLearning.ai in collaboration with Anthropic.


## 🚀 Features

### MCP Server (financial_server.py)
- **Tools**: 4 powerful financial analysis tools
  - `get_stock_info`: Get comprehensive stock information
  - `get_historical_data`: Retrieve historical price data
  - `compare_stocks`: Compare multiple stocks by metrics
  - `get_market_summary`: Get major market indices summary
- **Resources**: Access saved financial data
  - `finance://portfolios`: List all saved analyses
  - `finance://{filename}`: Access specific data files
- **Prompts**: Pre-built analysis templates
  - `analyze_stock_prompt`: Comprehensive stock analysis
  - `portfolio_comparison_prompt`: Multi-stock portfolio analysis

### Enhanced MCP Client (enhanced_financial_chatbot.py)
- Interactive chat interface with financial focus
- **🛡️ Comprehensive guardrails system**
- Support for resources (@portfolios, @filename)
- Support for prompts (/prompts, /prompt <name> <args>)
- Integration with multiple MCP servers
- Real-time financial data queries
- Session tracking and monitoring
- Investment advice detection and blocking

### 🛡️ Comprehensive Guardrails System (guardrails.py)
- **Content Filtering**: Blocks investment advice requests and high-risk content
- **Rate Limiting**: Prevents API abuse (15 calls/minute, 200/hour, 2000/day)
- **Input Validation**: Stock symbol format validation and sanitization
- **Security Protection**: Code injection detection and blocking
- **Session Management**: User session tracking with violation logging
- **Risk Assessment**: Automatic query risk level evaluation
- **Response Enhancement**: Automatic disclaimers and safety warnings
- **Compliance Features**: Regulatory compliance and professional referrals

## 📦 Installation

1. **Clone and setup the project:**
```bash
# Create project directory
mkdir financial-mcp-project
cd financial-mcp-project

# Initialize with uv
uv init
```

2. **Install dependencies:**
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install core dependencies
uv add mcp yfinance anthropic python-dotenv nest-asyncio pandas numpy

# Install security libraries for guardrails
uv add ratelimit validators bleach
```

3. **Set up environment variables:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Anthropic API key
ANTHROPIC_API_KEY=your_actual_api_key_here
```

4. **Create required files and directories:**
```bash
# Create data directory
mkdir -p financial_data

# Create enhanced version directory
mkdir -p enhanced_version

# Create guardrails configuration in enhanced_version folder
touch enhanced_version/guardrails_config.json
```

## 🏃‍♂️ Quick Start

### Running the MCP Server (Testing)
```bash
# Test the server with MCP inspector
npx @modelcontextprotocol/inspector uv run financial_server.py
```

### Running the Enhanced Financial Chatbot
```bash
# Navigate to enhanced version folder
cd enhanced_version

# Start the chatbot with comprehensive guardrails
uv run enhanced_financial_chatbot.py
```

### Running the Simple Version (Optional)
```bash
# Navigate to enhanced version folder
cd enhanced_version

# Start the chatbot with basic guardrails
uv run simple_financial_chatbot.py
```

### Running the Original Basic Chatbot
```bash
# From main directory
uv run financial_chatbot.py
```

## 💬 Usage Examples

### Basic Stock Queries
```
Query: What's the current price of Apple stock?
Query: Get me historical data for TSLA over the past year
Query: Compare AAPL, GOOGL, and MSFT by market cap
```

### Using Resources
```
Query: @portfolios                    # List all saved data
Query: @AAPL_info.json               # View specific stock data
Query: @market_summary_20241220.json # View market summary
```

### Using Prompts
```
Query: /prompts                                              # List available prompts
Query: /prompt analyze_stock_prompt symbol=AAPL            # Analyze Apple stock
Query: /prompt portfolio_comparison_prompt symbols=["AAPL","GOOGL","MSFT"] timeframe=1y
```

### Guardrails Features
```
Query: /status                           # Check session statistics and violations
Query: Should I buy Apple stock?         # Will be blocked - investment advice
Query: What's a good investment?         # Will be blocked - investment advice
```

### Advanced Analysis
```
Query: Analyze the tech sector by comparing AAPL, GOOGL, MSFT, and NVDA
Query: What's the current market sentiment based on major indices?
Query: Create a risk assessment for a portfolio containing AAPL, TSLA, and NVDA
```

## 🛠️ Available Tools

| Tool | Description | Parameters | Guardrails Applied |
|------|-------------|------------|-------------------|
| `get_stock_info` | Get comprehensive stock information | `symbol` (required) | Symbol validation, rate limiting |
| `get_historical_data` | Get historical price data | `symbol`, `period`, `interval` | Symbol validation, period limits, data point limits |
| `compare_stocks` | Compare multiple stocks | `symbols` (list), `metric` | Symbol validation, maximum 10 symbols |
| `get_market_summary` | Get major market indices | None | Rate limiting only |

## 📊 Supported Data

- **Stock Information**: Price, market cap, P/E ratio, dividends, volume
- **Historical Data**: OHLCV data with customizable periods and intervals
- **Market Indices**: S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX
- **Comparison Metrics**: Price, market cap, P/E ratio, volume, and more

## 🔒 Comprehensive Safety Features

### Content Filtering
- **Investment Advice Detection**: Blocks queries asking for buy/sell recommendations
- **High-Risk Content**: Flags mentions of options, leverage, penny stocks, etc.
- **Blocked Keywords**: Prevents "pump and dump", "guaranteed returns", etc.
- **Professional Referrals**: Redirects advice requests to licensed financial advisors

### Security Protection
- **Input Sanitization**: Removes dangerous characters and validates input length
- **Code Injection Prevention**: Blocks SQL injection, XSS, and code execution attempts
- **Symbol Validation**: Ensures proper stock symbol format and blocks fake symbols
- **Response Filtering**: Limits response length and adds security metadata

### Rate Limiting & Resource Protection
- **Per-Session Limits**: 15 calls/minute, 200/hour, 2000/day
- **Burst Protection**: Prevents rapid-fire requests
- **Data Point Limits**: Maximum 10,000 historical data points per request
- **Symbol Limits**: Maximum 10 symbols per comparison

### Compliance & Monitoring
- **Session Tracking**: Unique session IDs for each user interaction
- **Violation Logging**: Comprehensive logging of security events
- **Risk Assessment**: Automatic classification of query risk levels
- **Audit Trail**: Complete record of user interactions and system responses

## 📁 Project Structure

```
financial-mcp-project/
├── financial_server.py           # MCP server with financial tools
├── financial_chatbot.py          # Original basic chatbot
├── server_config.json            # MCP server configuration
├── pyproject.toml                # Project dependencies
├── .env.example                  # Environment variables template
├── README.md                     # This file
├── financial_data/               # Generated data directory
│   ├── AAPL_info.json
│   ├── GOOGL_info.json
│   ├── NVDA_info.json
│   └── market_summary_20250720_132820.json
└── enhanced_version/             # Enhanced chatbot with guardrails
    ├── enhanced_financial_chatbot.py  # Main chatbot with comprehensive guardrails
    ├── simple_financial_chatbot.py    # Chatbot with basic guardrails (optional)
    ├── guardrails.py                  # Comprehensive security module
    └── guardrails_config.json         # Guardrails configuration
```

## 🧪 Testing

### Test the MCP Server
```bash
npx @modelcontextprotocol/inspector uv run financial_server.py
```

### Test Guardrails
```bash
# Navigate to enhanced version folder
cd enhanced_version

# Test basic validation
python -c "from guardrails import FinancialGuardrails; g = FinancialGuardrails(); print(g.validate_symbols(['AAPL']))"

# Test investment advice detection
python -c "from guardrails import validate_financial_query; print(validate_financial_query('Should I buy Apple stock?'))"
```

### Test Individual Components
```bash
# Test server functions directly
python -c "import yfinance as yf; print(yf.Ticker('AAPL').info['currentPrice'])"
```

## 🔧 Configuration

### Environment Variables
- `ANTHROPIC_API_KEY`: Required for Claude API access
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `FINANCE_DATA_DIR`: Directory for saving financial data

### Guardrails Configuration (enhanced_version/guardrails_config.json)
```json
{
  "rate_limiting": {
    "max_calls_per_minute": 15,
    "max_calls_per_hour": 200,
    "max_calls_per_day": 2000,
    "min_request_interval_seconds": 1
  },
  "content_filtering": {
    "blocked_keywords": [
      "pump and dump",
      "insider trading", 
      "guaranteed returns",
      "risk-free investment"
    ],
    "high_risk_terms": [
      "options", "derivatives", "leverage", "margin",
      "penny stocks", "crypto", "day trading"
    ]
  },
  "symbol_validation": {
    "max_symbols_per_request": 10,
    "blocked_symbols": ["SCAM", "FAKE", "TEST"]
  },
  "security": {
    "sanitize_inputs": true,
    "max_input_length": 2000,
    "timeout_seconds": 45
  }
}
```

### Server Configuration
Edit `server_config.json` to configure MCP servers:
```json
{
    "mcpServers": {
        "finance": {
            "command": "uv",
            "args": ["run", "financial_server.py"]
        },
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
        }
    }
}
```

## 🚨 Important Security Notes

### What the Guardrails Prevent
1. **Investment Advice**: Blocks queries asking for buy/sell recommendations
2. **High-Risk Content**: Flags dangerous financial instruments and schemes
3. **API Abuse**: Rate limiting prevents server overload
4. **Security Threats**: Blocks code injection and malicious input
5. **Compliance Violations**: Ensures regulatory compliance with disclaimers

### What Users Can Still Do
1. **Get Factual Data**: Stock prices, market information, company data
2. **Analyze Trends**: Historical performance and technical analysis
3. **Compare Options**: Side-by-side stock comparisons
4. **Educational Content**: Learn about financial concepts and markets

### Monitoring and Logging
- All security violations are logged with timestamps
- Session statistics available via `/status` command
- Comprehensive audit trail for compliance purposes
- Real-time monitoring of suspicious activity

## 📈 Extended Usage

### Portfolio Analysis with Guardrails
```bash
# This will work - factual analysis
Query: /prompt portfolio_comparison_prompt symbols=["AAPL","GOOGL","MSFT"] timeframe=1y

# This will be blocked - investment advice
Query: Which of these stocks should I buy for my retirement portfolio?
```

### Market Research (Compliant)
```bash
# Allowed - factual market data
Query: Get me a market summary and compare TSLA's performance to the S&P 500

# Blocked - prediction request
Query: Which stocks will go up next week?
```

### Risk Assessment (Educational)
```bash
# Allowed - educational risk analysis
Query: Compare the historical volatility of AAPL, TSLA, and QQQ over 6 months

# Blocked - specific investment guidance
Query: How much should I invest in each of these stocks?
```

## 🛡️ Guardrails Architecture

### Client-Side Protection (enhanced_version/enhanced_financial_chatbot.py)
- Query validation and filtering
- Session management and tracking
- User interface for monitoring
- Response enhancement with disclaimers

### Modular Security (enhanced_version/guardrails.py)
- Reusable security components
- Configurable validation rules
- Comprehensive logging system
- Risk assessment algorithms

### Configuration-Driven (enhanced_version/guardrails_config.json)
- Adjustable security parameters
- Environment-specific settings
- Easy policy updates
- Compliance customization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all guardrails tests pass
5. Update security documentation if needed
6. Submit a pull request

### Security Contributions
When contributing to guardrails:
- Test all security features thoroughly
- Document new validation rules
- Consider compliance implications
- Update configuration examples

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Legal Disclaimer

**IMPORTANT**: This software is for educational and informational purposes only and is intended for non-commercial use. It is not intended as financial advice, investment guidance, or professional recommendation. 

### What This System Does
- Provides factual financial data and market information
- Offers educational content about financial concepts
- Enables data analysis and research capabilities
- Maintains strict compliance with informational use guidelines

### What This System Does NOT Do
- Provide investment advice or recommendations
- Guarantee accuracy of market predictions
- Replace professional financial consultation
- Offer personalized investment strategies

### User Responsibilities
- Consult qualified financial professionals for investment decisions
- Verify all data through official sources before acting
- Understand that past performance does not guarantee future results
- Use information solely for educational and research purposes

### Compliance Statement
This system includes comprehensive guardrails designed to prevent the provision of unlicensed financial advice and ensure compliance with relevant regulations. All users are directed to consult with licensed financial advisors for investment decisions.

**By using this system, you acknowledge that you understand these limitations and will use the information responsibly.**





