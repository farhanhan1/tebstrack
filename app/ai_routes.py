"""
AI-related routes for TeBSTrack
Add these routes to your main routes.py file
"""

from flask import request, jsonify
from .ai_service import ai_service

# Add these routes to your main routes.py file

@main.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot_api():
    """API endpoint for chatbot conversations"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        ticket_context = data.get('ticket_context')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
            
        response = ai_service.chatbot_response(user_message, ticket_context)
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        logging.error(f"Chatbot API error: {e}")
        return jsonify({
            'error': 'An error occurred processing your request',
            'status': 'error'
        }), 500

@main.route('/api/ai/categorize', methods=['POST'])
@login_required
def ai_categorize_ticket():
    """API endpoint for AI ticket categorization"""
    try:
        data = request.get_json()
        subject = data.get('subject', '')
        description = data.get('description', '')
        
        if not subject and not description:
            return jsonify({'error': 'Subject or description is required'}), 400
            
        result = ai_service.categorize_ticket(subject, description)
        
        return jsonify({
            'result': result,
            'status': 'success'
        })
        
    except Exception as e:
        logging.error(f"AI categorization error: {e}")
        return jsonify({
            'error': 'An error occurred during categorization',
            'status': 'error'
        }), 500

@main.route('/api/ai/recommend-template', methods=['POST'])
@login_required
def ai_recommend_template():
    """API endpoint for email template recommendation"""
    try:
        data = request.get_json()
        subject = data.get('subject', '')
        description = data.get('description', '')
        category = data.get('category', '')
        
        result = ai_service.recommend_email_template(subject, description, category)
        
        return jsonify({
            'result': result,
            'status': 'success'
        })
        
    except Exception as e:
        logging.error(f"Template recommendation error: {e}")
        return jsonify({
            'error': 'An error occurred during template recommendation',
            'status': 'error'
        }), 500
