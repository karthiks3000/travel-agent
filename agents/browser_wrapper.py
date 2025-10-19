"""
Generic Nova Act browser wrapper for handling local vs AgentCore browser sessions
"""
import os
from nova_act import NovaAct
from typing import List, Dict, Any
from datetime import datetime


class BrowserWrapper:
    """Ultra-simple generic Nova Act session management for local vs AgentCore"""
    
    def __init__(self, api_key, use_agentcore_browser=False, region="us-east-1"):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Nova Act API key is required")
        self.use_agentcore_browser = use_agentcore_browser
        self.region = region
        
        # Ensure Playwright modules are installed automatically
        os.environ['NOVA_ACT_SKIP_PLAYWRIGHT_INSTALL'] = 'true'
    
    def execute_instructions(self, starting_page: str, instructions: List[str], 
                           extraction_instruction: str, result_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic method that:
        1. Creates Nova Act session (local or AgentCore)
        2. Navigates to starting page  
        3. Executes each instruction in sequence
        4. Extracts results using extraction_instruction
        """
        print(f"🔍 Starting browser session: {starting_page}")
        
        try:
            if self.use_agentcore_browser:
                return self._execute_with_agentcore_browser(starting_page, instructions, extraction_instruction, result_schema)
            else:
                return self._execute_with_local_browser(starting_page, instructions, extraction_instruction, result_schema)
                    
        except Exception as e:
            print(f"❌ Browser session error: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_with_local_browser(self, starting_page: str, instructions: List[str], 
                                   extraction_instruction: str, result_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser automation with local Nova Act session"""
        print(f"   Using local browser")
        
        with NovaAct(
            starting_page=starting_page,
            headless=False,
            user_agent="TravelAgent/1.0 (NovaAct)",
            nova_act_api_key=self.api_key,
            ignore_https_errors=True
        ) as nova:
            # Execute each instruction sequentially
            for i, instruction in enumerate(instructions, 1):
                print(f"   Step {i}: {instruction}")
                nova.act(instruction)
            
            # Extract structured results
            print(f"   Extracting results...")
            result = nova.act(extraction_instruction, schema=result_schema)
            
            if result.matches_schema:
                print(f"✅ Successfully extracted structured results")
                return result.parsed_response
            else:
                print("⚠️  Schema validation failed, returning raw response")
                return {
                    "error": "Schema validation failed",
                    "raw_response": result.response[:500],  # First 500 chars
                    "timestamp": datetime.now().isoformat()
                }
    
    def _execute_with_agentcore_browser(self, starting_page: str, instructions: List[str], 
                                       extraction_instruction: str, result_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser automation with AgentCore browser session"""
        print(f"   Using AgentCore Browser Tool (region: {self.region})")
        
        try:
            from bedrock_agentcore.tools.browser_client import browser_session
            
            print("🌐 Creating AgentCore browser session...")
            with browser_session(self.region) as client:
                ws_url, headers = client.generate_ws_headers()
                print("✅ AgentCore browser session established")
                
                with NovaAct(
                    cdp_endpoint_url=ws_url,
                    cdp_headers=headers,
                    preview={"playwright_actuation": True},
                    nova_act_api_key=self.api_key,
                    ignore_https_errors=True,  # SSL fix for AgentCore
                    starting_page=starting_page
                ) as nova:
                    # Execute each instruction sequentially within context
                    for i, instruction in enumerate(instructions, 1):
                        print(f"   Step {i}: {instruction}")
                        nova.act(instruction)
                    
                    # Extract structured results within context
                    print(f"   Extracting results...")
                    result = nova.act(extraction_instruction, schema=result_schema)
                    
                    if result.matches_schema:
                        print(f"✅ Successfully extracted structured results")
                        return result.parsed_response
                    else:
                        print("⚠️  Schema validation failed, returning raw response")
                        return {
                            "error": "Schema validation failed",
                            "raw_response": result.response[:500],  # First 500 chars
                            "timestamp": datetime.now().isoformat()
                        }
                
        except ImportError:
            print("❌ bedrock_agentcore not installed. Run: pip install bedrock-agentcore")
            raise
        except Exception as e:
            print(f"❌ AgentCore browser error: {str(e)}")
            raise
