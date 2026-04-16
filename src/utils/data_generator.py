"""
Random Data Generator Module
Generates random Salesforce opportunities and cases for email sending
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional


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

    # Personal wellbeing snippets to make emails feel more human
    PERSONAL_WELLBEING_SNIPPETS = [
        "Hope you're having a good week and finding a bit of time to breathe between all the project work.",
        "I know things have been busy on your side, so I appreciate you taking a moment to review this.",
        "I hope everything is going well with your team and that you're not overloaded with back-to-back meetings.",
        "Trust you're doing well and settling into the new quarter smoothly.",
        "Hope your week is going okay and that you managed to get some downtime over the weekend."
    ]

    # Product-related business story snippets (trial feedback, questions, issues, demo interest)
    PRODUCT_STORY_SNIPPETS = [
        (
            "We have started to see more usage from the recent product trials, and a few teams have "
            "already shared detailed feedback about what is working well and what still feels confusing. "
            "Some users are especially interested in how the reporting and analytics behave under real "
            "load, while others are focusing more on day-to-day usability and how quickly new team "
            "members can ramp up."
        ),
        (
            "Over the last couple of weeks we have received a steady stream of questions about specific "
            "product capabilities, pricing options and how integrations would look in a real deployment. "
            "A lot of the conversations centre around how flexible the configuration is and what it would "
            "take to adapt the solution to each team's existing processes without forcing a big redesign."
        ),
        (
            "Support has logged a handful of product issues from early adopters, mostly around edge cases "
            "and advanced configurations rather than basic functionality. We are tracking these closely, "
            "prioritising fixes where they block evaluation, and making sure we keep everyone updated on "
            "expected timelines so trials can continue without unnecessary disruption."
        ),
        (
            "We are also seeing increased interest in scheduling tailored product demos for different "
            "stakeholder groups. Some teams want a high-level walkthrough focused on outcomes and roadmap, "
            "while others prefer a deeper technical session where we can explore architecture, security "
            "and how the solution would fit into their existing environment."
        )
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

    def generate_business_emails(self, count: int, topic_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Generate random business emails distributed across selected types.

        Args:
            count: Total number of business emails to generate
            topic_types: If provided, only these types are used. If None or empty, all 9 types are used.

        Returns:
            List of business email dictionaries with 'type' and 'data' keys
        """
        emails = []

        # All 9 valid types
        all_types = [
            'meeting_invitation',
            'followup',
            'thank_you',
            'project_update',
            'reminder',
            'trial_feedback',
            'product_queries',
            'product_issues',
            'demo_enquiry'
        ]

        # Use selected types or all
        if topic_types:
            email_types = [t for t in topic_types if t in all_types]
        if not topic_types or not email_types:
            email_types = all_types

        num_types = len(email_types)
        per_type = count // num_types
        remainder = count % num_types

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
                elif email_type == 'trial_feedback':
                    emails.append(self._generate_trial_feedback())
                elif email_type == 'product_queries':
                    emails.append(self._generate_product_queries())
                elif email_type == 'product_issues':
                    emails.append(self._generate_product_issues())
                elif email_type == 'demo_enquiry':
                    emails.append(self._generate_demo_enquiry())

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
        organizer = self._random_name()
        recipient = self._random_name()

        return {
            'type': 'meeting_invitation',
            'subject': f"Invitation: {subject}",
            'meeting_title': subject,
            'date': date,
            'time': time_slot,
            'location': location,
            'organizer': organizer,
            'agenda': self._generate_meeting_agenda(),
            'recipient_name': recipient,
            'sender_name': organizer,
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"We'd like to use this session to walk through your current use of the product, "
                f"discuss any feedback from the trial so far, and answer questions about how it would "
                f"fit into your team's day-to-day work. "
                f"{random.choice(self.PRODUCT_STORY_SNIPPETS)}"
            )
        }

    def _generate_followup(self) -> Dict:
        """Generate a follow-up email"""
        context = random.choice(self.FOLLOWUP_CONTEXTS)
        sender = self._random_name()
        recipient = self._random_name()

        return {
            'type': 'followup',
            'subject': f"Following up on {context.split(' ', 1)[1] if ' ' in context else 'our discussion'}",
            'context': context,
            'sender': sender,
            'action_items': self._generate_action_items(),
            'next_steps': self._generate_next_steps(),
            'recipient_name': recipient,
            'sender_name': sender,
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"I just wanted to circle back on {context} and make sure you have everything you "
                f"need from our side. If new questions have come up from your team about the product, "
                f"trial configuration or potential rollout plan, I'm happy to address them or schedule "
                f"a deeper session. "
                f"{random.choice(self.PRODUCT_STORY_SNIPPETS)}"
            )
        }

    def _generate_thank_you(self) -> Dict:
        """Generate a thank you email"""
        reason = random.choice(self.THANKYOU_REASONS)
        sender = self._random_name()
        recipient = self._random_name()

        return {
            'type': 'thank_you',
            'subject': f"Thank you for {reason.split(' ', 1)[1] if ' ' in reason else reason}",
            'reason': reason,
            'sender': sender,
            'company': random.choice(self.COMPANY_NAMES),
            'additional_note': self._generate_thank_you_note(),
            'recipient_name': recipient,
            'sender_name': sender,
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"It really means a lot that you chose to explore the product with us and share "
                f"honest feedback. Input from you and your team helps us shape the roadmap, "
                f"prioritise improvements, and make sure we're solving real problems in a way that "
                f"fits naturally into your business. "
                f"{random.choice(self.PRODUCT_STORY_SNIPPETS)}"
            )
        }

    def _generate_project_update(self) -> Dict:
        """Generate a project update email"""
        milestone = random.choice(self.PROJECT_MILESTONES)
        project_name = f"{random.choice(self.OPPORTUNITY_TYPES)} Project"
        manager = self._random_name()
        recipient = self._random_name()

        return {
            'type': 'project_update',
            'subject': f"Project Update: {milestone}",
            'project_name': project_name,
            'milestone': milestone,
            'completion': random.choice([60, 70, 75, 80, 85, 90]),
            'next_milestone': random.choice(self.PROJECT_MILESTONES),
            'manager': manager,
            'status': random.choice(["On Track", "Ahead of Schedule", "Needs Attention"]),
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"From a project perspective, we're steadily moving through the current milestone "
                f"and starting to plan the next phase of the rollout. If there are any risks on your "
                f"side (resourcing, timelines, competing initiatives), this is a great time to surface "
                f"them so we can keep things on track together. "
                f"{random.choice(self.PRODUCT_STORY_SNIPPETS)}"
            ),
            'recipient_name': recipient,
            'sender_name': manager
        }

    def _generate_reminder(self) -> Dict:
        """Generate a reminder email"""
        reminder_type = random.choice(self.REMINDER_TYPES)
        sender = self._random_name()
        recipient = self._random_name()

        return {
            'type': 'reminder',
            'subject': f"Reminder: {reminder_type.split(' ', 2)[-1] if len(reminder_type.split(' ')) > 2 else reminder_type}",
            'reminder_about': reminder_type,
            'due_date': self._random_future_date(days_range=7),
            'priority': random.choice(["Normal", "High", "Urgent"]),
            'sender': sender,
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"This is just a friendly reminder about the {reminder_type}. If priorities have shifted "
                f"or you need more time to collect feedback from the trial or review open issues, "
                f"please let me know and we can adjust the plan together. "
                f"{random.choice(self.PRODUCT_STORY_SNIPPETS)}"
            ),
            'recipient_name': recipient,
            'sender_name': sender
        }

    def _generate_trial_feedback(self) -> Dict:
        """Generate a product trial feedback email"""
        sender = self._random_name()
        recipient = self._random_name()
        return {
            'type': 'trial_feedback',
            'subject': random.choice([
                "Product trial feedback",
                "Following up on your trial feedback",
                "Your feedback on the product trial",
            ]),
            'recipient_name': recipient,
            'sender_name': sender,
            'title': 'Product Trial Feedback',
            'message': "Thank you for trying the product. We'd like to hear how it's going.",
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"We have started to see more usage from the recent product trials, and a few teams have "
                f"already shared detailed feedback about what is working well and what still feels confusing. "
                f"Some users are especially interested in how the reporting and analytics behave under real "
                f"load, while others are focusing more on day-to-day usability and how quickly new team "
                f"members can ramp up. We would value your input so we can keep improving."
            )
        }

    def _generate_product_queries(self) -> Dict:
        """Generate a product queries email"""
        sender = self._random_name()
        recipient = self._random_name()
        return {
            'type': 'product_queries',
            'subject': random.choice([
                "Queries regarding the product",
                "Your questions about the product",
                "Product capabilities and pricing",
            ]),
            'recipient_name': recipient,
            'sender_name': sender,
            'title': 'Queries Regarding the Product',
            'message': "Here are some answers to the questions you raised about the product.",
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"Over the last couple of weeks we have received a steady stream of questions about specific "
                f"product capabilities, pricing options and how integrations would look in a real deployment. "
                f"A lot of the conversations centre around how flexible the configuration is and what it would "
                f"take to adapt the solution to each team's existing processes without forcing a big redesign. "
                f"Happy to schedule a call if you have more questions."
            )
        }

    def _generate_product_issues(self) -> Dict:
        """Generate a product issues email"""
        sender = self._random_name()
        recipient = self._random_name()
        return {
            'type': 'product_issues',
            'subject': random.choice([
                "Issues in the product – update",
                "Product issue follow-up",
                "Update on reported product issues",
            ]),
            'recipient_name': recipient,
            'sender_name': sender,
            'title': 'Product Issues Update',
            'message': "We wanted to give you an update on the product issues you reported.",
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"Support has logged a handful of product issues from early adopters, mostly around edge cases "
                f"and advanced configurations rather than basic functionality. We are tracking these closely, "
                f"prioritising fixes where they block evaluation, and making sure we keep everyone updated on "
                f"expected timelines so trials can continue without unnecessary disruption. We will reach out "
                f"again once a fix is available."
            )
        }

    def _generate_demo_enquiry(self) -> Dict:
        """Generate an enquiry for product demo email"""
        sender = self._random_name()
        recipient = self._random_name()
        return {
            'type': 'demo_enquiry',
            'subject': random.choice([
                "Enquiry for product demo",
                "Product demo – next steps",
                "Scheduling your product demo",
            ]),
            'recipient_name': recipient,
            'sender_name': sender,
            'title': 'Enquiry for Product Demo',
            'message': "Thank you for your interest in a product demo. We would be glad to arrange one.",
            'custom_message': (
                f"{random.choice(self.PERSONAL_WELLBEING_SNIPPETS)} "
                f"We are seeing increased interest in scheduling tailored product demos for different "
                f"stakeholder groups. Some teams want a high-level walkthrough focused on outcomes and roadmap, "
                f"while others prefer a deeper technical session where we can explore architecture, security "
                f"and how the solution would fit into your existing environment. Let us know your preference "
                f"and we will send a calendar invite."
            )
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
