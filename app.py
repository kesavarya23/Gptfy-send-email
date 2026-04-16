"""
Salesforce Email Sender - Web UI
Simple web interface for sending emails
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import sys
import secrets
import os
import time
sys.path.append('src')

from agent import EmailAgent
from utils.data_generator import DataGenerator
from utils.email_generator import EmailGenerator

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)  # Enable CORS for all routes


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/send_emails', methods=['POST'])
def send_emails():
    """Send emails endpoint"""
    try:
        # Get form data
        data = request.json

        sender_email = data.get('sender_email')
        sender_password = data.get('sender_password')
        sender_name = data.get('sender_name', sender_email)
        recipient_email = data.get('recipient_email')
        num_opportunities = int(data.get('num_opportunities', 0))
        num_cases = int(data.get('num_cases', 0))
        num_business = int(data.get('num_business', 0))
        topic_mode = data.get('topic_mode', 'default')
        selected_topics = data.get('selected_topics') or []
        custom_message = data.get('custom_message', 'Please review this Salesforce data.')
        # Delay between emails in seconds (0 = no delay)
        try:
            delay_seconds = int(data.get('delay_seconds', 0) or 0)
        except (TypeError, ValueError):
            delay_seconds = 0

        # Validation
        if not sender_email or not sender_password or not recipient_email:
            return jsonify({
                'success': False,
                'error': 'Please fill in all required fields'
            })

        if num_opportunities == 0 and num_cases == 0 and num_business == 0:
            return jsonify({
                'success': False,
                'error': 'Please specify at least 1 opportunity, case, or business email'
            })

        if num_business > 0 and topic_mode == 'custom' and not selected_topics:
            return jsonify({
                'success': False,
                'error': 'Please select at least one topic when using Custom mode'
            })

        # Initialize services
        data_generator = DataGenerator()
        agent = EmailAgent(
            sender_email=sender_email,
            sender_password=sender_password,
            sender_name=sender_name
        )
        email_generator = EmailGenerator()

        results = []
        all_emails = []

        # Generate and send opportunities
        if num_opportunities > 0:
            opportunities = data_generator.generate_opportunities(num_opportunities)

            for i, opp in enumerate(opportunities, 1):
                try:
                    email_content = email_generator.generate_opportunity_email(
                        opportunity_data=opp,
                        custom_message=custom_message
                    )

                    success = agent.email_service.send_email(
                        to_email=recipient_email,
                        subject=email_content['subject'],
                        html_content=email_content['html_content'],
                        plain_text=email_content.get('plain_text')
                    )

                    all_emails.append({
                        'type': 'Opportunity',
                        'name': opp['opportunity_name'],
                        'status': 'Sent' if success else 'Failed',
                        'number': i
                    })

                except Exception as e:
                    all_emails.append({
                        'type': 'Opportunity',
                        'name': opp.get('opportunity_name', 'Unknown'),
                        'status': 'Failed',
                        'error': str(e),
                        'number': i
                    })

                # Delay between emails if configured
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

        # Generate and send cases
        if num_cases > 0:
            cases = data_generator.generate_cases(num_cases)

            for i, case in enumerate(cases, 1):
                try:
                    email_content = email_generator.generate_case_email(
                        case_data=case,
                        custom_message=custom_message
                    )

                    success = agent.email_service.send_email(
                        to_email=recipient_email,
                        subject=email_content['subject'],
                        html_content=email_content['html_content'],
                        plain_text=email_content.get('plain_text')
                    )

                    all_emails.append({
                        'type': 'Case',
                        'name': f"Case {case['case_number']}",
                        'status': 'Sent' if success else 'Failed',
                        'number': i
                    })

                except Exception as e:
                    all_emails.append({
                        'type': 'Case',
                        'name': f"Case {case.get('case_number', 'Unknown')}",
                        'status': 'Failed',
                        'error': str(e),
                        'number': i
                    })

                # Delay between emails if configured
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

        # Generate and send business emails
        if num_business > 0:
            topic_types = selected_topics if topic_mode == 'custom' and selected_topics else None
            business_emails = data_generator.generate_business_emails(num_business, topic_types=topic_types)

            for i, business_email in enumerate(business_emails, 1):
                try:
                    email_content = email_generator.generate_business_email(business_email)

                    success = agent.email_service.send_email(
                        to_email=recipient_email,
                        subject=email_content['subject'],
                        html_content=email_content['html_content'],
                        plain_text=email_content.get('plain_text')
                    )

                    # Friendly type names
                    type_names = {
                        'meeting_invitation': 'Meeting Invitation',
                        'followup': 'Follow-up',
                        'thank_you': 'Thank You',
                        'project_update': 'Project Update',
                        'reminder': 'Reminder',
                        'trial_feedback': 'Product Trial Feedback',
                        'product_queries': 'Product Queries',
                        'product_issues': 'Product Issues',
                        'demo_enquiry': 'Demo Enquiry',
                    }

                    all_emails.append({
                        'type': type_names.get(business_email['type'], business_email['type']),
                        'name': email_content['subject'],
                        'status': 'Sent' if success else 'Failed',
                        'number': i
                    })

                except Exception as e:
                    all_emails.append({
                        'type': 'Business Email',
                        'name': business_email.get('subject', 'Unknown'),
                        'status': 'Failed',
                        'error': str(e),
                        'number': i
                    })

                # Delay between emails if configured
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

        # Calculate summary
        total_sent = sum(1 for email in all_emails if email['status'] == 'Sent')
        total_failed = len(all_emails) - total_sent

        return jsonify({
            'success': True,
            'summary': {
                'total': len(all_emails),
                'sent': total_sent,
                'failed': total_failed,
                'success_rate': round((total_sent / len(all_emails) * 100), 1) if all_emails else 0
            },
            'emails': all_emails
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    print("="*70)
    print("SALESFORCE EMAIL SENDER - WEB UI")
    print("="*70)
    print()
    print("Starting web server...")
    print("Open your browser and go to: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("="*70)

    app.run(debug=True, host='0.0.0.0', port=5000)
