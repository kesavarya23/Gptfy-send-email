"""
Salesforce Service Module
Handles Salesforce API integration for fetching opportunities and cases
"""

from simple_salesforce import Salesforce
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SalesforceService:
    """Service for interacting with Salesforce API"""

    def __init__(self, username: str, password: str, security_token: str, domain: str = 'login'):
        """
        Initialize Salesforce connection

        Args:
            username: Salesforce username
            password: Salesforce password
            security_token: Salesforce security token
            domain: 'login' for production, 'test' for sandbox
        """
        try:
            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
            logger.info("Successfully connected to Salesforce")
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {str(e)}")
            raise

    def get_opportunities(
        self,
        filters: Optional[Dict[str, str]] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch opportunities from Salesforce

        Args:
            filters: Dictionary of field filters (e.g., {'StageName': 'Prospecting'})
            limit: Maximum number of records to fetch

        Returns:
            List of opportunity dictionaries
        """
        try:
            # Build SOQL query
            query = """
                SELECT Id, Name, AccountId, Account.Name, StageName, Amount,
                       CloseDate, Probability, OwnerId, Owner.Name,
                       Description, NextStep, CreatedDate, LastModifiedDate
                FROM Opportunity
            """

            # Add filters if provided
            if filters:
                where_clauses = [f"{field} = '{value}'" for field, value in filters.items()]
                query += " WHERE " + " AND ".join(where_clauses)

            query += f" ORDER BY LastModifiedDate DESC LIMIT {limit}"

            logger.info(f"Executing Salesforce query: {query}")
            result = self.sf.query(query)

            opportunities = []
            for record in result['records']:
                opp = {
                    'id': record.get('Id'),
                    'opportunity_name': record.get('Name'),
                    'account_name': record.get('Account', {}).get('Name') if record.get('Account') else 'N/A',
                    'stage': record.get('StageName'),
                    'amount': record.get('Amount', 0),
                    'close_date': record.get('CloseDate'),
                    'probability': record.get('Probability', 0),
                    'owner_name': record.get('Owner', {}).get('Name') if record.get('Owner') else 'N/A',
                    'description': record.get('Description', ''),
                    'next_steps': record.get('NextStep', ''),
                    'created_date': record.get('CreatedDate'),
                    'last_modified_date': record.get('LastModifiedDate')
                }
                opportunities.append(opp)

            logger.info(f"Retrieved {len(opportunities)} opportunities from Salesforce")
            return opportunities

        except Exception as e:
            logger.error(f"Error fetching opportunities: {str(e)}")
            return []

    def get_cases(
        self,
        filters: Optional[Dict[str, str]] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch cases from Salesforce

        Args:
            filters: Dictionary of field filters (e.g., {'Status': 'New'})
            limit: Maximum number of records to fetch

        Returns:
            List of case dictionaries
        """
        try:
            # Build SOQL query
            query = """
                SELECT Id, CaseNumber, Subject, Status, Priority, Type, Origin,
                       AccountId, Account.Name, ContactId, Contact.Name,
                       OwnerId, Owner.Name, Description, Resolution,
                       CreatedDate, ClosedDate, LastModifiedDate
                FROM Case
            """

            # Add filters if provided
            if filters:
                where_clauses = [f"{field} = '{value}'" for field, value in filters.items()]
                query += " WHERE " + " AND ".join(where_clauses)

            query += f" ORDER BY LastModifiedDate DESC LIMIT {limit}"

            logger.info(f"Executing Salesforce query: {query}")
            result = self.sf.query(query)

            cases = []
            for record in result['records']:
                case = {
                    'id': record.get('Id'),
                    'case_number': record.get('CaseNumber'),
                    'subject': record.get('Subject'),
                    'status': record.get('Status'),
                    'priority': record.get('Priority', 'Medium'),
                    'type': record.get('Type', ''),
                    'origin': record.get('Origin', ''),
                    'account_name': record.get('Account', {}).get('Name') if record.get('Account') else 'N/A',
                    'contact_name': record.get('Contact', {}).get('Name') if record.get('Contact') else 'N/A',
                    'owner_name': record.get('Owner', {}).get('Name') if record.get('Owner') else 'N/A',
                    'description': record.get('Description', ''),
                    'resolution': record.get('Resolution', ''),
                    'created_date': record.get('CreatedDate'),
                    'closed_date': record.get('ClosedDate'),
                    'last_modified_date': record.get('LastModifiedDate')
                }
                cases.append(case)

            logger.info(f"Retrieved {len(cases)} cases from Salesforce")
            return cases

        except Exception as e:
            logger.error(f"Error fetching cases: {str(e)}")
            return []

    def get_opportunity_by_id(self, opportunity_id: str) -> Optional[Dict]:
        """
        Fetch a single opportunity by ID

        Args:
            opportunity_id: Salesforce opportunity ID

        Returns:
            Opportunity dictionary or None
        """
        opportunities = self.get_opportunities(filters={'Id': opportunity_id}, limit=1)
        return opportunities[0] if opportunities else None

    def get_case_by_number(self, case_number: str) -> Optional[Dict]:
        """
        Fetch a single case by case number

        Args:
            case_number: Salesforce case number

        Returns:
            Case dictionary or None
        """
        cases = self.get_cases(filters={'CaseNumber': case_number}, limit=1)
        return cases[0] if cases else None
