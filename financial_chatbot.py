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
    An MCP-powered chatbot specialized for financial data analysis.
    """

    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        self.available_resources: List[str] = []
        self.available_prompts: List[str] = []

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
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
        """Get content from a resource."""
        try:
            # Find the session that provides this resource
            for session in self.sessions:
                try:
                    result = await session.read_resource(resource_uri)
                    return result.contents[0].text if result.contents else "No content available"
                except Exception:
                    continue
            return f"Resource not found: {resource_uri}"
        except Exception as e:
            return f"Error retrieving resource: {str(e)}"

    async def execute_prompt(self, prompt_name: str, arguments: Dict[str, str]) -> str:
        """Execute a prompt template with given arguments."""
        try:
            # Find the session that provides this prompt
            for session in self.sessions:
                try:
                    result = await session.get_prompt(prompt_name, arguments)
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
        """List all available prompts."""
        if not self.available_prompts:
            return "No prompts available."
        
        content = "Available prompts:\n"
        for prompt in self.available_prompts:
            content += f"- {prompt}\n"
        content += "\nUsage: /prompt <name> <arg1=value1> <arg2=value2>"
        return content

    def parse_prompt_command(self, user_input: str) -> tuple:
        """Parse prompt command from user input."""
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
                arguments[key] = value
        
        return prompt_name, arguments
    
    async def process_query(self, query):
        """Process a user query using available tools."""
        messages = [{'role':'user', 'content':query}]
        response = self.anthropic.messages.create(
            max_tokens = 4096,
            model = 'claude-3-5-sonnet-20241022', 
            tools = self.available_tools,
            messages = messages
        )
        
        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type =='text':
                    print(content.text)
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
                    
                    # Call a tool using the appropriate session
                    try:
                        session = self.tool_to_session[tool_name]
                        result = await session.call_tool(tool_name, arguments=tool_args)
                        print(f"✅ Tool result received")
                        
                        messages.append({"role": "user", 
                                          "content": [
                                              {
                                                  "type": "tool_result",
                                                  "tool_use_id":tool_id,
                                                  "content": result.content
                                              }
                                          ]
                                        })
                    except Exception as e:
                        error_msg = f"Error calling tool {tool_name}: {str(e)}"
                        print(f"❌ {error_msg}")
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
                        tools = self.available_tools,
                        messages = messages
                    ) 
                    
                    if(len(response.content) == 1 and response.content[0].type == "text"):
                        print(response.content[0].text)
                        process_query= False

    async def chat_loop(self):
        """Run an interactive chat loop with financial commands."""
        print("\n💰 Financial MCP Chatbot Started!")
        print("=" * 50)
        print("Available commands:")
        print("📊 Regular queries: Ask about stocks, markets, analysis")
        print("📁 Resources: @portfolios, @<filename>")
        print("📝 Prompts: /prompts, /prompt <name> <args>")
        print("❌ Exit: type 'quit'")
        print("=" * 50)
        
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
                        print("Invalid prompt format. Use: /prompt <name> <arg1=value1>")
                    continue
                
                # Regular query processing
                await self.process_query(query)
                        
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                logger.error(f"Chat loop error: {e}")

    async def cleanup(self):
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()
        print("🧹 Cleaned up all connections")

async def main():
    """Main entry point for the financial chatbot."""
    chatbot = FinancialChatBot()
    try:
        print("🚀 Starting Financial MCP Chatbot...")
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Main execution error: {e}")
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
