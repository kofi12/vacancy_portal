# AI Tools Integration: Exposing API Endpoints as AI Tools

## Overview

Transform your Vacancy Portal API endpoints into AI-callable tools that can be invoked by AI models through MCP (Model Context Protocol) or similar AI tool protocols.

## Architecture for AI Tools

### **High-Level Design**

```mermaid
AI Model → MCP Client → MCP Server → API Tools → Your Backend API
```

### **Tool Definition Structure**

```python
# Each API endpoint becomes an AI tool with:
{
    "name": "get_vacancy_status",
    "description": "Get vacancy status for organizations user is subscribed to",
    "parameters": {
        "user_id": {"type": "integer", "description": "User ID"},
        "organization_ids": {"type": "array", "description": "Optional specific organization IDs"}
    },
    "returns": {
        "type": "object",
        "properties": {
            "organizations": "array of organization vacancy data"
        }
    }
}
```

## Implementation Plan

### **Phase 1: API Tool Definitions (Week 1)**

#### **1.1 Core Tool Categories**

##### **Tenant Management Tools**

```python
# tools/tenant_tools.py
TENANT_TOOLS = [
    {
        "name": "get_tenant_info",
        "description": "Get detailed information about a specific tenant",
        "parameters": {
            "tenant_id": {"type": "integer", "required": True},
            "include_documents": {"type": "boolean", "default": False}
        },
        "endpoint": "/api/tenants/tenant/{tenant_id}",
        "method": "GET"
    },
    {
        "name": "create_tenant",
        "description": "Create a new tenant in the system",
        "parameters": {
            "name": {"type": "string", "required": True},
            "organization_id": {"type": "integer", "required": True},
            "admission_date": {"type": "string", "format": "date"},
            "waitlist": {"type": "boolean", "default": False}
        },
        "endpoint": "/api/tenants/create-tenant",
        "method": "POST"
    },
    {
        "name": "update_tenant",
        "description": "Update tenant information",
        "parameters": {
            "tenant_id": {"type": "integer", "required": True},
            "name": {"type": "string"},
            "admission_date": {"type": "string", "format": "date"},
            "discharge_date": {"type": "string", "format": "date"},
            "waitlist": {"type": "boolean"}
        },
        "endpoint": "/api/tenants/update/{tenant_id}",
        "method": "PUT"
    },
    {
        "name": "get_waitlist_tenants",
        "description": "Get all tenants currently on waitlist",
        "parameters": {
            "organization_id": {"type": "integer", "required": False}
        },
        "endpoint": "/api/tenants/waitlist",
        "method": "GET"
    },
    {
        "name": "admit_tenant",
        "description": "Admit a tenant from waitlist to active status",
        "parameters": {
            "tenant_id": {"type": "integer", "required": True},
            "admission_date": {"type": "string", "format": "date", "required": True}
        },
        "endpoint": "/api/tenants/admit/{tenant_id}",
        "method": "POST"
    },
    {
        "name": "discharge_tenant",
        "description": "Discharge a tenant from the facility",
        "parameters": {
            "tenant_id": {"type": "integer", "required": True},
            "discharge_date": {"type": "string", "format": "date", "required": True}
        },
        "endpoint": "/api/tenants/discharge/{tenant_id}",
        "method": "POST"
    }
]
```

##### **Organization Management Tools**

```python
# tools/organization_tools.py
ORGANIZATION_TOOLS = [
    {
        "name": "get_organization_info",
        "description": "Get detailed information about a specific organization",
        "parameters": {
            "organization_id": {"type": "integer", "required": True}
        },
        "endpoint": "/api/orgs/org/{organization_id}",
        "method": "GET"
    },
    {
        "name": "get_user_organizations",
        "description": "Get all organizations that a user is subscribed to",
        "parameters": {
            "user_id": {"type": "integer", "required": True}
        },
        "endpoint": "/api/orgs/user/{user_id}/organizations",
        "method": "GET"
    },
    {
        "name": "get_vacancy_status",
        "description": "Get vacancy status for organizations",
        "parameters": {
            "organization_ids": {"type": "array", "items": {"type": "integer"}},
            "user_id": {"type": "integer", "required": True}
        },
        "endpoint": "/api/orgs/vacancy-status",
        "method": "GET"
    },
    {
        "name": "get_all_organizations",
        "description": "Get list of all available organizations",
        "parameters": {
            "include_vacancy": {"type": "boolean", "default": True}
        },
        "endpoint": "/api/orgs/all-orgs",
        "method": "GET"
    }
]
```

##### **User Management Tools**

```python
# tools/user_tools.py
USER_TOOLS = [
    {
        "name": "get_user_profile",
        "description": "Get user profile information",
        "parameters": {
            "user_id": {"type": "integer", "required": True}
        },
        "endpoint": "/api/users/user/{user_id}",
        "method": "GET"
    },
    {
        "name": "update_user_profile",
        "description": "Update user profile information",
        "parameters": {
            "user_id": {"type": "integer", "required": True},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "community_org": {"type": "string"}
        },
        "endpoint": "/api/users/update/{user_id}",
        "method": "PUT"
    },
    {
        "name": "get_user_subscriptions",
        "description": "Get organizations that a user is subscribed to",
        "parameters": {
            "user_id": {"type": "integer", "required": True}
        },
        "endpoint": "/api/users/{user_id}/subscriptions",
        "method": "GET"
    }
]
```

##### **Document Management Tools**

```python
# tools/document_tools.py
DOCUMENT_TOOLS = [
    {
        "name": "upload_tenant_document",
        "description": "Upload a document for a specific tenant",
        "parameters": {
            "tenant_id": {"type": "integer", "required": True},
            "file": {"type": "file", "required": True},
            "document_type": {"type": "string", "required": True}
        },
        "endpoint": "/api/tenants/upload-pdf/{tenant_id}",
        "method": "POST"
    },
    {
        "name": "download_tenant_document",
        "description": "Download a document for a specific tenant",
        "parameters": {
            "tenant_id": {"type": "integer", "required": True}
        },
        "endpoint": "/api/tenants/download-pdf/{tenant_id}",
        "method": "GET"
    },
    {
        "name": "get_tenant_documents",
        "description": "Get list of documents for a tenant",
        "parameters": {
            "tenant_id": {"type": "integer", "required": True}
        },
        "endpoint": "/api/tenants/{tenant_id}/documents",
        "method": "GET"
    }
]
```

### **Phase 2: MCP Server Implementation (Week 2)**

#### **2.1 MCP Server Setup**

```python
# infrastructure/ai/mcp_server.py
from mcp import Server
from mcp.types import Tool, TextContent
from typing import Dict, Any, List
import httpx
import json

class VacancyPortalMCPServer:
    def __init__(self, api_base_url: str, api_token: str):
        self.server = Server("vacancy-portal")
        self.api_base_url = api_base_url
        self.api_token = api_token
        self.http_client = httpx.AsyncClient()
        self._register_tools()
    
    def _register_tools(self):
        """Register all API tools with MCP server"""
        
        # Register tenant tools
        for tool in TENANT_TOOLS:
            self.server.tool(
                tool["name"],
                tool["description"],
                self._create_tool_handler(tool)
            )
        
        # Register organization tools
        for tool in ORGANIZATION_TOOLS:
            self.server.tool(
                tool["name"],
                tool["description"],
                self._create_tool_handler(tool)
            )
        
        # Register user tools
        for tool in USER_TOOLS:
            self.server.tool(
                tool["name"],
                tool["description"],
                self._create_tool_handler(tool)
            )
        
        # Register document tools
        for tool in DOCUMENT_TOOLS:
            self.server.tool(
                tool["name"],
                tool["description"],
                self._create_tool_handler(tool)
            )
    
    def _create_tool_handler(self, tool_def: Dict[str, Any]):
        """Create a handler function for a tool"""
        
        async def tool_handler(**kwargs):
            try:
                # Prepare the request
                endpoint = tool_def["endpoint"]
                method = tool_def["method"]
                
                # Replace path parameters
                for param_name, param_value in kwargs.items():
                    if f"{{{param_name}}}" in endpoint:
                        endpoint = endpoint.replace(f"{{{param_name}}}", str(param_value))
                
                # Prepare headers
                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }
                
                # Make the API call
                url = f"{self.api_base_url}{endpoint}"
                
                if method == "GET":
                    # Handle query parameters
                    query_params = {k: v for k, v in kwargs.items() 
                                  if f"{{{k}}}" not in tool_def["endpoint"]}
                    response = await self.http_client.get(url, headers=headers, params=query_params)
                
                elif method == "POST":
                    # Handle body parameters
                    body_data = {k: v for k, v in kwargs.items() 
                               if f"{{{k}}}" not in tool_def["endpoint"] and k != "file"}
                    response = await self.http_client.post(url, headers=headers, json=body_data)
                
                elif method == "PUT":
                    body_data = {k: v for k, v in kwargs.items() 
                               if f"{{{k}}}" not in tool_def["endpoint"]}
                    response = await self.http_client.put(url, headers=headers, json=body_data)
                
                elif method == "DELETE":
                    response = await self.http_client.delete(url, headers=headers)
                
                # Handle response
                if response.status_code == 200:
                    return TextContent(
                        type="text",
                        text=json.dumps(response.json(), indent=2)
                    )
                else:
                    return TextContent(
                        type="text",
                        text=f"Error: {response.status_code} - {response.text}"
                    )
                    
            except Exception as e:
                return TextContent(
                    type="text",
                    text=f"Error executing tool {tool_def['name']}: {str(e)}"
                )
        
        return tool_handler
    
    async def start(self):
        """Start the MCP server"""
        await self.server.start()
    
    async def stop(self):
        """Stop the MCP server"""
        await self.http_client.aclose()
        await self.server.stop()
```

#### **2.2 Tool Registry Service**

```python
# application/services/tool_registry_service.py
from typing import Dict, List, Any
from domain.services.tenant_service import TenantService
from domain.services.organization_service import OrganizationService
from domain.services.user_service import UserService

class ToolRegistryService:
    def __init__(self, tenant_service: TenantService, 
                 org_service: OrganizationService,
                 user_service: UserService):
        self.tenant_service = tenant_service
        self.org_service = org_service
        self.user_service = user_service
    
    def get_available_tools(self, user_id: int) -> List[Dict[str, Any]]:
        """Get available tools based on user permissions"""
        user = self.user_service.get_user(user_id)
        available_tools = []
        
        # Add tools based on user role and permissions
        if user.role in ["admin", "owner"]:
            available_tools.extend(TENANT_TOOLS)
            available_tools.extend(ORGANIZATION_TOOLS)
            available_tools.extend(USER_TOOLS)
            available_tools.extend(DOCUMENT_TOOLS)
        
        elif user.role == "scworker":
            available_tools.extend(TENANT_TOOLS)
            available_tools.extend(ORGANIZATION_TOOLS)
            available_tools.extend(DOCUMENT_TOOLS)
        
        else:  # pending or basic user
            available_tools.extend([
                tool for tool in ORGANIZATION_TOOLS 
                if tool["name"] in ["get_organization_info", "get_vacancy_status"]
            ])
        
        return available_tools
    
    def validate_tool_access(self, user_id: int, tool_name: str) -> bool:
        """Validate if user has access to specific tool"""
        available_tools = self.get_available_tools(user_id)
        return any(tool["name"] == tool_name for tool in available_tools)
```

### **Phase 3: AI Query Processing (Week 3)**

#### **3.1 Natural Language to Tool Mapping**

```python
# application/services/ai_query_processor.py
from typing import Dict, List, Tuple, Optional
import re
from dataclasses import dataclass

@dataclass
class ToolCall:
    tool_name: str
    parameters: Dict[str, Any]
    confidence: float

class AIQueryProcessor:
    def __init__(self, tool_registry_service: ToolRegistryService):
        self.tool_registry = tool_registry_service
        self.intent_patterns = self._build_intent_patterns()
    
    def _build_intent_patterns(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build patterns for intent recognition"""
        return {
            "get_vacancy_status": [
                (r"vacancy status", "get_vacancy_status"),
                (r"available beds", "get_vacancy_status"),
                (r"how many spots", "get_vacancy_status"),
                (r"capacity", "get_vacancy_status"),
                (r"openings", "get_vacancy_status")
            ],
            "get_tenant_info": [
                (r"tenant (?:named |called )?(\w+)", "get_tenant_info"),
                (r"resident (?:named |called )?(\w+)", "get_tenant_info"),
                (r"(\w+) (?:tenant|resident)", "get_tenant_info")
            ],
            "get_waitlist_tenants": [
                (r"waitlist", "get_waitlist_tenants"),
                (r"waiting list", "get_waitlist_tenants"),
                (r"people waiting", "get_waitlist_tenants")
            ],
            "get_organization_info": [
                (r"organization (?:named |called )?(\w+)", "get_organization_info"),
                (r"facility (?:named |called )?(\w+)", "get_organization_info"),
                (r"RCF (?:named |called )?(\w+)", "get_organization_info")
            ]
        }
    
    def process_query(self, user_id: int, query: str) -> List[ToolCall]:
        """Process natural language query and return tool calls"""
        query_lower = query.lower()
        tool_calls = []
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern, tool_name in patterns:
                matches = re.findall(pattern, query_lower)
                if matches:
                    # Validate user has access to this tool
                    if self.tool_registry.validate_tool_access(user_id, tool_name):
                        tool_call = self._create_tool_call(tool_name, matches, user_id)
                        if tool_call:
                            tool_calls.append(tool_call)
        
        return tool_calls
    
    def _create_tool_call(self, tool_name: str, matches: List[str], user_id: int) -> Optional[ToolCall]:
        """Create a tool call based on the tool name and matches"""
        
        if tool_name == "get_vacancy_status":
            return ToolCall(
                tool_name=tool_name,
                parameters={"user_id": user_id},
                confidence=0.9
            )
        
        elif tool_name == "get_tenant_info":
            if matches:
                tenant_name = matches[0]
                return ToolCall(
                    tool_name=tool_name,
                    parameters={"tenant_name": tenant_name},
                    confidence=0.8
                )
        
        elif tool_name == "get_waitlist_tenants":
            return ToolCall(
                tool_name=tool_name,
                parameters={},
                confidence=0.9
            )
        
        elif tool_name == "get_organization_info":
            if matches:
                org_name = matches[0]
                return ToolCall(
                    tool_name=tool_name,
                    parameters={"organization_name": org_name},
                    confidence=0.8
                )
        
        return None
```

#### **3.2 AI Response Generator**

```python
# application/services/ai_response_generator.py
from typing import List, Dict, Any
from application.services.ai_query_processor import ToolCall

class AIResponseGenerator:
    def __init__(self, mcp_server: VacancyPortalMCPServer):
        self.mcp_server = mcp_server
    
    async def generate_response(self, user_id: int, tool_calls: List[ToolCall]) -> str:
        """Generate natural language response from tool calls"""
        
        if not tool_calls:
            return "I'm sorry, I couldn't understand your request. Try asking about vacancy status, tenant information, or waitlist status."
        
        responses = []
        
        for tool_call in tool_calls:
            try:
                # Execute the tool call
                result = await self.mcp_server.execute_tool(tool_call.tool_name, tool_call.parameters)
                
                # Format the response
                formatted_response = self._format_tool_response(tool_call.tool_name, result)
                responses.append(formatted_response)
                
            except Exception as e:
                responses.append(f"Sorry, I couldn't get that information: {str(e)}")
        
        # Combine responses
        if len(responses) == 1:
            return responses[0]
        else:
            return "\n\n".join(responses)
    
    def _format_tool_response(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format tool response into natural language"""
        
        if tool_name == "get_vacancy_status":
            return self._format_vacancy_status(result)
        
        elif tool_name == "get_tenant_info":
            return self._format_tenant_info(result)
        
        elif tool_name == "get_waitlist_tenants":
            return self._format_waitlist_status(result)
        
        elif tool_name == "get_organization_info":
            return self._format_organization_info(result)
        
        else:
            return str(result)
    
    def _format_vacancy_status(self, data: Dict[str, Any]) -> str:
        """Format vacancy status response"""
        if "organizations" not in data:
            return "I couldn't retrieve vacancy status information."
        
        orgs = data["organizations"]
        if not orgs:
            return "You don't have any subscribed organizations."
        
        response = "Here's the vacancy status for your organizations:\n\n"
        
        for org in orgs:
            name = org.get("business_name", "Unknown")
            active_tenants = org.get("active_tenants", 0)
            total_beds = org.get("number_of_beds", "Unlimited")
            available_beds = org.get("available_beds", "Unknown")
            
            if total_beds == "Unlimited":
                response += f"• {name}: {active_tenants} active tenants, unlimited capacity\n"
            else:
                response += f"• {name}: {active_tenants} active tenants, {available_beds} available beds\n"
        
        return response
    
    def _format_tenant_info(self, data: Dict[str, Any]) -> str:
        """Format tenant information response"""
        if not data:
            return "I couldn't find that tenant."
        
        name = data.get("name", "Unknown")
        status = "Active" if data.get("discharge_date") is None else "Discharged"
        waitlist = "On waitlist" if data.get("waitlist") else "Not on waitlist"
        admission_date = data.get("admission_date", "Not specified")
        
        return f"Tenant Information:\n• Name: {name}\n• Status: {status}\n• Waitlist: {waitlist}\n• Admission Date: {admission_date}"
    
    def _format_waitlist_status(self, data: Dict[str, Any]) -> str:
        """Format waitlist status response"""
        if "waitlist" not in data:
            return "I couldn't retrieve waitlist information."
        
        waitlist = data["waitlist"]
        if not waitlist:
            return "There are currently no tenants on the waitlist."
        
        response = f"There are {len(waitlist)} tenants on the waitlist:\n\n"
        
        for tenant in waitlist[:10]:  # Show first 10
            name = tenant.get("name", "Unknown")
            org_name = tenant.get("organization_name", "Unknown")
            response += f"• {name} (waiting for {org_name})\n"
        
        if len(waitlist) > 10:
            response += f"\n... and {len(waitlist) - 10} more."
        
        return response
```

### **Phase 4: API Integration (Week 4)**

#### **4.1 AI Endpoints**

```python
# presentation/controllers/ai_controller.py
from fastapi import APIRouter, Depends, HTTPException
from application.services.ai_query_processor import AIQueryProcessor
from application.services.ai_response_generator import AIResponseGenerator
from application.dto.ai_dto import AIQueryRequest, AIQueryResponse
from presentation.dependencies import get_current_user_with_scopes

ai_router = APIRouter(prefix='/api/ai')

@ai_router.post('/query', response_model=AIQueryResponse)
async def process_ai_query(
    request: AIQueryRequest,
    current_user = Depends(get_current_user_with_scopes),
    query_processor: AIQueryProcessor = Depends(),
    response_generator: AIResponseGenerator = Depends()
):
    """Process natural language query and return AI response"""
    
    try:
        # Process the query to get tool calls
        tool_calls = query_processor.process_query(current_user.id, request.query)
        
        # Generate response from tool calls
        response_text = await response_generator.generate_response(current_user.id, tool_calls)
        
        return AIQueryResponse(
            query=request.query,
            response=response_text,
            tool_calls_used=[call.tool_name for call in tool_calls]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@ai_router.get('/tools')
async def get_available_tools(
    current_user = Depends(get_current_user_with_scopes),
    tool_registry: ToolRegistryService = Depends()
):
    """Get available AI tools for the current user"""
    
    tools = tool_registry.get_available_tools(current_user.id)
    
    return {
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool.get("parameters", {})
            }
            for tool in tools
        ]
    }
```

#### **4.2 DTOs for AI**

```python
# application/dto/ai_dto.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AIQueryRequest:
    query: str
    context: Optional[Dict[str, Any]] = None

@dataclass
class AIQueryResponse:
    query: str
    response: str
    tool_calls_used: List[str]
    confidence: Optional[float] = None
```

### **Phase 5: Frontend Integration (Week 5)**

#### **5.1 AI Chat Component**

```typescript
// components/AIChat.tsx
import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../services/api';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  toolCalls?: string[];
}

export const AIChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const scrollViewRef = useRef<ScrollView>(null);

  const queryMutation = useMutation({
    mutationFn: (query: string) => api.queryAI(query),
    onSuccess: (data) => {
      const aiMessage: Message = {
        id: Date.now().toString(),
        text: data.response,
        isUser: false,
        timestamp: new Date(),
        toolCalls: data.tool_calls_used
      };
      setMessages(prev => [...prev, aiMessage]);
    },
    onError: (error) => {
      Alert.alert('Error', 'Failed to process your query. Please try again.');
    }
  });

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentQuery = inputText;
    setInputText('');

    // Process with AI
    queryMutation.mutate(currentQuery);
  };

  const handleVoiceInput = async () => {
    // Implement voice input using Expo Speech
    // This would integrate with the device's speech recognition
  };

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  return (
    <View style={styles.container}>
      <ScrollView 
        ref={scrollViewRef}
        style={styles.messagesContainer}
        showsVerticalScrollIndicator={false}
      >
        {messages.map(message => (
          <View key={message.id} style={[
            styles.message,
            message.isUser ? styles.userMessage : styles.aiMessage
          ]}>
            <Text style={styles.messageText}>{message.text}</Text>
            {message.toolCalls && message.toolCalls.length > 0 && (
              <Text style={styles.toolCallsText}>
                Used: {message.toolCalls.join(', ')}
              </Text>
            )}
            <Text style={styles.timestamp}>
              {message.timestamp.toLocaleTimeString()}
            </Text>
          </View>
        ))}
        
        {queryMutation.isPending && (
          <View style={styles.aiMessage}>
            <Text style={styles.thinkingText}>Thinking...</Text>
          </View>
        )}
      </ScrollView>
      
      <View style={styles.inputContainer}>
        <TouchableOpacity 
          style={styles.voiceButton}
          onPress={handleVoiceInput}
        >
          <Text style={styles.voiceButtonText}>🎤</Text>
        </TouchableOpacity>
        
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Ask about vacancy status, tenants, or waitlist..."
          multiline
          maxLength={500}
        />
        
        <TouchableOpacity 
          style={[styles.sendButton, queryMutation.isPending && styles.sendButtonDisabled]}
          onPress={sendMessage}
          disabled={queryMutation.isPending}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  messagesContainer: {
    flex: 1,
    padding: 16,
  },
  message: {
    marginBottom: 12,
    padding: 12,
    borderRadius: 12,
    maxWidth: '80%',
  },
  userMessage: {
    backgroundColor: '#007AFF',
    alignSelf: 'flex-end',
  },
  aiMessage: {
    backgroundColor: '#E5E5EA',
    alignSelf: 'flex-start',
  },
  messageText: {
    fontSize: 16,
    color: '#000',
  },
  toolCallsText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontStyle: 'italic',
  },
  timestamp: {
    fontSize: 10,
    color: '#999',
    marginTop: 4,
  },
  thinkingText: {
    fontStyle: 'italic',
    color: '#666',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  voiceButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  voiceButtonText: {
    fontSize: 20,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    maxHeight: 100,
  },
  sendButton: {
    width: 60,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: '#999',
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
});
```

#### **5.2 AI Service Integration**

```typescript
// services/aiService.ts
import { api } from './api';

export interface AIQueryRequest {
  query: string;
  context?: Record<string, any>;
}

export interface AIQueryResponse {
  query: string;
  response: string;
  tool_calls_used: string[];
  confidence?: number;
}

export interface AITool {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export class AIService {
  static async queryAI(request: AIQueryRequest): Promise<AIQueryResponse> {
    const response = await api.post('/ai/query', request);
    return response.data;
  }

  static async getAvailableTools(): Promise<AITool[]> {
    const response = await api.get('/ai/tools');
    return response.data.tools;
  }

  static async getQuerySuggestions(): Promise<string[]> {
    return [
      "Can you give the vacancy status of every organization or RCF that I am subscribed to?",
      "How many tenants are currently on the waitlist for Maple Gardens?",
      "When was John Smith admitted to Sunshine Care?",
      "Which organizations have the most available beds right now?",
      "Show me all active tenants in my organizations"
    ];
  }
}
```

## Example Usage Scenarios

### **Scenario 1: Vacancy Status Query**

**User Input**: "Can you give the vacancy status of every organization or RCF that I am subscribed to?"

**AI Processing**:

1. Intent Recognition: `get_vacancy_status`
2. Tool Call: `get_vacancy_status(user_id=123)`
3. API Call: `GET /api/orgs/vacancy-status?user_id=123`
4. Response Formatting: Natural language summary

**AI Response**:

```text
Here's the vacancy status for your organizations:

• Maple Gardens: 45 active tenants, 5 available beds
• Sunshine Care: 32 active tenants, 18 available beds
• Golden Years: 28 active tenants, unlimited capacity
```

### **Scenario 2: Tenant Information Query**

**User Input**: "When was John Smith admitted to Sunshine Care?"

**AI Processing**:

1. Intent Recognition: `get_tenant_info`
2. Entity Extraction: `tenant_name="John Smith"`
3. Tool Call: `get_tenant_info(tenant_name="John Smith")`
4. API Call: `GET /api/tenants/tenant?name=John Smith`
5. Response Formatting: Natural language answer

**AI Response**:

```text
Tenant Information:
• Name: John Smith
• Status: Active
• Waitlist: Not on waitlist
• Admission Date: 2024-01-15
```

## Benefits of This Approach

### **1. Direct API Integration**

- AI tools directly call your existing API endpoints
- No need to duplicate business logic
- Consistent data and behavior

### **2. Scalable Architecture**

- Easy to add new tools by defining new API endpoints
- Permission-based tool access
- Modular design

### **3. Natural Language Processing**

- Intent recognition for common queries
- Entity extraction from natural language
- Context-aware responses

### **4. Cross-Platform Support**

- Works with any AI model that supports MCP
- Consistent API across all platforms
- Easy to extend for new AI providers

This approach transforms your API into AI-callable tools while maintaining the clean architecture and providing a seamless user experience across mobile and web platforms.
