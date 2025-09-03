"""
AI Service for TeBSTrack
Handles ticket categorization, urgency prediction, template recommendation, and chatbot functionality
"""

import openai
import os
import json
import logging
import shutil
from typing import Dict, List, Optional, Tuple
from .models import Category, db

class TeBSTrackAI:
    def __init__(self):
        # Get API key from system settings or environment
        from .models import SystemSettings
        api_key = SystemSettings.get_openai_api_key()
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Cost-effective for categorization
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> str:
        """Load the Infra Knowledge Transfer document content"""
        try:
            from .document_loader import DocumentLoader
            
            # First priority: Check for edited copy of infra_guide (text version)
            text_copy_paths = [
                'app/knowledge/infra_guide_edited.txt',
                'knowledge/infra_guide_edited.txt'
            ]
            
            for path in text_copy_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                logging.info(f"Loaded knowledge base from edited text copy {path}")
                                return content
                    except Exception as e:
                        logging.warning(f"Failed to load edited text copy {path}: {e}")
                        continue
            
            # Second priority: Check for edited copy of infra_guide (document version)
            copy_paths = [
                'app/knowledge/infra_guide_edited.docx',
                'app/knowledge/infra_guide_edited.pdf',
                'knowledge/infra_guide_edited.docx',
                'knowledge/infra_guide_edited.pdf'
            ]
            
            for path in copy_paths:
                if os.path.exists(path):
                    try:
                        content = DocumentLoader.load_knowledge_document(path)
                        if content:
                            logging.info(f"Loaded knowledge base from edited copy {path}")
                            return content
                    except Exception as e:
                        logging.warning(f"Failed to load edited copy {path}: {e}")
                        continue
            
            # Third priority: Check for custom text knowledge
            custom_paths = [
                'app/knowledge/custom_knowledge.txt',
                'knowledge/custom_knowledge.txt'
            ]
            
            for path in custom_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                logging.info(f"Loaded custom knowledge base from {path}")
                                return content
                    except Exception as e:
                        logging.warning(f"Failed to load custom knowledge from {path}: {e}")
                        continue
            
            # Fourth priority: Load original knowledge document
            original_paths = [
                'app/knowledge/infra_guide.docx',
                'app/knowledge/infra_guide.pdf',
                'knowledge/infra_guide.docx',
                'knowledge/infra_guide.pdf'
            ]
            
            for path in original_paths:
                if os.path.exists(path):
                    try:
                        content = DocumentLoader.load_knowledge_document(path)
                        if content:
                            logging.info(f"Loaded knowledge base from original document {path}")
                            return content
                    except Exception as e:
                        logging.warning(f"Failed to load {path}: {e}")
                        continue
        except ImportError:
            logging.warning("DocumentLoader not available")
        
        # Fallback knowledge base content
        logging.info("Using fallback knowledge base content")
        return """
        TeBSTrack Infrastructure Ticketing System Knowledge Base:
        
        SYSTEM OVERVIEW:
        TeBSTrack is an infrastructure team ticketing system that:
        - Automatically creates tickets from emails sent to the "infra mailbox"
        - Allows infra team members to track, manage, and resolve user requests
        - Serves as a central hub for infrastructure-related issues and requests
        
        WORKFLOW:
        1. External users/employees send requests to infra mailbox
        2. TeBSTrack automatically converts emails into tickets
        3. Infra team members (TeBSTrack users) view and manage tickets
        4. Infra team resolves issues and responds to requesters
        
        USER ROLES:
        - TeBSTrack Users: Infra team members who manage and resolve tickets
        - Ticket Requesters: External users who send emails to infra mailbox
        
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
    
    def get_knowledge_base_status(self) -> Dict[str, any]:
        """Get information about the knowledge base loading status"""
        kb_length = len(self.knowledge_base) if self.knowledge_base else 0
        
        # Determine which file is currently being used
        current_source_path = None
        source_type = "unknown"
        
        # Check for edited text copy first (highest priority)
        text_copy_paths = [
            'app/knowledge/infra_guide_edited.txt',
            'knowledge/infra_guide_edited.txt'
        ]
        
        for path in text_copy_paths:
            if os.path.exists(path):
                current_source_path = path
                source_type = "edited_text_copy"
                break
        
        # Check for edited document copy
        if not current_source_path:
            copy_paths = [
                'app/knowledge/infra_guide_edited.docx',
                'app/knowledge/infra_guide_edited.pdf',
                'knowledge/infra_guide_edited.docx',
                'knowledge/infra_guide_edited.pdf'
            ]
            
            for path in copy_paths:
                if os.path.exists(path):
                    current_source_path = path
                    source_type = "edited_document_copy"
                    break
        
        # Check for custom text knowledge
        if not current_source_path:
            custom_paths = [
                'app/knowledge/custom_knowledge.txt',
                'knowledge/custom_knowledge.txt'
            ]
            
            for path in custom_paths:
                if os.path.exists(path):
                    current_source_path = path
                    source_type = "custom_text"
                    break
        
        # Check for original document
        if not current_source_path:
            original_paths = [
                'app/knowledge/infra_guide.docx',
                'app/knowledge/infra_guide.pdf',
                'knowledge/infra_guide.docx',
                'knowledge/infra_guide.pdf'
            ]
            
            for path in original_paths:
                if os.path.exists(path):
                    current_source_path = path
                    source_type = "original_document"
                    break
        
        # Fallback case
        if not current_source_path:
            source_type = "fallback_content"
            current_source_path = "Built-in fallback content (no files found)"
        
        # Check if using fallback content
        is_fallback = "Emergency Mode" in self.knowledge_base if self.knowledge_base else True
        if is_fallback and source_type != "fallback_content":
            source_type = "fallback_content"
            current_source_path = "Built-in fallback content"
        
        return {
            "loaded": bool(self.knowledge_base),
            "content_length": kb_length,
            "source_type": source_type,
            "source_path": current_source_path,
            "is_fallback_content": is_fallback,
            "has_document": source_type in ["original_document", "edited_document_copy"],
            "preview": self.knowledge_base[:200] + "..." if self.knowledge_base else "No knowledge base loaded"
        }
    
    def test_knowledge_base_integration(self, test_question: str = "How do I reset a user's VPN access?") -> str:
        """Test the knowledge base integration with a sample question"""
        try:
            response = self.chatbot_response(
                user_message=test_question,
                ticket_context=None,
                user_context={"username": "test_user", "role": "infra"}
            )
            return response
        except Exception as e:
            return f"Knowledge base test failed: {e}"
    
    def refresh_knowledge_base(self) -> bool:
        """Reload the knowledge base from files"""
        try:
            old_kb_length = len(self.knowledge_base) if self.knowledge_base else 0
            self.knowledge_base = self._load_knowledge_base()
            new_kb_length = len(self.knowledge_base) if self.knowledge_base else 0
            
            logging.info(f"Knowledge base refreshed: {old_kb_length} -> {new_kb_length} characters")
            return True
        except Exception as e:
            logging.error(f"Failed to refresh knowledge base: {e}")
            return False
    
    def update_knowledge_base(self, new_content: str) -> bool:
        """Update the knowledge base by creating an edited copy of the original document"""
        try:
            if not new_content or not new_content.strip():
                logging.warning("Attempted to set empty knowledge base content")
                return False
            
            # Find the original infra_guide document
            original_path = self._find_original_document()
            if not original_path:
                # Fallback to text-based custom knowledge if no original document exists
                return self._save_custom_text_knowledge(new_content)
            
            # Create a copy with the edited content
            success = self._create_edited_copy(original_path, new_content)
            if success:
                # Update in-memory knowledge base
                self.knowledge_base = new_content.strip()
                logging.info(f"Knowledge base updated via edited copy: {len(self.knowledge_base)} characters")
                return True
            else:
                # Fallback to text-based custom knowledge
                return self._save_custom_text_knowledge(new_content)
                
        except Exception as e:
            logging.error(f"Failed to update knowledge base: {e}")
            return False
    
    def reset_knowledge_base(self) -> bool:
        """Reset knowledge base to original document by removing edited copies"""
        try:
            # Remove any edited text copies
            text_copy_paths = [
                'app/knowledge/infra_guide_edited.txt',
                'knowledge/infra_guide_edited.txt'
            ]
            
            # Remove any edited document copies
            copy_paths = [
                'app/knowledge/infra_guide_edited.docx',
                'app/knowledge/infra_guide_edited.pdf',
                'knowledge/infra_guide_edited.docx',
                'knowledge/infra_guide_edited.pdf'
            ]
            
            removed_any = False
            all_paths = text_copy_paths + copy_paths
            
            for path in all_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        logging.info(f"Removed edited copy: {path}")
                        removed_any = True
                    except Exception as e:
                        logging.warning(f"Failed to remove {path}: {e}")
            
            # Also remove custom text knowledge files
            custom_paths = [
                'app/knowledge/custom_knowledge.txt',
                'knowledge/custom_knowledge.txt'
            ]
            
            for path in custom_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        logging.info(f"Removed custom knowledge: {path}")
                        removed_any = True
                    except Exception as e:
                        logging.warning(f"Failed to remove {path}: {e}")
            
            # Reload knowledge base from original document
            self.knowledge_base = self._load_knowledge_base()
            logging.info("Knowledge base reset to original document")
            return True
            
        except Exception as e:
            logging.error(f"Failed to reset knowledge base: {e}")
            return False
    
    def _find_original_document(self) -> Optional[str]:
        """Find the original infra_guide document"""
        original_paths = [
            'app/knowledge/infra_guide.docx',
            'app/knowledge/infra_guide.pdf',
            'knowledge/infra_guide.docx',
            'knowledge/infra_guide.pdf'
        ]
        
        for path in original_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _create_edited_copy(self, original_path: str, new_content: str) -> bool:
        """Create an edited copy of the original document with new content"""
        try:
            # Determine the copy path based on original file extension
            directory = os.path.dirname(original_path)
            filename = os.path.basename(original_path)
            name, ext = os.path.splitext(filename)
            copy_path = os.path.join(directory, f"{name}_edited{ext}")
            
            # For now, save as text file since we can't easily edit DOCX/PDF files
            # We'll create a text representation that the document loader can handle
            text_copy_path = os.path.join(directory, "infra_guide_edited.txt")
            
            with open(text_copy_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logging.info(f"Created edited knowledge copy at: {text_copy_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create edited copy: {e}")
            return False
    
    def _save_custom_text_knowledge(self, content: str) -> bool:
        """Fallback method to save custom knowledge as text file"""
        try:
            # Ensure the knowledge directory exists
            knowledge_dir = 'app/knowledge'
            if not os.path.exists(knowledge_dir):
                os.makedirs(knowledge_dir)
            
            # Save the custom content
            custom_path = os.path.join(knowledge_dir, 'custom_knowledge.txt')
            with open(custom_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update in-memory knowledge base
            self.knowledge_base = content.strip()
            logging.info(f"Saved custom knowledge as text: {len(content)} characters")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save custom text knowledge: {e}")
            return False
    
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
        # Get available templates from database
        from .models import EmailTemplate
        
        active_templates = EmailTemplate.query.filter_by(is_active=True).all()
        if not active_templates:
            return {
                "template_name": None,
                "confidence": 0.0,
                "reasoning": "No active email templates available in the database",
                "recommended": False
            }
        
        # Build templates dictionary with their use cases
        templates = {}
        for template in active_templates:
            use_case = template.use_case_description if template.use_case_description else f"Email template for general use"
            templates[template.name] = use_case
        
        prompt = f"""
Analyze this support ticket and recommend the most appropriate email template:

TICKET DETAILS:
Subject: {subject}
Description: {description}
Category: {category}

AVAILABLE TEMPLATES:
{json.dumps(templates, indent=2)}

TEMPLATE SELECTION GUIDELINES:
- Match the ticket content to template purpose and use case
- Consider the specific request type and category
- Look for keywords that indicate template relevance
- If no specific template fits well, set template_name to null and explain why

Respond with JSON:
{{
    "template_name": "exact template name or null",
    "confidence": 0.85,
    "reasoning": "why this template fits or why no template is suitable",
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
            # Try to find a general purpose template from database
            from .models import EmailTemplate
            
            general_template = EmailTemplate.query.filter_by(is_active=True).filter(
                db.or_(
                    EmailTemplate.name.ilike('%general%'),
                    EmailTemplate.name.ilike('%response%'),
                    EmailTemplate.use_case_description.ilike('%general%')
                )
            ).first()
            
            if general_template:
                return {
                    "template_name": general_template.name,
                    "confidence": 0.0,
                    "reasoning": "AI recommendation failed, using available general template",
                    "recommended": False
                }
            else:
                return {
                    "template_name": None,
                    "confidence": 0.0,
                    "reasoning": "AI recommendation failed and no general template available",
                    "recommended": False
                }

    def chatbot_response(self, user_message: str, ticket_context: Optional[Dict] = None, user_context: Optional[Dict] = None) -> str:
        """
        Generate intelligent, context-aware chatbot response for user questions
        """
        # Check if OpenAI is available, if not provide fallback responses
        if not self.client:
            return self._fallback_response(user_message, ticket_context, user_context)
        
        # Analyze the user's intent to determine response type
        intent = self._analyze_user_intent(user_message)
        
        # Build context based on intent - include comprehensive ticket details when ticket context exists
        context_info = ""
        
        # Add user information to context
        if user_context:
            context_info += f"""
USER INFORMATION:
- Current User: {user_context.get('username', 'Unknown')}
- User Role: {user_context.get('role', 'user')}
"""
        
        if ticket_context and intent['needs_ticket_details']:
            context_info += f"""
COMPLETE TICKET INFORMATION:
- Ticket ID: #{ticket_context.get('id', 'N/A')}
- Subject: {ticket_context.get('subject', 'N/A')}
- REQUEST BY (Email Sender): {ticket_context.get('sender', 'N/A')}
- Category: {ticket_context.get('category', 'N/A')} 
- Status: {ticket_context.get('status', 'N/A')}
- Urgency: {ticket_context.get('urgency', 'N/A')}
- Created Date: {ticket_context.get('created_at', 'N/A')}
- Assigned to: {ticket_context.get('assigned_to', 'Unassigned')}

ORIGINAL EMAIL REQUEST:
{ticket_context.get('body', 'No description available')}

IMPORTANT: This ticket was automatically created from an email sent to the infra mailbox. The "REQUEST BY" field shows the external user who sent the email request. Your role is to help the infra team member resolve this request.
"""
        elif ticket_context:
            # Provide comprehensive context for all questions when viewing a ticket
            context_info += f"""
COMPLETE TICKET INFORMATION:
- Ticket ID: #{ticket_context.get('id', 'N/A')}
- Subject: {ticket_context.get('subject', 'N/A')}
- REQUEST BY (Email Sender): {ticket_context.get('sender', 'N/A')}
- Category: {ticket_context.get('category', 'N/A')}
- Status: {ticket_context.get('status', 'N/A')}
- Urgency: {ticket_context.get('urgency', 'N/A')}
- Created Date: {ticket_context.get('created_at', 'N/A')}
- Assigned to: {ticket_context.get('assigned_to', 'Unassigned')}

ORIGINAL EMAIL REQUEST:
{ticket_context.get('body', 'No description available')}

IMPORTANT: This ticket was automatically created from an email sent to the infra mailbox. The "REQUEST BY" field shows the external user who sent the email request. Your role is to help the infra team member resolve this request.
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
            elif any(word in message_lower for word in ['who', 'sender', 'from']) and any(word in message_lower for word in ['requested', 'sent', 'created', 'mail', 'request', 'ticket']):
                sender = ticket_context.get('sender', 'Unknown')
                return f"Requested by: {sender}"
            # For more complex questions like "what should I do next?", let AI provide comprehensive response

        # Build system prompt based on intent
        system_prompt = self._build_chatbot_system_prompt(user_message, ticket_context is not None, intent, user_context)
        
        # Build the user prompt with knowledge base integration
        if intent['needs_ticket_details']:
            user_prompt = f"""
{context_info}

KNOWLEDGE BASE REFERENCE:
{self.knowledge_base}

USER QUESTION: {user_message}

Using the complete ticket context above AND the knowledge base information, provide an informative and helpful response. Reference the knowledge base to suggest specific solutions, procedures, or troubleshooting steps when relevant to the ticket category and user's question."""
        else:
            user_prompt = f"""
{context_info}

KNOWLEDGE BASE REFERENCE:
{self.knowledge_base}

USER QUESTION: {user_message}

Provide a helpful response using the knowledge base information and any relevant context available. Reference specific procedures, solutions, or guidelines from the knowledge base when applicable."""

        try:
            # Significantly increased token limits for comprehensive, detailed responses
            max_tokens = 150 if intent.get('is_casual', False) else (500 if intent.get('needs_ticket_details', False) else 300)
            
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
            return self._fallback_response(user_message, ticket_context, user_context, f"AI service error: {str(e)}")

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
        
        # Keywords that definitely need ticket context (including specific who/when questions)
        definite_ticket_keywords = [
            'status', 'category', 'urgency', 'assigned', 'created', 'sender',
            'next steps', 'what should', 'how to resolve', 'solution', 'fix', 'resolve',
            'when was this', 'when did this', 'what date', 'creation date', 'reported',
            'issue occur', 'this happen', 'this reported', 
            'who requested', 'who sent', 'who created', 'who is the sender', 'from who',
            'who made this', 'who submitted', 'who opened', 'who filed', 'created by',
            'requested by', 'sent by', 'submitted by', 'opened by', 'filed by'
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

    def _fallback_response(self, user_message: str, ticket_context: Optional[Dict] = None, user_context: Optional[Dict] = None, error_msg: str = None) -> str:
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
                    # Add user name if available
                    if user_context and user_context.get('username'):
                        if key in ['hi', 'hello', 'hey']:
                            return f"Hi {user_context['username']}! 👋 How can I help you today?"
                    return response
            
            # Default casual response with user name
            user_name = user_context.get('username', '') if user_context else ''
            greeting = f"Hi {user_name}! " if user_name else "Hi! "
            return f"{greeting}How can I help with TeBSTrack?"
        
        # If we have ticket context and user wants ticket details
        if ticket_context and intent.get('needs_ticket_details', False):
            return f"""Ticket #{ticket_context.get('id', 'N/A')}: {ticket_context.get('subject', 'No subject')}
Status: {ticket_context.get('status', 'Unknown')} | Category: {ticket_context.get('category', 'N/A')} | Urgency: {ticket_context.get('urgency', 'N/A')}
Requested by: {ticket_context.get('sender', 'Unknown')} | Created: {ticket_context.get('created_at', 'Unknown')}
Assigned: {ticket_context.get('assigned_to', 'Unassigned')}

This ticket was auto-created from an email to the infra mailbox."""
        
        # Brief acknowledgment if viewing ticket but not asking for details
        elif ticket_context:
            user_name = user_context.get('username', '') if user_context else ''
            greeting = f"{user_name}, I" if user_name else "I"
            return f"{greeting} can see you're viewing Ticket #{ticket_context.get('id', 'N/A')} from {ticket_context.get('sender', 'unknown requester')}. How can I help you resolve this?"
        
        # General responses when no ticket context
        else:
            user_name = user_context.get('username', '') if user_context else ''
            greeting = f"Hi {user_name}! I'm" if user_name else "I'm"
            return f"{greeting} your TeBSTrack assistant, here to help the infra team manage tickets and resolve user requests efficiently."

    def _build_chatbot_system_prompt(self, user_message: str, has_ticket_context: bool, intent: Dict[str, bool], user_context: Optional[Dict] = None) -> str:
        """Build an appropriate system prompt based on the user's question and context"""
        
        # Build user information section
        user_info = ""
        if user_context:
            username = user_context.get('username', 'Unknown')
            role = user_context.get('role', 'user')
            user_info = f"""

CURRENT USER:
- Username: {username}
- Role: {role}
- You are assisting this user with their question"""
        
        base_prompt = f"""You are TeBSTrack Assistant, an AI helper for the TeBSTrack Infrastructure Ticketing System.

SYSTEM CONTEXT:
TeBSTrack is an infrastructure team ticketing system where:
- External users/employees send requests to an "infra mailbox" 
- The system automatically creates tickets from these emails
- Infra team members (TeBSTrack users) view, track, and resolve these tickets
- You assist infra team members in managing their workflow

KNOWLEDGE BASE USAGE:
- You have access to a comprehensive infrastructure knowledge base
- ALWAYS reference the knowledge base when answering questions about procedures, solutions, or troubleshooting
- Provide specific guidance from the knowledge base for different ticket categories
- When users ask "how to" questions, refer to documented procedures
- For technical issues, suggest knowledge base solutions and troubleshooting steps

USER CONTEXT:
- TeBSTrack users are infra team members responsible for resolving tickets
- Ticket requesters are external users who sent emails to the infra mailbox
- When viewing tickets, the "REQUEST BY" field shows who sent the original email request{user_info}"""
        
        if intent.get('is_casual', False):
            # Handle casual conversation
            return base_prompt + """

CASUAL MODE: Keep responses friendly and brief (1-2 sentences). Be conversational but helpful."""
            
        elif has_ticket_context and intent.get('needs_ticket_details', False):
            # User wants detailed ticket information
            return base_prompt + """

INFRA TEAM TICKET ANALYSIS MODE: 
- Use the COMPLETE TICKET INFORMATION provided
- ACTIVELY reference the KNOWLEDGE BASE for category-specific solutions and procedures
- Focus on helping the infra team member understand and resolve the request
- The "REQUEST BY" field shows the external user who sent the email to infra mailbox
- This ticket was auto-created from an email request
- Provide actionable insights for resolving infrastructure requests using knowledge base guidance
- When asked "who created/requested/sent this", refer to the email sender
- When asked "who, not when" - focus ONLY on the requester, don't mention dates
- Help the infra team member understand what needs to be done using documented procedures"""
            
        elif has_ticket_context:
            # User is viewing a ticket but asking general questions
            return base_prompt + """

INFRA TEAM CONTEXT-AWARE MODE: 
- Use the COMPLETE TICKET INFORMATION to help the infra team member
- Reference the KNOWLEDGE BASE for relevant procedures and solutions
- The "REQUEST BY" field shows the external user who emailed the infra mailbox
- This ticket was auto-created from an email request
- Provide helpful insights for infrastructure team workflow using knowledge base guidance
- Reference ticket details when relevant to assist in resolution"""
            
        else:
            # General assistance
            return base_prompt + """

INFRA TEAM HELP MODE: Provide clear, helpful answers about TeBSTrack features and infrastructure team workflow. Actively use the KNOWLEDGE BASE to answer questions about procedures, troubleshooting, and solutions. Help infra team members manage tickets and resolve user requests efficiently using documented guidance."""

    def recommend_email_template(self, ticket_subject: str, ticket_description: str, ticket_category: str = None) -> Dict[str, any]:
        """
        Use AI to recommend the most appropriate email template for a ticket
        """
        from .models import EmailTemplate
        
        # Get available templates from database
        active_templates = EmailTemplate.query.filter_by(is_active=True).all()
        if not active_templates:
            return {
                "recommended_template": None,
                "confidence": 0.0,
                "reasoning": "No email templates configured in the system",
                "templates_available": []
            }
        
        # Build templates description for AI
        templates_info = {}
        for template in active_templates:
            templates_info[template.name] = {
                "subject": template.subject,
                "use_case": template.use_case_description or "General use",
                "body_preview": template.body[:200] + "..." if len(template.body) > 200 else template.body
            }
        
        # Get template selection guidance from system settings
        template_guide = self._get_template_selection_guide()
        
        prompt = f"""
Analyze this support ticket and recommend the most appropriate email template:

TICKET INFORMATION:
Subject: {ticket_subject}
Description: {ticket_description}
Category: {ticket_category or "Not specified"}

AVAILABLE EMAIL TEMPLATES:
{json.dumps(templates_info, indent=2)}

TEMPLATE SELECTION GUIDE:
{template_guide}

ANALYSIS REQUIREMENTS:
1. Match ticket content to template purpose and use cases
2. Consider the specific request type and category
3. Look for keywords that indicate template relevance  
4. Evaluate how well each template would address the user's request
5. If no template is clearly suitable, explain why

Respond with JSON:
{{
    "recommended_template": "exact template name or null",
    "confidence": 0.85,
    "reasoning": "detailed explanation of why this template fits or why no template is suitable",
    "alternative_templates": ["list of other potentially relevant templates"],
    "template_match_score": 0.85
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert email template recommendation system. Analyze support tickets and suggest the most appropriate response template based on content analysis and use case matching."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for consistent recommendations
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result["templates_available"] = [t.name for t in active_templates]
            return result
            
        except Exception as e:
            logging.error(f"Template recommendation failed: {e}")
            return {
                "recommended_template": None,
                "confidence": 0.0,
                "reasoning": f"AI recommendation failed: {str(e)}",
                "templates_available": [t.name for t in active_templates],
                "alternative_templates": [],
                "template_match_score": 0.0
            }

    def _get_template_selection_guide(self) -> str:
        """Get the template selection guide from system settings"""
        from .models import SystemSettings, EmailTemplate
        
        guide = SystemSettings.get_setting('email_template_guide', '')
        if not guide:
            # Generate dynamic guide based on available templates
            active_templates = EmailTemplate.query.filter_by(is_active=True).all()
            
            if active_templates:
                guide = "TEMPLATE SELECTION GUIDELINES:\n\n"
                
                for i, template in enumerate(active_templates, 1):
                    use_case = template.use_case_description if template.use_case_description else f"Email template for general use"
                    guide += f"{i}. {template.name}: {use_case}\n"
                
                guide += """
SELECTION CRITERIA:
- Match specific keywords in the request to template purpose
- Consider the technical complexity of the request
- Evaluate if the template provides appropriate information for the user's needs
- If multiple templates could work, choose the most specific one
- Only recommend a template if there's a clear match (confidence > 0.7)
"""
            else:
                guide = """
TEMPLATE SELECTION GUIDELINES:
No email templates are currently configured in the system.
Please contact the administrator to set up email templates.
"""
        
        return guide

    def generate_template_action_steps(self, template_name: str, ticket_context: Dict[str, any]) -> List[Dict[str, any]]:
        """
        Generate AI-suggested action steps for a template based on ticket context
        """
        from .models import EmailTemplate, TemplateActionStep
        
        # Get the template and its existing action steps
        template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
        if not template:
            return []
        
        existing_steps = TemplateActionStep.query.filter_by(template_id=template.id).order_by(TemplateActionStep.step_order).all()
        
        # If template has configured steps, return those with any dynamic content filled in
        if existing_steps:
            return self._customize_action_steps(existing_steps, ticket_context)
        
        # If no configured steps, generate AI suggestions
        return self._generate_ai_action_steps(template, ticket_context)

    def _customize_action_steps(self, steps: List, ticket_context: Dict[str, any]) -> List[Dict[str, any]]:
        """Customize existing action steps with ticket-specific information"""
        customized_steps = []
        
        for step in steps:
            step_data = {
                "id": step.id,
                "order": step.step_order,
                "type": step.step_type,
                "title": step.step_title,
                "description": step.step_description,
                "is_automated": step.is_automated,
                "config": json.loads(step.step_config) if step.step_config else {}
            }
            
            # Customize step description with ticket context
            step_data["description"] = self._apply_ticket_variables(step_data["description"], ticket_context)
            
            customized_steps.append(step_data)
        
        return customized_steps

    def _apply_ticket_variables(self, text: str, ticket_context: Dict[str, any]) -> str:
        """Apply ticket variables to step descriptions"""
        variables = {
            "{user_email}": ticket_context.get("sender", "user@example.com"),
            "{username}": ticket_context.get("sender", "user@example.com").split("@")[0] if "@" in ticket_context.get("sender", "") else "username",
            "{ticket_id}": str(ticket_context.get("id", "N/A")),
            "{subject}": ticket_context.get("subject", ""),
            "{category}": ticket_context.get("category", "")
        }
        
        result = text
        for var, value in variables.items():
            result = result.replace(var, value)
        
        return result

    def _generate_ai_action_steps(self, template, ticket_context: Dict[str, any]) -> List[Dict[str, any]]:
        """Generate AI-suggested action steps when none are configured"""
        
        prompt = f"""
Generate specific action steps for resolving this support ticket using the "{template.name}" email template:

TICKET DETAILS:
Subject: {ticket_context.get('subject', '')}
Description: {ticket_context.get('description', '')}
Category: {ticket_context.get('category', '')}
Requested by: {ticket_context.get('sender', '')}

TEMPLATE INFORMATION:
Name: {template.name}
Purpose: {template.use_case_description}
Email Subject: {template.subject}

Generate 3-5 specific, actionable steps that an infrastructure team member should take to resolve this request. Focus on practical actions, not just "send email".

Respond with JSON:
{{
    "action_steps": [
        {{
            "order": 1,
            "title": "Step Title",
            "description": "Detailed description of what to do",
            "type": "manual",
            "is_automated": false
        }}
    ]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an IT workflow expert. Generate specific, actionable steps for infrastructure team members to resolve support requests."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("action_steps", [])
            
        except Exception as e:
            logging.error(f"Action step generation failed: {e}")
            return [
                {
                    "order": 1,
                    "title": f"Process {template.name} Request",
                    "description": f"Follow standard procedure for {template.name.lower()} as described in the email template.",
                    "type": "manual",
                    "is_automated": False
                }
            ]


# Global AI service instance (lazy-loaded)
_ai_service = None

def get_ai_service():
    """Get the global AI service instance (lazy-loaded)."""
    global _ai_service
    if _ai_service is None:
        _ai_service = TeBSTrackAI()
    return _ai_service

def reset_ai_service():
    """Reset the AI service instance (useful when API key changes)."""
    global _ai_service
    _ai_service = None
