# Strategic Roadmap: Vacancy Portal Evolution

## Vision Overview

Transform the Vacancy Portal into a modern, AI-powered platform with:

1. **Clean Architecture Backend** - Maintainable, scalable, and testable with Google SSO integration
2. **Cross-Platform Frontend** - React Native mobile app + React web admin
3. **AI-Powered Conversations** - MCP integration for natural language queries

## Phase 1: Backend Architecture Refactoring (Weeks 1-6)

### **Current Status**

- ✅ Architecture analysis complete
- ✅ Design documents created
- ✅ Implementation plan ready
- ✅ Google SSO integration strategy defined

### **Implementation Timeline**

#### **Week 1-2: Foundation & Domain Layer**

```bash
# Directory structure
mkdir -p domain/{entities,repositories,services,exceptions,value_objects}
mkdir -p application/{use_cases,dto,interfaces,services}
mkdir -p infrastructure/{database,auth,file_storage,external}
mkdir -p presentation/{controllers,middleware,serializers,validators}
```

**Deliverables:**

- Base entity classes
- Domain entities (Tenant, User, Organization) with authentication support
- Repository interfaces
- Domain services including authentication services
- Domain exceptions including authentication exceptions

#### **Week 3-4: Application & Infrastructure Layers**

**Deliverables:**

- Application services for all operations including authentication services
- DTOs for API contracts including authentication DTOs
- Repository implementations
- Google SSO adapter and JWT token service
- Authorization service implementation
- Dependency injection container

#### **Week 5-6: Presentation Layer & Migration**

**Deliverables:**

- Refactored controllers with authentication middleware
- Google SSO integration in Clean Architecture
- Gradual migration of endpoints with feature flags
- Comprehensive testing including authentication tests
- Documentation updates

### **Google SSO Integration Strategy**

#### **Preserve Existing Functionality**

- Keep current Google SSO endpoints working during migration
- Implement feature flags for safe deployment
- Maintain backward compatibility

#### **Clean Architecture Integration**

- Google SSO adapter in infrastructure layer
- JWT token service with domain abstractions
- Scope-based authorization service
- Authentication use cases in application layer

#### **Migration Approach**

```python
# Feature flag controlled deployment
if FeatureFlags.use_clean_architecture_auth():
    app.include_router(auth_controller.auth_router, prefix="/api/v2")
else:
    app.include_router(old_auth.auth_router, prefix="/api/v1")
```

### **Success Criteria**

- ✅ All endpoints working with new architecture
- ✅ Google SSO integration preserved and enhanced
- ✅ 80%+ test coverage including authentication
- ✅ Zero breaking changes for existing clients
- ✅ Performance maintained or improved

---

## Phase 2: Frontend Development (Weeks 7-12)

### **Mobile App (React Native + Expo)**

#### **Week 7-8: Project Setup & Core Architecture**

```bash
# Create React Native app with Expo
npx create-expo-app VacancyPortalMobile --template blank-typescript
cd VacancyPortalMobile
npm install @react-navigation/native @react-navigation/stack
npm install @tanstack/react-query axios
npm install @react-native-async-storage/async-storage
```

**Architecture:**

```mermaid
src/
├── components/          # Reusable UI components
├── screens/            # Screen components
├── navigation/         # Navigation configuration
├── services/           # API service layer
├── hooks/              # Custom React hooks
├── store/              # State management (Zustand/Redux)
├── types/              # TypeScript type definitions
└── utils/              # Utility functions
```

#### **Week 9-10: Core Features**

**Screens to Implement:**

```typescript
// Authentication screens
- LoginScreen (Google SSO integration)
- OnboardingScreen (role selection)
- ProfileScreen (user management)

// Core functionality screens
- OrganizationListScreen
- OrganizationDetailScreen
- TenantListScreen
- TenantDetailScreen
- WaitlistScreen
- AddTenantScreen
```

#### **Google SSO Integration in Mobile**

```typescript
// services/authService.ts
import { GoogleSignin } from '@react-native-google-signin/google-signin';

export class AuthService {
  constructor() {
    GoogleSignin.configure({
      webClientId: 'your-google-client-id',
      offlineAccess: true,
    });
  }

  async signInWithGoogle() {
    try {
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();
      
      // Send to backend for JWT token
      const response = await api.post('/api/v2/auth/google/callback', {
        googleToken: userInfo.idToken,
      });
      
      return response.data;
    } catch (error) {
      throw new Error('Google sign-in failed');
    }
  }

  async validateToken(token: string) {
    const response = await api.post('/api/v2/auth/validate-token', {
      token,
    });
    return response.data;
  }
}
```

#### **Week 11-12: Advanced Features & Polish**

**Features:**

- Real-time updates with WebSocket integration
- Offline support with data synchronization
- Push notifications for vacancy updates
- Advanced search and filtering
- User role management
- Organization management for owners

### **Web Admin Platform (React + TypeScript)**

#### **Week 13-14: Admin Dashboard**

```typescript
// Admin-specific features
- Comprehensive dashboard with analytics
- Bulk operations for tenant management
- Advanced reporting and exports
- User management and role assignment
- Organization configuration
- System settings and configuration
```

#### **Week 15-16: Advanced Admin Features**

**Features:**

- Real-time analytics and monitoring
- Advanced search and filtering
- Bulk import/export functionality
- Audit logging and compliance
- System health monitoring
- Performance optimization

### **Success Criteria**

- ✅ Mobile app works on iOS and Android
- ✅ Web admin provides full management capabilities
- ✅ Google SSO integration works seamlessly
- ✅ Shared codebase for common functionality
- ✅ Responsive design and accessibility
- ✅ Offline support and data synchronization

---

## Phase 3: AI Integration with MCP (Weeks 17-20)

### **MCP (Model Context Protocol) Integration**

#### **Week 17: MCP Server Setup**

```python
# infrastructure/ai/mcp_server.py
from mcp import Server
from mcp.types import Tool, TextContent
from domain.services.tenant_service import TenantService
from domain.services.organization_service import OrganizationService

class VacancyPortalMCPServer:
    def __init__(self, tenant_service: TenantService, org_service: OrganizationService):
        self.server = Server("vacancy-portal")
        self.tenant_service = tenant_service
        self.org_service = org_service
        self._register_tools()
    
    def _register_tools(self):
        self.server.tool(
            "get_vacancy_status",
            "Get vacancy status for organizations user is subscribed to",
            self.get_vacancy_status
        )
        
        self.server.tool(
            "get_tenant_info",
            "Get information about specific tenant",
            self.get_tenant_info
        )
        
        self.server.tool(
            "get_waitlist_status",
            "Get waitlist status for organizations",
            self.get_waitlist_status
        )
    
    async def get_vacancy_status(self, user_id: int) -> str:
        """Get vacancy status for user's subscribed organizations"""
        organizations = await self.org_service.get_user_organizations(user_id)
        results = []
        
        for org in organizations:
            tenants = await self.tenant_service.get_by_organization(org.id)
            active_count = len([t for t in tenants if t.is_active()])
            available_beds = org.number_of_beds - active_count if org.number_of_beds else "Unlimited"
            
            results.append(f"{org.business_name}: {active_count} active tenants, {available_beds} available beds")
        
        return "\n".join(results)
    
    async def get_tenant_info(self, tenant_name: str) -> str:
        """Get information about a specific tenant"""
        tenant = await self.tenant_service.get_tenant_by_name(tenant_name)
        if not tenant:
            return f"Tenant '{tenant_name}' not found"
        
        status = "Active" if tenant.is_active() else "Discharged"
        waitlist = "On waitlist" if tenant.is_on_waitlist() else "Not on waitlist"
        
        return f"Tenant: {tenant.name}\nStatus: {status}\nWaitlist: {waitlist}\nAdmission Date: {tenant.admission_date}"
```

#### **Week 18: AI Query Processing**

```python
# application/services/ai_query_service.py
from domain.services.tenant_service import TenantService
from domain.services.organization_service import OrganizationService
from infrastructure.ai.mcp_server import VacancyPortalMCPServer

class AIQueryService:
    def __init__(self, tenant_service: TenantService, org_service: OrganizationService):
        self.mcp_server = VacancyPortalMCPServer(tenant_service, org_service)
    
    async def process_query(self, user_id: int, query: str) -> str:
        """Process natural language query and return response"""
        # Extract intent and parameters from query
        intent = self._extract_intent(query)
        
        if intent == "vacancy_status":
            return await self.mcp_server.get_vacancy_status(user_id)
        elif intent == "tenant_info":
            tenant_name = self._extract_tenant_name(query)
            return await self.mcp_server.get_tenant_info(tenant_name)
        elif intent == "waitlist_status":
            return await self.mcp_server.get_waitlist_status(user_id)
        else:
            return "I'm sorry, I don't understand that query. Please try asking about vacancy status, tenant information, or waitlist status."
    
    def _extract_intent(self, query: str) -> str:
        """Extract intent from natural language query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["vacancy", "available", "beds", "capacity"]):
            return "vacancy_status"
        elif any(word in query_lower for word in ["tenant", "resident", "person"]):
            return "tenant_info"
        elif any(word in query_lower for word in ["waitlist", "waiting", "queue"]):
            return "waitlist_status"
        else:
            return "unknown"
    
    def _extract_tenant_name(self, query: str) -> str:
        """Extract tenant name from query"""
        # Simple extraction - in production, use NLP library
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() in ["tenant", "resident", "person"]:
                if i + 1 < len(words):
                    return words[i + 1]
        return ""
```

#### **Week 19: Voice Integration**

```python
# infrastructure/ai/voice_service.py
import speech_recognition as sr
from gtts import gTTS
import io

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def speech_to_text(self, audio_data) -> str:
        """Convert speech to text"""
        try:
            text = self.recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""
    
    def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech"""
        tts = gTTS(text=text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        return audio_buffer.getvalue()
```

#### **Week 20: Integration & Testing**

**Features:**

- Natural language processing for queries
- Voice input and output capabilities
- Context-aware responses
- Multi-turn conversations
- Integration with mobile and web interfaces
- Comprehensive testing and validation

### **Success Criteria**

- ✅ AI can understand and respond to natural language queries
- ✅ Voice integration works on mobile devices
- ✅ MCP tools are properly integrated with backend
- ✅ Context is maintained across conversations
- ✅ Performance is acceptable for real-time use

---

## Phase 4: Integration & Optimization (Weeks 21-24)

### **System Integration**

#### **Week 21: End-to-End Testing**

- Integration testing across all components
- Performance testing and optimization
- Security testing and validation
- User acceptance testing

#### **Week 22: Performance Optimization**

- Database query optimization
- Caching implementation
- API response time optimization
- Frontend performance optimization

#### **Week 23: Security & Compliance**

- Security audit and penetration testing
- Healthcare compliance validation
- Data privacy implementation
- Audit logging and monitoring

#### **Week 24: Production Deployment**

- Production environment setup
- CI/CD pipeline implementation
- Monitoring and alerting setup
- Documentation completion

### **Success Criteria**

- ✅ All systems integrated and working together
- ✅ Performance meets requirements
- ✅ Security and compliance validated
- ✅ Production deployment successful
- ✅ Monitoring and alerting operational

---

## Technology Stack Summary

### **Backend**

- **Framework**: FastAPI with Clean Architecture
- **Database**: PostgreSQL with SQLModel
- **Authentication**: Google SSO with JWT tokens
- **AI Integration**: MCP (Model Context Protocol)
- **Testing**: Pytest with comprehensive coverage

### **Frontend**

- **Mobile**: React Native with Expo
- **Web Admin**: React with TypeScript
- **State Management**: Redux Toolkit / Zustand
- **API Client**: React Query with Axios
- **UI Components**: Material-UI / Ant Design

### **Infrastructure**

- **Containerization**: Docker with Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus with Grafana
- **Logging**: Structured logging with ELK stack

---

## Risk Mitigation

### **Technical Risks**

- **Google SSO Integration**: Comprehensive testing and gradual migration
- **AI Integration Complexity**: Phased approach with MVP first
- **Performance Issues**: Early performance testing and optimization
- **Security Vulnerabilities**: Regular security audits and testing

### **Business Risks**

- **User Adoption**: Early user testing and feedback
- **Feature Creep**: Strict scope management and MVP focus
- **Timeline Delays**: Buffer time and parallel development
- **Resource Constraints**: Clear prioritization and resource allocation

---

## Success Metrics

### **Technical Metrics**

- **Performance**: API response time < 200ms
- **Reliability**: 99.9% uptime
- **Security**: Zero security incidents
- **Code Quality**: 90%+ test coverage

### **Business Metrics**

- **User Adoption**: 80%+ user satisfaction
- **Feature Usage**: 70%+ feature adoption rate
- **System Performance**: 50%+ improvement in user workflows
- **AI Integration**: 90%+ query accuracy

---

## Conclusion

This strategic roadmap provides a comprehensive plan for transforming the Vacancy Portal into a modern, AI-powered platform while preserving and enhancing your existing Google SSO integration. The phased approach ensures:

1. **Gradual Migration**: No disruption to existing functionality
2. **Clean Architecture**: Maintainable and scalable codebase
3. **AI Integration**: Natural language and voice capabilities
4. **Cross-Platform**: Mobile and web interfaces
5. **Security & Compliance**: Healthcare-grade security

The roadmap is designed to be flexible and adaptable to changing requirements while maintaining focus on delivering value to users and stakeholders.
