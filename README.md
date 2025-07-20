# Financial MCP Project

A Model Context Protocol (MCP) implementation for financial data analysis using yfinance, featuring a comprehensive server with tools, resources, and prompts for stock market analysis.

## 🚀 Features

### MCP Server (financial_server.py)
- **Tools**: 5 powerful financial analysis tools
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

### MCP Client (financial_chatbot.py)
- Interactive chat interface with financial focus
- Support for resources (@portfolios, @filename)
- Support for prompts (/prompts, /prompt <name> <args>)
- Integration with multiple MCP servers
- Real-time financial data queries

### Safety Features (guardrails.py)
- Stock symbol validation
- Rate limiting protection
- Data quality checks
- Input sanitization
- Error handling and logging

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

# Install dependencies
uv add mcp yfinance anthropic python-dotenv nest-asyncio pandas numpy
```

3. **Set up environment variables:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Anthropic API key
ANTHROPIC_API_KEY=your_actual_api_key_here
```

## 🏃‍♂️ Quick Start

### Running the MCP Server (Testing)
```bash
# Test the server with MCP inspector
npx @modelcontextprotocol/inspector uv run financial_server.py
```

### Running the Financial Chatbot
```bash
# Start the integrated chatbot
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

### Advanced Analysis
```
Query: Analyze the tech sector by comparing AAPL, GOOGL, MSFT, and NVDA
Query: What's the current market sentiment based on major indices?
Query: Create a risk assessment for a portfolio containing AAPL, TSLA, and NVDA
```

## 🛠️ Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_stock_info` | Get comprehensive stock information | `symbol` (required) |
| `get_historical_data` | Get historical price data | `symbol` (required), `period`, `interval` |
| `compare_stocks` | Compare multiple stocks | `symbols` (list), `metric` |
| `get_market_summary` | Get major market indices | None |

## 📊 Supported Data

- **Stock Information**: Price, market cap, P/E ratio, dividends, volume
- **Historical Data**: OHLCV data with customizable periods and intervals
- **Market Indices**: S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX
- **Comparison Metrics**: Price, market cap, P/E ratio, volume, and more

## 🔒 Safety Features

- **Input Validation**: Stock symbols, date ranges, parameters
- **Rate Limiting**: Prevents API abuse (30 requests/minute default)
- **Data Sanitization**: Handles missing/invalid data gracefully
- **Error Handling**: Comprehensive error logging and user feedback
- **Quality Checks**: Warns about stale or unusual data

## 📁 Project Structure

```
financial-mcp-project/
├── financial_server.py      # MCP server with financial tools
├── financial_chatbot.py     # MCP client chatbot
├── guardrails.py            # Safety and validation module
├── server_config.json       # MCP server configuration
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment variables template
├── README.md                # This file
└── financial_data/          # Generated data directory
    ├── AAPL_info.json
    ├── TSLA_historical_1y_1d.json
    └── market_summary_*.json
```

## 🧪 Testing

Run the MCP inspector to test your server:
```bash
npx @modelcontextprotocol/inspector uv run financial_server.py
```

Test individual components:
```bash
# Test guardrails
python -c "from guardrails import guardrails; print(guardrails.validate_stock_symbol('AAPL'))"

# Test server functions directly
python -c "import yfinance as yf; print(yf.Ticker('AAPL').info['currentPrice'])"
```

## 🔧 Configuration

### Environment Variables
- `ANTHROPIC_API_KEY`: Required for Claude API access
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `FINANCE_DATA_DIR`: Directory for saving financial data
- `MAX_REQUESTS_PER_MINUTE`: Rate limiting (default: 30)
- `MAX_SYMBOLS_PER_REQUEST`: Maximum symbols per comparison (default: 10)

### Server Configuration
Edit `server_config.json` to add/remove MCP servers:
```json
{
    "mcpServers": {
        "finance": {
            "command": "uv",
            "args": ["run", "financial_server.py"]
        }
    }
}
```

## 🚨 Important Notes

1. **API Limits**: yfinance has unofficial rate limits. The guardrails help prevent issues.
2. **Data Accuracy**: Financial data is for informational purposes only.
3. **Real-time Data**: Some data may have delays depending on the source.
4. **Error Handling**: The system gracefully handles network issues and invalid requests.

## 📈 Extended Usage

### Portfolio Analysis
```python
# Through the chatbot
Query: /prompt portfolio_comparison_prompt symbols=["AAPL","GOOGL","MSFT","AMZN"] timeframe=1y

# This will:
# 1. Get individual stock information
# 2. Retrieve historical data
# 3. Compare key metrics
# 4. Provide portfolio recommendations
# 5. Suggest risk management strategies
```

### Market Research
```python
Query: Get me a market summary and then analyze how TSLA compares to the overall market
```

### Risk Assessment
```python
Query: Compare the volatility of AAPL, TSLA, and Bitcoin (if available) over the past 6 months
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and informational purposes only. It is not intended as financial advice. Always consult with qualified financial professionals before making investment decisions.
