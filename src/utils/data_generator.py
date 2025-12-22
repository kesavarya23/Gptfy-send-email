"""
Random Data Generator Module
Generates random Salesforce opportunities and cases for email sending
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict


class DataGenerator:
    """Generate random Salesforce data"""

    # Sample data for generating realistic records
    COMPANY_NAMES = [
        "Acme Corporation", "TechStart Inc", "Global Finance Ltd", "Innovate Systems",
        "Digital Solutions Co", "Enterprise Tech", "Cloud Nine Services", "NextGen Software",
        "Alpha Industries", "Beta Technologies", "Gamma Enterprises", "Delta Corp",
        "Epsilon Solutions", "Zeta Systems", "Theta Technologies", "Omega Industries",
        "Quantum Computing Inc", "Cyber Security Pro", "Data Analytics Group", "AI Solutions Ltd",
        "BlockChain Ventures", "IoT Innovations", "Smart Automation", "Digital Transformation Co",
        "Future Tech Systems", "Advanced Analytics", "CloudFirst Solutions", "Mobile First Inc"
    ]

    OPPORTUNITY_TYPES = [
        "Cloud Migration", "CRM Implementation", "Security Audit", "Data Analytics Platform",
        "Mobile App Development", "API Integration", "Infrastructure Upgrade", "Digital Transformation",
        "AI/ML Implementation", "System Integration", "Legacy Modernization", "DevOps Setup",
        "Consulting Services", "Training Program", "Support Package", "License Renewal"
    ]

    STAGES = [
        "Prospecting", "Qualification", "Needs Analysis", "Value Proposition",
        "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"
    ]

    CASE_TYPES = [
        "Technical Issue", "Bug Report", "Feature Request", "Account Question",
        "Billing Issue", "Performance Problem", "Configuration Help", "Training Request",
        "Integration Issue", "Access Problem", "Data Issue", "Security Concern"
    ]

    CASE_SUBJECTS = [
        "Unable to access dashboard", "System performance is slow", "Error message on login",
        "Missing data in reports", "Export functionality not working", "Email notifications not received",
        "Integration with external system failing", "User permissions need updating",
        "Request for additional licenses", "Data migration assistance needed",
        "Custom field not displaying", "Workflow automation not triggering",
        "API rate limit exceeded", "Mobile app crashes on startup"
    ]

    CASE_STATUSES = ["New", "In Progress", "Escalated", "Waiting for Customer", "Resolved", "Closed"]

    PRIORITIES = ["Low", "Medium", "High", "Critical"]

    ORIGINS = ["Web", "Email", "Phone", "Chat", "Social Media"]

    # Business Email Data
    MEETING_SUBJECTS = [
        "Quarterly Business Review", "Project Kickoff Meeting", "Sprint Planning Session",
        "Budget Review Meeting", "Strategy Discussion", "Product Roadmap Review",
        "Team Sync", "Client Check-in", "Executive Briefing", "Technical Deep Dive"
    ]

    FOLLOWUP_CONTEXTS = [
        "our last conversation about the project timeline",
        "the demo we conducted last week",
        "your inquiry about our services",
        "the proposal we sent",
        "our discussion regarding pricing",
        "the technical requirements you shared",
        "the meeting we had yesterday",
        "your questions about implementation"
    ]

    THANKYOU_REASONS = [
        "attending our product demonstration",
        "choosing our services for your project",
        "your partnership and continued trust",
        "taking the time to meet with our team",
        "your valuable feedback on our proposal",
        "participating in our webinar",
        "your recent purchase",
        "referring us to your colleagues"
    ]

    PROJECT_MILESTONES = [
        "Phase 1 Discovery Completed", "Design Review Finished", "Development Sprint 2 Complete",
        "User Acceptance Testing Started", "Go-Live Preparation", "System Integration Complete",
        "Data Migration Finished", "Training Materials Ready", "Performance Testing Done",
        "Security Audit Passed"
    ]

    REMINDER_TYPES = [
        "upcoming deadline for project deliverables",
        "scheduled maintenance window this weekend",
        "contract renewal coming up next month",
        "required training session next week",
        "pending approval on the proposal",
        "outstanding invoice payment",
        "security compliance certification expiring",
        "quarterly report submission due"
    ]

    CONTACT_FIRST_NAMES = [
        "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
        "James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Thomas", "Linda"
    ]

    CONTACT_LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Taylor", "Thomas"
    ]

    DESCRIPTIONS = [
        "Customer requires immediate attention to resolve critical business issues.",
        "Comprehensive solution needed to address current and future business needs.",
        "Strategic initiative to improve operational efficiency and reduce costs.",
        "High-priority project with tight deadline and executive sponsorship.",
        "Opportunity to expand existing relationship and increase revenue.",
        "Technical evaluation required before proceeding with implementation.",
        "Budget approved and stakeholders aligned on project scope.",
        "Competitive situation requiring compelling value proposition."
    ]

    def __init__(self, seed: int = None):
        """
        Initialize data generator

        Args:
            seed: Random seed for reproducibility (optional)
        """
        if seed:
            random.seed(seed)

    def generate_opportunities(self, count: int) -> List[Dict]:
        """
        Generate random opportunity records

        Args:
            count: Number of opportunities to generate

        Returns:
            List of opportunity dictionaries
        """
        opportunities = []

        for i in range(count):
            company = random.choice(self.COMPANY_NAMES)
            opp_type = random.choice(self.OPPORTUNITY_TYPES)

            opportunity = {
                'opportunity_name': f"{opp_type} - {company}",
                'account_name': company,
                'stage': random.choice(self.STAGES),
                'amount': random.randint(10, 500) * 1000,  # $10k to $500k
                'close_date': self._random_future_date(days_range=90),
                'probability': random.choice([10, 25, 50, 60, 75, 90, 100]),
                'owner_name': self._random_name(),
                'description': random.choice(self.DESCRIPTIONS),
                'next_steps': self._generate_next_steps()
            }

            opportunities.append(opportunity)

        return opportunities

    def generate_cases(self, count: int) -> List[Dict]:
        """
        Generate random case records

        Args:
            count: Number of cases to generate

        Returns:
            List of case dictionaries
        """
        cases = []

        for i in range(count):
            case_number = f"{random.randint(10000, 99999):05d}"

            case = {
                'case_number': case_number,
                'subject': random.choice(self.CASE_SUBJECTS),
                'status': random.choice(self.CASE_STATUSES),
                'priority': random.choice(self.PRIORITIES),
                'type': random.choice(self.CASE_TYPES),
                'origin': random.choice(self.ORIGINS),
                'account_name': random.choice(self.COMPANY_NAMES),
                'contact_name': self._random_name(),
                'owner_name': self._random_name(),
                'description': self._generate_case_description(),
                'resolution': self._generate_resolution() if random.random() > 0.5 else "",
                'created_date': self._random_past_date(days_range=30)
            }

            cases.append(case)

        return cases

    def generate_mixed(self, opportunity_count: int, case_count: int) -> Dict[str, List[Dict]]:
        """
        Generate both opportunities and cases

        Args:
            opportunity_count: Number of opportunities
            case_count: Number of cases

        Returns:
            Dictionary with 'opportunities' and 'cases' keys
        """
        return {
            'opportunities': self.generate_opportunities(opportunity_count),
            'cases': self.generate_cases(case_count)
        }

    def _random_name(self) -> str:
        """Generate a random full name"""
        first = random.choice(self.CONTACT_FIRST_NAMES)
        last = random.choice(self.CONTACT_LAST_NAMES)
        return f"{first} {last}"

    def _random_future_date(self, days_range: int = 90) -> str:
        """Generate a random future date"""
        days = random.randint(1, days_range)
        future_date = datetime.now() + timedelta(days=days)
        return future_date.strftime('%Y-%m-%d')

    def _random_past_date(self, days_range: int = 30) -> str:
        """Generate a random past date"""
        days = random.randint(1, days_range)
        past_date = datetime.now() - timedelta(days=days)
        return past_date.strftime('%Y-%m-%d')

    def _generate_next_steps(self) -> str:
        """Generate random next steps for opportunities"""
        steps = [
            "Schedule follow-up call with decision maker",
            "Send detailed proposal and pricing",
            "Arrange technical demo for stakeholders",
            "Obtain executive approval for budget",
            "Finalize contract terms and conditions",
            "Conduct discovery session with team",
            "Present ROI analysis to leadership",
            "Schedule implementation planning meeting"
        ]
        return random.choice(steps)

    def _generate_case_description(self) -> str:
        """Generate random case description"""
        descriptions = [
            "Customer reports issue with system functionality. Initial investigation shows potential configuration problem.",
            "User experiencing performance degradation. System logs indicate high load during peak hours.",
            "Request for assistance with data migration from legacy system. Customer needs timeline and resource estimate.",
            "Critical issue impacting production environment. Customer requires immediate resolution.",
            "Question about product features and capabilities. Customer evaluating options for expansion.",
            "Technical error occurring consistently. Customer has provided detailed steps to reproduce.",
            "Access issue preventing user from completing work. Urgent resolution needed.",
            "Enhancement request to improve workflow efficiency. Customer suggests specific implementation."
        ]
        return random.choice(descriptions)

    def _generate_resolution(self) -> str:
        """Generate random case resolution"""
        resolutions = [
            "Issue resolved by updating configuration settings. Customer confirmed system working as expected.",
            "Root cause identified and permanent fix deployed. Monitoring for 24 hours to ensure stability.",
            "Provided workaround solution while permanent fix is developed. Target completion in next release.",
            "Training provided to user on correct process. Documentation updated to prevent future occurrences.",
            "Product limitation explained. Feature request submitted to development team for consideration.",
            "Access permissions corrected. User able to complete required tasks successfully.",
            "Bug fixed in latest patch. Customer upgraded and confirmed resolution.",
            "Escalated to engineering team. Custom solution developed and implemented."
        ]
        return random.choice(resolutions)

    def generate_business_emails(self, count: int) -> List[Dict]:
        """
        Generate random business emails distributed across 5 types
        Types: Meeting Invitation, Follow-up, Thank You, Project Update, Reminder

        Args:
            count: Total number of business emails to generate

        Returns:
            List of business email dictionaries with 'type' and 'data' keys
        """
        emails = []

        # Define email types
        email_types = [
            'meeting_invitation',
            'followup',
            'thank_you',
            'project_update',
            'reminder'
        ]

        # Distribute count evenly across types
        per_type = count // 5
        remainder = count % 5

        # Generate emails for each type
        for idx, email_type in enumerate(email_types):
            # Add one extra email to first types if there's remainder
            type_count = per_type + (1 if idx < remainder else 0)

            for _ in range(type_count):
                if email_type == 'meeting_invitation':
                    emails.append(self._generate_meeting_invitation())
                elif email_type == 'followup':
                    emails.append(self._generate_followup())
                elif email_type == 'thank_you':
                    emails.append(self._generate_thank_you())
                elif email_type == 'project_update':
                    emails.append(self._generate_project_update())
                elif email_type == 'reminder':
                    emails.append(self._generate_reminder())

        # Shuffle to mix types
        random.shuffle(emails)

        return emails

    def _generate_meeting_invitation(self) -> Dict:
        """Generate a meeting invitation email"""
        subject = random.choice(self.MEETING_SUBJECTS)
        date = self._random_future_date(days_range=14)
        time_slot = random.choice([
            "9:00 AM - 10:00 AM",
            "10:30 AM - 11:30 AM",
            "2:00 PM - 3:00 PM",
            "3:30 PM - 4:30 PM"
        ])
        location = random.choice([
            "Conference Room A",
            "Virtual (Teams)",
            "Virtual (Zoom)",
            "Office Building, Floor 3",
            "Client Site"
        ])

        return {
            'type': 'meeting_invitation',
            'subject': f"Invitation: {subject}",
            'meeting_title': subject,
            'date': date,
            'time': time_slot,
            'location': location,
            'organizer': self._random_name(),
            'agenda': self._generate_meeting_agenda()
        }

    def _generate_followup(self) -> Dict:
        """Generate a follow-up email"""
        context = random.choice(self.FOLLOWUP_CONTEXTS)

        return {
            'type': 'followup',
            'subject': f"Following up on {context.split(' ', 1)[1] if ' ' in context else 'our discussion'}",
            'context': context,
            'sender': self._random_name(),
            'action_items': self._generate_action_items(),
            'next_steps': self._generate_next_steps()
        }

    def _generate_thank_you(self) -> Dict:
        """Generate a thank you email"""
        reason = random.choice(self.THANKYOU_REASONS)

        return {
            'type': 'thank_you',
            'subject': f"Thank you for {reason.split(' ', 1)[1] if ' ' in reason else reason}",
            'reason': reason,
            'sender': self._random_name(),
            'company': random.choice(self.COMPANY_NAMES),
            'additional_note': self._generate_thank_you_note()
        }

    def _generate_project_update(self) -> Dict:
        """Generate a project update email"""
        milestone = random.choice(self.PROJECT_MILESTONES)
        project_name = f"{random.choice(self.OPPORTUNITY_TYPES)} Project"

        return {
            'type': 'project_update',
            'subject': f"Project Update: {milestone}",
            'project_name': project_name,
            'milestone': milestone,
            'completion': random.choice([60, 70, 75, 80, 85, 90]),
            'next_milestone': random.choice(self.PROJECT_MILESTONES),
            'manager': self._random_name(),
            'status': random.choice(["On Track", "Ahead of Schedule", "Needs Attention"])
        }

    def _generate_reminder(self) -> Dict:
        """Generate a reminder email"""
        reminder_type = random.choice(self.REMINDER_TYPES)

        return {
            'type': 'reminder',
            'subject': f"Reminder: {reminder_type.split(' ', 2)[-1] if len(reminder_type.split(' ')) > 2 else reminder_type}",
            'reminder_about': reminder_type,
            'due_date': self._random_future_date(days_range=7),
            'priority': random.choice(["Normal", "High", "Urgent"]),
            'sender': self._random_name()
        }

    def _generate_meeting_agenda(self) -> str:
        """Generate meeting agenda"""
        agendas = [
            "Review current project status\nDiscuss upcoming milestones\nAddress open issues\nQ&A session",
            "Quarterly results presentation\nFuture strategy discussion\nBudget review\nTeam feedback",
            "Sprint retrospective\nNext sprint planning\nResource allocation\nTechnical challenges",
            "Client requirements review\nProposal discussion\nTimeline and deliverables\nNext steps"
        ]
        return random.choice(agendas)

    def _generate_action_items(self) -> str:
        """Generate action items for follow-up"""
        items = [
            "Review the updated proposal\nProvide feedback by end of week\nSchedule next meeting",
            "Complete the requirements document\nShare with stakeholders\nConfirm budget approval",
            "Test the new features\nReport any issues\nApprove for production",
            "Review contract terms\nObtain legal approval\nSchedule signing meeting"
        ]
        return random.choice(items)

    def _generate_thank_you_note(self) -> str:
        """Generate additional thank you note"""
        notes = [
            "We truly appreciate your trust in our team and look forward to continuing our partnership.",
            "Your support means a lot to us. We're committed to delivering exceptional results.",
            "It was a pleasure working with you. We hope to collaborate again in the future.",
            "We value your business and are grateful for the opportunity to serve you."
        ]
        return random.choice(notes)
