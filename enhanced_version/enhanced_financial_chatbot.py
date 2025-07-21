from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio
import re
import logging
from datetime import datetime
from guardrails import FinancialGuardrails, RiskLevel, GuardrailViolation, GuardrailViolationType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class FinancialChatBot:
    """
    An MCP-powered chatbot specialized for financial data analysis with comprehensive guardrails.
    """

    def __init__(self, guardrails_config_path: str = "guardrails_config.json"):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        self.available_resources: List[str] = []
        self.available_prompts: List[str] = []
        
        # Initialize guardrails with configuration
        self.guardrails = FinancialGuardrails(guardrails_config_path)
        
        # Generate session ID for this chatbot instance
        self.session_id = self.guardrails.get_session_id("chatbot_session")
        
        # Track conversation context for better safety
        self.conversation_history = []
        
        logger.info(f"Initialized Financial Chatbot with session ID: {self.session_id}")

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server with error handling."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            # List available resources
            try:
                resources_response = await session.list_resources()
                resources = resources_response.resources
                for resource in resources:
                    self.available_resources.append(resource.uri)
                print(f"Available resources from {server_name}:", [r.uri for r in resources])
            except Exception as e:
                logger.info(f"No resources available from {server_name}: {e}")
            
            # List available prompts
            try:
                prompts_response = await session.list_prompts()
                prompts = prompts_response.prompts
                for prompt in prompts:
                    self.available_prompts.append(prompt.name)
                print(f"Available prompts from {server_name}:", [p.name for p in prompts])
            except Exception as e:
                logger.info(f"No prompts available from {server_name}: {e}")
                
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
            logger.error(f"Connection error for {server_name}: {e}")

    async def connect_to_servers(self):
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            logger.error(f"Server configuration error: {e}")
            raise

    async def get_resource(self, resource_uri: str) -> str:
        """Get content from a resource with validation."""
        try:
            # Validate resource URI
            if not resource_uri.startswith('finance://'):
                return "⚠️ Error: Only finance resources are allowed for security reasons"
            
            # Find the session that provides this resource
            for session in self.sessions:
                try:
                    result = await session.read_resource(resource_uri)
                    content = result.contents[0].text if result.contents else "No content available"
                    
                    # Add disclaimer to resource content
                    disclaimer = "\n\n📋 Note: This financial data is for informational purposes only and should not be considered as investment advice."
                    return content + disclaimer
                except Exception:
                    continue
            return f"Resource not found: {resource_uri}"
        except Exception as e:
            return f"Error retrieving resource: {str(e)}"

    async def execute_prompt(self, prompt_name: str, arguments: Dict[str, str]) -> str:
        """Execute a prompt template with given arguments and validation."""
        try:
            # Validate prompt name (whitelist approach)
            allowed_prompts = ['analyze_stock_prompt', 'portfolio_comparison_prompt']
            if prompt_name not in allowed_prompts:
                return f"⚠️ Prompt '{prompt_name}' is not allowed for security reasons"
            
            # Validate and clean arguments
            clean_arguments = {}
            for key, value in arguments.items():
                # Sanitize input
                clean_value = self.guardrails.sanitize_input(str(value))
                clean_arguments[key] = clean_value
            
            # Additional validation for symbol arguments
            if 'symbol' in clean_arguments:
                symbols = [clean_arguments['symbol']]
                is_valid, error_msg, cleaned_symbols = self.guardrails.validate_symbols(symbols)
                if not is_valid:
                    return f"⚠️ Error: {error_msg}"
                clean_arguments['symbol'] = cleaned_symbols[0] if cleaned_symbols else clean_arguments['symbol']
            
            # Find the session that provides this prompt
            for session in self.sessions:
                try:
                    result = await session.get_prompt(prompt_name, clean_arguments)
                    if result.messages:
                        # Extract the prompt content and send to LLM
                        prompt_content = ""
                        for message in result.messages:
                            if hasattr(message, 'content'):
                                if hasattr(message.content, 'text'):
                                    prompt_content += message.content.text
                                else:
                                    prompt_content += str(message.content)
                        
                        # Process the prompt with the LLM
                        await self.process_query(prompt_content)
                        return ""
                    return "No prompt content received"
                except Exception:
                    continue
            return f"Prompt not found: {prompt_name}"
        except Exception as e:
            return f"Error executing prompt: {str(e)}"

    def list_prompts(self) -> str:
        """List all available prompts with safety information."""
        if not self.available_prompts:
            return "No prompts available."
        
        content = "Available prompts:\n"
        for prompt in self.available_prompts:
            content += f"- {prompt}\n"
        content += "\nUsage: /prompt <name> <arg1=value1> <arg2=value2>"
        content += "\n\n⚠️ All prompts are for informational purposes only and not investment advice."
        content += "\n📋 All inputs are automatically validated and sanitized for security."
        return content

    def parse_prompt_command(self, user_input: str) -> tuple:
        """Parse prompt command from user input with validation."""
        # Remove /prompt prefix
        command = user_input[7:].strip()  # Remove '/prompt '
        
        # Split by spaces but handle quoted arguments
        parts = re.findall(r'(\w+(?:=(?:"[^"]*"|[^\s]+))?)', command)
        
        if not parts:
            return None, {}
        
        prompt_name = parts[0]
        arguments = {}
        
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=', 1)
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                # Sanitize value using guardrails
                value = self.guardrails.sanitize_input(value)
                arguments[key] = value
        
        return prompt_name, arguments
    
    async def process_query(self, query: str):
        """Process a user query with comprehensive safety checks."""
        try:
            # 1. Rate limiting check
            rate_ok, rate_msg = self.guardrails.check_rate_limit(self.session_id)
            if not rate_ok:
                print(f"🚫 {rate_msg}")
                return
            
            # 2. Query validation
            is_valid, violation, risk_level = self.guardrails.validate_query(query, self.session_id)
            if not is_valid:
                print(f"🚫 {violation.message}")
                self.guardrails.log_violation(violation, self.session_id)
                return
            
            # 3. Record request for rate limiting
            self.guardrails.record_request(self.session_id)
            
            # 4. Add query to conversation history (limited size for privacy)
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'query': query[:200],  # Truncate for privacy
                'risk_level': risk_level.value,
                'session_id': self.session_id
            })
            
            # Keep only last 10 interactions
            if len(self.conversation_history) > 10:
                self.conversation_history.pop(0)
            
            messages = [{'role':'user', 'content':query}]
            
            # 5. Enhanced system prompt for Claude with guardrails context
            system_prompt = f"""You are a financial data assistant with strict safety guidelines. IMPORTANT RULES:

WHAT YOU CAN DO:
- Provide factual, objective financial data and market information
- Explain financial concepts and terminology
- Analyze historical performance and trends
- Compare financial metrics between companies
- Discuss market conditions and economic indicators

WHAT YOU CANNOT DO:
- Give investment advice or recommendations (buy/sell/hold)
- Predict future stock prices or market movements
- Guarantee returns or suggest "sure things"
- Provide trading strategies or timing advice
- Recommend specific investments or portfolio allocations

SAFETY REQUIREMENTS:
- Always include appropriate disclaimers
- Redirect investment advice requests to licensed financial professionals
- Focus on education and data analysis, not predictions
- Be transparent about data limitations and sources
- Maintain objectivity and avoid speculation

Current session risk level: {risk_level.value}
Session ID: {self.session_id}"""
            
            response = self.anthropic.messages.create(
                max_tokens = 4096,
                model = 'claude-3-5-sonnet-20241022',
                system = system_prompt,
                tools = self.available_tools,
                messages = messages
            )
            
            process_query = True
            while process_query:
                assistant_content = []
                for content in response.content:
                    if content.type =='text':
                        # Add disclaimer based on risk level using guardrails
                        final_response = self.guardrails.add_disclaimer(content.text, risk_level)
                        print(final_response)
                        assistant_content.append(content)
                        if(len(response.content) == 1):
                            process_query= False
                    elif content.type == 'tool_use':
                        assistant_content.append(content)
                        messages.append({'role':'assistant', 'content':assistant_content})
                        tool_id = content.id
                        tool_args = content.input
                        tool_name = content.name

                        print(f"\n🔧 Calling tool {tool_name} with args {tool_args}")
                        
                        # 6. Tool-specific validation using guardrails
                        valid_tool, tool_error = self.guardrails.validate_tool_call(tool_name, tool_args)
                        if not valid_tool:
                            error_msg = f"Tool call blocked by safety checks: {tool_error}"
                            print(f"❌ {error_msg}")
                            
                            # Log the violation
                            violation = GuardrailViolation(
                                violation_type=GuardrailViolationType.INVALID_SYMBOL,
                                message=tool_error,
                                risk_level=RiskLevel.MEDIUM,
                                details={"tool_name": tool_name, "args": tool_args}
                            )
                            self.guardrails.log_violation(violation, self.session_id)
                            
                            messages.append({"role": "user", 
                                              "content": [
                                                  {
                                                      "type": "tool_result",
                                                      "tool_use_id":tool_id,
                                                      "content": error_msg
                                                  }
                                              ]
                                            })
                        else:
                            # Add session_id to tool arguments for server-side tracking
                            enhanced_tool_args = {**tool_args, "session_id": self.session_id}
                            
                            # Call a tool using the appropriate session
                            try:
                                session = self.tool_to_session[tool_name]
                                result = await session.call_tool(tool_name, arguments=enhanced_tool_args)
                                print(f"✅ Tool result received")
                                
                                # Parse and validate tool response
                                tool_response = self._process_tool_response(result.content, tool_name, risk_level)
                                
                                messages.append({"role": "user", 
                                                  "content": [
                                                      {
                                                          "type": "tool_result",
                                                          "tool_use_id":tool_id,
                                                          "content": tool_response
                                                      }
                                                  ]
                                                })
                            except Exception as e:
                                error_msg = f"Error calling tool {tool_name}: {str(e)}"
                                print(f"❌ {error_msg}")
                                logger.error(f"Tool error: {e}")
                                
                                # Log the error
                                violation = GuardrailViolation(
                                    violation_type=GuardrailViolationType.EXCESSIVE_REQUEST,
                                    message=f"Tool execution failed: {str(e)}",
                                    risk_level=RiskLevel.MEDIUM,
                                    details={"tool_name": tool_name, "error": str(e)}
                                )
                                self.guardrails.log_violation(violation, self.session_id)
                                
                                messages.append({"role": "user", 
                                                  "content": [
                                                      {
                                                          "type": "tool_result",
                                                          "tool_use_id":tool_id,
                                                          "content": error_msg
                                                      }
                                                  ]
                                                })
                        
                        response = self.anthropic.messages.create(
                            max_tokens = 4096,
                            model = 'claude-3-5-sonnet-20241022',
                            system = system_prompt,
                            tools = self.available_tools,
                            messages = messages
                        ) 
                        
                        if(len(response.content) == 1 and response.content[0].type == "text"):
                            final_response = self.guardrails.add_disclaimer(response.content[0].text, risk_level)
                            print(final_response)
                            process_query= False
                            
        except Exception as e:
            print(f"❌ Error processing query: {str(e)}")
            logger.error(f"Query processing error: {e}")
            
            # Log the error as a violation
            violation = GuardrailViolation(
                violation_type=GuardrailViolationType.EXCESSIVE_REQUEST,
                message=f"Query processing failed: {str(e)}",
                risk_level=RiskLevel.HIGH,
                details={"error": str(e), "query": query[:100]}
            )
            self.guardrails.log_violation(violation, self.session_id)

    def _process_tool_response(self, response_content, tool_name: str, risk_level: RiskLevel) -> str:
        """Process and validate tool responses"""
        try:
            # Handle different response types
            if isinstance(response_content, list):
                # If it's a list, convert to string
                response_str = str(response_content[0]) if response_content else ""
            elif isinstance(response_content, str):
                response_str = response_content
            else:
                response_str = str(response_content)
            
            # Try to parse as JSON to add metadata
            try:
                response_data = json.loads(response_str)
                if isinstance(response_data, dict):
                    # Add guardrails metadata to response
                    response_data['guardrails_info'] = {
                        'validated': True,
                        'risk_level': risk_level.value,
                        'session_id': self.session_id,
                        'tool_name': tool_name,
                        'timestamp': datetime.now().isoformat()
                    }
                    return json.dumps(response_data, indent=2)
            except json.JSONDecodeError:
                # Not JSON, return as-is with disclaimer
                pass
            
            # Add basic disclaimer for non-JSON responses
            max_length = self.guardrails.config["response_filtering"]["max_response_length"]
            if len(response_str) > max_length:
                response_str = response_str[:max_length] + "... [response truncated for safety]"
            
            return response_str
            
        except Exception as e:
            logger.error(f"Error processing tool response: {e}")
            return f"Error processing response: {str(e)}"

    async def chat_loop(self):
        """Run an interactive chat loop with enhanced safety features."""
        print("\n💰 Financial MCP Chatbot Started!")
        print("=" * 60)
        print("🛡️ COMPREHENSIVE GUARDRAILS ENABLED:")
        print("• Rate limiting and input validation")
        print("• Content filtering and risk assessment")
        print("• No investment advice - informational only")
        print("• Automatic disclaimers and safety warnings")
        print("• Session tracking and violation logging")
        print("=" * 60)
        print("Available commands:")
        print("📊 Regular queries: Ask about stocks, markets, analysis")
        print("📁 Resources: @portfolios, @<filename>")
        print("📝 Prompts: /prompts, /prompt <n> <args>")
        print("📈 Status: /status (show session statistics)")
        print("❌ Exit: type 'quit'")
        print("=" * 60)
        print(f"🆔 Session ID: {self.session_id}")
        
        # Show available tools
        if self.available_tools:
            print("\n🔧 Available tools:")
            for tool in self.available_tools:
                print(f"  - {tool['name']}: {tool['description'][:80]}...")
        
        while True:
            try:
                query = input("\n💭 Query: ").strip()
        
                if query.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                
                # Handle status requests
                if query.lower() == '/status':
                    stats = self.guardrails.get_session_stats(self.session_id)
                    print("\n📊 Session Statistics:")
                    print(f"  • Total requests: {stats['total_requests']}")
                    print(f"  • Rate limits: {stats['rate_limits']}")
                    print(f"  • Violations: {len(stats['violations'])}")
                    if stats['violations']:
                        print("  • Recent violations:")
                        for violation in stats['violations'][-3:]:  # Show last 3
                            print(f"    - {violation['type']}: {violation['message'][:50]}...")
                    continue
                
                # Handle resource requests (@)
                if query.startswith('@'):
                    resource_name = query[1:]
                    if resource_name == 'portfolios':
                        result = await self.get_resource("finance://portfolios")
                    else:
                        result = await self.get_resource(f"finance://{resource_name}")
                    print(result)
                    continue
                
                # Handle prompt commands (/)
                if query.startswith('/prompts'):
                    print(self.list_prompts())
                    continue
                
                if query.startswith('/prompt '):
                    prompt_name, arguments = self.parse_prompt_command(query)
                    if prompt_name:
                        await self.execute_prompt(prompt_name, arguments)
                    else:
                        print("❌ Invalid prompt format. Use: /prompt <n> <arg1=value1>")
                    continue
                
                # Regular query processing with safety checks
                await self.process_query(query)
                        
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                logger.error(f"Chat loop error: {e}")
                
                # Log the error
                violation = GuardrailViolation(
                    violation_type=GuardrailViolationType.EXCESSIVE_REQUEST,
                    message=f"Chat loop error: {str(e)}",
                    risk_level=RiskLevel.MEDIUM,
                    details={"error": str(e)}
                )
                self.guardrails.log_violation(violation, self.session_id)

    async def cleanup(self):
        """Cleanly close all resources and show final statistics."""
        try:
            # Show final session statistics
            stats = self.guardrails.get_session_stats(self.session_id)
            print(f"\n📊 Final Session Statistics:")
            print(f"  • Total requests processed: {stats['total_requests']}")
            print(f"  • Security violations detected: {len(stats['violations'])}")
            print(f"  • Session duration: Complete")
            
            if stats['violations']:
                print(f"  • Violation types encountered:")
                violation_types = {}
                for v in stats['violations']:
                    vtype = v['type']
                    violation_types[vtype] = violation_types.get(vtype, 0) + 1
                for vtype, count in violation_types.items():
                    print(f"    - {vtype}: {count}")
            
        except Exception as e:
            logger.error(f"Error generating final statistics: {e}")
        
        await self.exit_stack.aclose()
        print("🧹 Cleaned up all connections")
        print("🛡️ Guardrails session terminated safely")

async def main():
    """Main entry point for the financial chatbot."""
    chatbot = FinancialChatBot()
    try:
        print("🚀 Starting Financial MCP Chatbot with Enhanced Guardrails...")
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Main execution error: {e}")
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
