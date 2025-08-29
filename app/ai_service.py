"""
AI Service for TeBSTrack
Handles ticket categorization, urgency prediction, template recommendation, and chatbot functionality
"""

import openai
import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from .models import Category, db

class TeBSTrackAI:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"  # Cost-effective for categorization
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> str:
        """Load the Infra Knowledge Transfer document content"""
        try:
            from .document_loader import DocumentLoader
            
            # Try to load knowledge document
            knowledge_paths = [
                'app/knowledge/infra_guide.pdf',
                'app/knowledge/infra_guide.docx',
                'knowledge/infra_guide.pdf',
                'knowledge/infra_guide.docx'
            ]
            
            for path in knowledge_paths:
                if os.path.exists(path):
                    try:
                        content = DocumentLoader.load_knowledge_document(path)
                        if content:
                            return content
                    except Exception as e:
                        logging.warning(f"Failed to load {path}: {e}")
                        continue
        except ImportError:
            logging.warning("DocumentLoader not available")
        
        # Fallback knowledge base content
        return """
        TeBSTrack IT Support Knowledge Base:
        
        CATEGORIES:
        1. SVN & VPN - Version control and VPN access issues
        2. Server request - Server provisioning and maintenance
        3. Joiners and Exit - Employee onboarding/offboarding
        4. Laptop Hardware Issue - Hardware problems and repairs
        5. TMS - Travel Management System issues
        6. Application Access Requests - Software access and permissions
        7. M365 - Microsoft 365 related issues
        8. DevOps - CI/CD, deployment, infrastructure issues
        9. Other request - General IT inquiries
        
        URGENCY LEVELS:
        - Urgent: System down, security breach
        - High: Major functionality impaired
        - Medium: Minor issues, workarounds available
        - Low: Enhancement requests, questions
        """
        
        for path in knowledge_paths:
            if os.path.exists(path):
                content = DocumentLoader.load_knowledge_document(path)
                if content:
                    return content
        
        # Fallback content if no document found
        return """
        Infrastructure Knowledge Base:
        - VPN & SVN: Check user permissions, validate account status, verify network connectivity
        - Server requests: Validate resource requirements, check capacity, approve specifications
        - Joiners and Exit: Follow onboarding/offboarding procedures, update access permissions
        - Laptop Hardware: Diagnose hardware issues, check warranty, coordinate replacements
        - TMS: Traffic Management System issues, check system status, validate configurations
        - Application Access: Verify user permissions, check group memberships, validate licenses
        - M365: Microsoft 365 issues, check licensing, verify admin portal settings
        - DevOps: CI/CD pipeline issues, deployment problems, infrastructure automation
        - Other requests: General support, escalation procedures, documentation requests
        """
    
    def get_available_categories(self) -> List[str]:
        """Get current categories from database"""
        categories = Category.query.all()
        return [cat.name for cat in categories]
    
    def categorize_ticket(self, subject: str, body: str, sender: str = "") -> Dict[str, any]:
        """
        Categorize ticket and predict urgency using OpenAI
        Returns: {category_name: str, urgency: str, confidence: float, reasoning: str}
        """
        categories = self.get_available_categories()
        urgency_levels = ["Low", "Medium", "High", "Urgent"]
        
        prompt = self._build_categorization_prompt(subject, body, sender, categories, urgency_levels)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent categorization
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logging.error(f"AI categorization failed: {e}")
            return {
                "category": "Other request",
                "urgency": "Medium", 
                "confidence": 0.0,
                "reasoning": "AI categorization failed, using defaults"
            }
    
    def _build_categorization_prompt(self, subject: str, body: str, sender: str, categories: List[str], urgency_levels: List[str]) -> str:
        """Build the categorization prompt"""
        return f"""
Analyze this support ticket and categorize it:

TICKET DETAILS:
Subject: {subject}
Description: {body}
Sender: {sender}

AVAILABLE CATEGORIES:
{', '.join(categories)}

URGENCY LEVELS:
- Low: Minor issues, cosmetic problems, feature requests
- Medium: Standard requests, non-critical issues affecting single user
- High: Issues affecting multiple users or business processes
- Urgent: System down, security issues, blocking business operations

KNOWLEDGE BASE CONTEXT:
{self.knowledge_base}

Please analyze and respond with a JSON object containing:
{{
    "category": "exact category name from available list",
    "urgency": "exact urgency level from list", 
    "confidence": 0.85,
    "reasoning": "brief explanation of categorization logic"
}}

Consider the business impact, number of affected users, and urgency keywords in your analysis.
"""

    def _get_system_prompt(self) -> str:
        """System prompt for AI categorization"""
        return """
You are an IT support categorization expert. Your task is to accurately categorize support tickets based on:

1. Technical content analysis
2. Business impact assessment  
3. Urgency indicators
4. Available knowledge base information

Always respond with valid JSON. Choose only from the provided categories and urgency levels.
Be conservative with "Urgent" - reserve for true emergencies.
"""

    def recommend_email_template(self, subject: str, description: str, category: str) -> Dict[str, any]:
        """
        Recommend email template based on ticket content
        Returns: {template_name: str, confidence: float, reasoning: str, recommended: bool}
        """
        # Define available templates and their use cases
        templates = {
            "VPN Account Creation": "Use for VPN access requests, VPN setup issues, remote access needs",
            "Password Reset": "Use for password reset requests, account lockouts, authentication issues", 
            "Software Installation": "Use for software requests, application installations, license requests",
            "Hardware Request": "Use for hardware requests, equipment issues, device replacements",
            "Server Access": "Use for server access requests, database permissions, system access",
            "General Response": "Use for general inquiries, acknowledgments, status updates"
        }
        
        prompt = f"""
Analyze this support ticket and recommend the most appropriate email template:

TICKET DETAILS:
Subject: {subject}
Description: {description}
Category: {category}

AVAILABLE TEMPLATES:
{json.dumps(templates, indent=2)}

TEMPLATE SELECTION GUIDELINES:
- Match the ticket content to template purpose
- Consider the specific request type
- Look for keywords that indicate template relevance
- If no specific template fits well, recommend "General Response"

Respond with JSON:
{{
    "template_name": "exact template name",
    "confidence": 0.85,
    "reasoning": "why this template fits",
    "recommended": true
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an email template recommendation expert. Analyze tickets and suggest the most appropriate response template."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logging.error(f"Template recommendation failed: {e}")
            return {
                "template_name": "General Response",
                "confidence": 0.0,
                "reasoning": "AI recommendation failed, using general template",
                "recommended": False
            }

    def chatbot_response(self, user_message: str, ticket_context: Optional[Dict] = None) -> str:
        """
        Generate intelligent, context-aware chatbot response for user questions
        """
        # Check if OpenAI is available, if not provide fallback responses
        if not self.client:
            return self._fallback_response(user_message, ticket_context)
        
        # Analyze the user's intent to determine response type
        intent = self._analyze_user_intent(user_message)
        
        # Build context based on intent - include comprehensive ticket details when ticket context exists
        context_info = ""
        
        if ticket_context and intent['needs_ticket_details']:
            context_info = f"""
CURRENT TICKET DETAILS:
- Ticket ID: #{ticket_context.get('id', 'N/A')}
- Subject: {ticket_context.get('subject', 'N/A')}
- From/Sender: {ticket_context.get('sender', 'N/A')}
- Category: {ticket_context.get('category', 'N/A')}
- Status: {ticket_context.get('status', 'N/A')}
- Urgency: {ticket_context.get('urgency', 'N/A')}
- Created: {ticket_context.get('created_at', 'N/A')}
- Assigned to: {ticket_context.get('assigned_to', 'Unassigned')}

TICKET CONTENT:
{ticket_context.get('body', 'No description available')}
"""
        elif ticket_context:
            # Provide comprehensive context for all questions when viewing a ticket
            context_info = f"""
CURRENT TICKET CONTEXT:
- Ticket ID: #{ticket_context.get('id', 'N/A')}
- Subject: {ticket_context.get('subject', 'N/A')}
- From/Sender: {ticket_context.get('sender', 'N/A')}
- Category: {ticket_context.get('category', 'N/A')}
- Status: {ticket_context.get('status', 'N/A')}
- Urgency: {ticket_context.get('urgency', 'N/A')}
- Created: {ticket_context.get('created_at', 'N/A')}
- Assigned to: {ticket_context.get('assigned_to', 'Unassigned')}
- Description: {ticket_context.get('body', 'No description available')}
"""

        # Check for direct responses to common questions to avoid AI calls
        if ticket_context and intent['needs_ticket_details']:
            message_lower = user_message.lower()
            # Only provide ultra-short responses for very simple, single-word type questions
            if 'status?' == message_lower.strip() or ('status' in message_lower and len(message_lower.split()) <= 3):
                return f"Status: {ticket_context.get('status', 'Unknown')}"
            elif 'category?' == message_lower.strip() or ('category' in message_lower and len(message_lower.split()) <= 3):
                return f"Category: {ticket_context.get('category', 'N/A')} - handles VPN/network access"
            elif 'urgency?' == message_lower.strip() or ('urgency' in message_lower and len(message_lower.split()) <= 3):
                return f"Urgency: {ticket_context.get('urgency', 'N/A')}"
            elif any(word in message_lower for word in ['when', 'date', 'created', 'received', 'reported', 'occurred', 'happen']) and ('this' in message_lower or 'ticket' in message_lower or 'issue' in message_lower):
                created_date = ticket_context.get('created_at', 'Unknown')
                return f"Created: {created_date}"
            elif any(word in message_lower for word in ['who', 'sender', 'from']) and any(word in message_lower for word in ['requested', 'sent', 'created', 'mail']):
                sender = ticket_context.get('sender', 'Unknown')
                return f"Sender: {sender}"
            # For more complex questions like "what should I do next?", let AI provide comprehensive response

        # Build system prompt based on intent
        system_prompt = self._build_chatbot_system_prompt(user_message, ticket_context is not None, intent)
        
        # Build the user prompt
        if intent['needs_ticket_details']:
            user_prompt = f"""
{context_info}

USER QUESTION: {user_message}

Using the complete ticket context above, provide an informative and helpful response. Include relevant details from the ticket information to fully answer the question."""
        else:
            user_prompt = f"""
{context_info}

USER QUESTION: {user_message}

Provide a helpful response using any relevant context available."""

        try:
            # Increased token limits for more informative responses (paragraph length)
            max_tokens = 100 if intent.get('is_casual', False) else (300 if intent.get('needs_ticket_details', False) else 200)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Chatbot response failed: {e}")
            return self._fallback_response(user_message, ticket_context, f"AI service error: {str(e)}")

    def _analyze_user_intent(self, user_message: str) -> Dict[str, bool]:
        """
        Analyze user message to determine what kind of response they need
        """
        message_lower = user_message.lower().strip()
        
        # Greetings and casual conversation
        casual_phrases = [
            'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 
            'thanks', 'thank you', 'bye', 'goodbye', 'how are you', 'how are you?',
            'how\'s it going', 'how is it going', 'what\'s up', 'whats up',
            'nice to meet you', 'pleased to meet you', 'good to see you'
        ]
        
        # Keywords that explicitly indicate wanting ticket details
        explicit_ticket_keywords = [
            'about this ticket', 'current ticket', 'this ticket', 'ticket details',
            'tell me about', 'explain this', 'describe this', 'summary of this',
            'what is this ticket', 'ticket summary', 'ticket information'
        ]
        
        # Keywords that definitely need ticket context (including date questions)
        definite_ticket_keywords = [
            'status', 'category', 'urgency', 'assigned', 'created', 'sender',
            'next steps', 'what should', 'how to resolve', 'solution', 'fix', 'resolve',
            'when was this', 'when did this', 'what date', 'creation date', 'reported',
            'issue occur', 'this happen', 'this reported', 'who requested', 'who sent',
            'who created', 'who is the sender', 'from who'
        ]
        
        # Questions that might need context but could be general
        contextual_questions = [
            'what', 'who', 'when', 'where', 'why', 'how', 'explain', 'show me', 'tell me more'
        ]
        
        # Check if explicitly asking about ticket (check this FIRST)
        if any(keyword in message_lower for keyword in explicit_ticket_keywords):
            return {'needs_ticket_details': True, 'is_casual': False}
        
        # Check for specific ticket-related keywords including date questions (check BEFORE casual)
        if any(keyword in message_lower for keyword in definite_ticket_keywords):
            return {'needs_ticket_details': True, 'is_casual': False}
        
        # Check if it's a simple greeting or casual conversation (check AFTER ticket keywords)
        if any(phrase in message_lower for phrase in casual_phrases):
            return {'needs_ticket_details': False, 'is_casual': True}
        
        # For contextual questions, only assume they want ticket details if they mention specific terms
        if any(word in message_lower for word in contextual_questions):
            # If the question is very short and general, treat as casual
            if len(message_lower.split()) <= 4 and not any(keyword in message_lower for keyword in definite_ticket_keywords):
                return {'needs_ticket_details': False, 'is_casual': False}
            # Otherwise assume they want ticket details
            return {'needs_ticket_details': True, 'is_casual': False}
        
        # Default: assume they want brief response
        return {'needs_ticket_details': False, 'is_casual': False}

    def _fallback_response(self, user_message: str, ticket_context: Optional[Dict] = None, error_msg: str = None) -> str:
        """Provide fallback responses when OpenAI is not available"""
        
        # Analyze user intent even in fallback mode
        intent = self._analyze_user_intent(user_message)
        
        # Handle casual conversation
        if intent.get('is_casual', False):
            casual_responses = {
                'hi': "Hi there! 👋",
                'hello': "Hello! How can I help?",
                'hey': "Hey! What's up?",
                'thanks': "You're welcome! 😊",
                'thank you': "Happy to help!",
                'bye': "Goodbye! 👋",
                'goodbye': "See you later!",
                'how are you': "I'm great! How can I help you today?"
            }
            
            message_lower = user_message.lower().strip()
            for key, response in casual_responses.items():
                if key in message_lower:
                    return response
            
            return "Hi! How can I help with TeBSTrack?"
        
        # If we have ticket context and user wants ticket details
        if ticket_context and intent.get('needs_ticket_details', False):
            return f"""Ticket #{ticket_context.get('id', 'N/A')}: {ticket_context.get('subject', 'No subject')}
Status: {ticket_context.get('status', 'Unknown')} | Category: {ticket_context.get('category', 'N/A')} | Urgency: {ticket_context.get('urgency', 'N/A')}
From: {ticket_context.get('sender', 'Unknown')} | Created: {ticket_context.get('created_at', 'Unknown')}
Assigned: {ticket_context.get('assigned_to', 'Unassigned')}"""
        
        # Brief acknowledgment if viewing ticket but not asking for details
        elif ticket_context:
            return f"I can see you're viewing Ticket #{ticket_context.get('id', 'N/A')}. How can I help?"
        
        # General responses when no ticket context
        else:
            return "I'm running in basic mode. How can I help with TeBSTrack?"

    def _build_chatbot_system_prompt(self, user_message: str, has_ticket_context: bool, intent: Dict[str, bool]) -> str:
        """Build an appropriate system prompt based on the user's question and context"""
        
        base_prompt = """You are TeBSTrack Assistant. Provide helpful, informative responses using all available ticket context."""
        
        if intent.get('is_casual', False):
            # Handle casual conversation
            return base_prompt + """

CASUAL MODE: Keep responses friendly and brief (1-2 sentences). Be conversational but helpful."""
            
        elif has_ticket_context and intent.get('needs_ticket_details', False):
            # User wants detailed ticket information
            return base_prompt + """

TICKET MODE: Provide informative responses using the complete ticket context. Include relevant details from all ticket fields. You can write a paragraph if needed to be thorough. Use newlines sparingly for readability."""
            
        elif has_ticket_context:
            # User is viewing a ticket but asking general questions
            return base_prompt + """

CONTEXT-AWARE MODE: Use the complete ticket context to provide informed answers. Reference ticket details when relevant to the question. Be informative but not overwhelming."""
            
        else:
            # General assistance
            return base_prompt + """

HELP MODE: Provide clear, helpful answers about TeBSTrack features and functionality."""

# Initialize AI service
ai_service = TeBSTrackAI()

def get_ai_service():
    """Get the global AI service instance."""
    return ai_service
