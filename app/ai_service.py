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
        
        # Build comprehensive context
        context_info = ""
        
        if ticket_context:
            context_info = f"""
CURRENT TICKET DETAILS:
- Ticket ID: #{ticket_context.get('id', 'N/A')}
- Subject: {ticket_context.get('subject', 'N/A')}
- From: {ticket_context.get('sender', 'N/A')}
- Category: {ticket_context.get('category', 'N/A')}
- Status: {ticket_context.get('status', 'N/A')}
- Urgency: {ticket_context.get('urgency', 'N/A')}
- Created: {ticket_context.get('created_at', 'N/A')}
- Assigned to: {ticket_context.get('assigned_to', 'Unassigned')}

TICKET CONTENT:
{ticket_context.get('body', 'No description available')}

RECENT ACTIVITY:
"""
            # Add recent activity if available
            recent_activity = ticket_context.get('recent_activity', [])
            if recent_activity:
                for activity in recent_activity[:3]:  # Show last 3 activities
                    context_info += f"- {activity.get('timestamp', '')}: {activity.get('action', '')} by {activity.get('user', '')} - {activity.get('details', '')}\n"
            else:
                context_info += "- No recent activity tracking available (logging system is general-purpose)\n"

        # Determine the type of query and build appropriate system prompt
        system_prompt = self._build_chatbot_system_prompt(user_message, ticket_context is not None)
        
        # Build the user prompt
        user_prompt = f"""
{context_info}

KNOWLEDGE BASE REFERENCE:
{self.knowledge_base}

USER QUESTION: {user_message}

Please provide a helpful, specific response based on the ticket context and knowledge base.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=400  # Increased for more detailed responses
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Chatbot response failed: {e}")
            return self._fallback_response(user_message, ticket_context, f"AI service error: {str(e)}")

    def _fallback_response(self, user_message: str, ticket_context: Optional[Dict] = None, error_msg: str = None) -> str:
        """Provide fallback responses when OpenAI is not available"""
        
        # If we have ticket context, provide detailed ticket information
        if ticket_context:
            ticket_info = f"""**Ticket #{ticket_context.get('id', 'Unknown')} Summary:**

📋 **Subject:** {ticket_context.get('subject', 'No subject')}
👤 **From:** {ticket_context.get('sender', 'Unknown sender')}
📂 **Category:** {ticket_context.get('category', 'Uncategorized')}
🔄 **Status:** {ticket_context.get('status', 'Unknown')}
⚡ **Urgency:** {ticket_context.get('urgency', 'Not set')}
📅 **Created:** {ticket_context.get('created_at', 'Unknown')}
👥 **Assigned to:** {ticket_context.get('assigned_to', 'Unassigned')}

**Ticket Description:**
{ticket_context.get('body', 'No description available')}"""

            # Provide different responses based on the user's question
            message_lower = user_message.lower()
            
            if any(word in message_lower for word in ['about', 'summary', 'tell me', 'what is', 'describe']):
                return ticket_info
            
            elif any(word in message_lower for word in ['next', 'do', 'action', 'steps']):
                return f"""{ticket_info}

**Suggested Next Steps:**
• Review the ticket details above
• Check if the category and urgency are appropriate
• Consider assigning the ticket if unassigned
• Follow your organization's procedures for {ticket_context.get('category', 'this type of')} requests"""
            
            elif any(word in message_lower for word in ['category', 'urgency', 'priority']):
                return f"""**Category & Urgency Information:**

📂 **Category:** {ticket_context.get('category', 'Uncategorized')}
⚡ **Urgency:** {ticket_context.get('urgency', 'Not set')}

This ticket is categorized as "{ticket_context.get('category', 'Uncategorized')}" and has "{ticket_context.get('urgency', 'Not set')}" urgency priority."""
            
            else:
                return f"""{ticket_info}

I can see you're viewing this ticket, but I need OpenAI API configuration for more intelligent responses. However, I can provide basic ticket information as shown above."""
        
        # General responses when no ticket context
        else:
            if error_msg:
                return f"I'm currently unable to access the AI service ({error_msg}). However, I can still help you navigate TeBSTrack! Try viewing a specific ticket for detailed information, or ask me about general TeBSTrack features."
            else:
                return "I'm currently running in basic mode (OpenAI API not configured). I can provide ticket information when you're viewing a specific ticket, or help with general TeBSTrack navigation. Try opening a ticket to see detailed information!"

    def _build_chatbot_system_prompt(self, user_message: str, has_ticket_context: bool) -> str:
        """Build an appropriate system prompt based on the user's question and context"""
        
        base_prompt = """You are TeBSTrack Assistant, an intelligent IT support chatbot. You help users understand tickets, navigate the system, and get support guidance."""
        
        if has_ticket_context:
            # User is viewing a specific ticket
            ticket_aware_prompt = base_prompt + """

TICKET-SPECIFIC CAPABILITIES:
- Analyze and summarize the current ticket
- Explain the ticket's category, urgency, and status
- Suggest next steps based on ticket content
- Interpret recent activity and progress
- Identify potential solutions based on the issue description
- Explain technical terms or procedures mentioned in the ticket

RESPONSE GUIDELINES:
- Always reference the specific ticket when relevant
- Use ticket details to provide contextualized advice
- If asked about "this ticket", refer to the current ticket data
- Provide actionable insights based on the ticket's category and content
- Explain any technical jargon in user-friendly terms
"""
        else:
            # General TeBSTrack assistance
            ticket_aware_prompt = base_prompt + """

GENERAL ASSISTANCE CAPABILITIES:
- Explain TeBSTrack features and navigation
- Guide users through ticket creation and management
- Explain category types and when to use them
- Help with understanding urgency levels
- Provide general IT support guidance

RESPONSE GUIDELINES:
- Provide clear, step-by-step instructions
- Explain system features and best practices
- Help users understand how to use TeBSTrack effectively
"""

        return ticket_aware_prompt

# Initialize AI service
ai_service = TeBSTrackAI()

def get_ai_service():
    """Get the global AI service instance."""
    return ai_service
