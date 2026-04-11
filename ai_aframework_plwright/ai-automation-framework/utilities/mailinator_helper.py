"""
Mailinator Email Helper
Retrieves MFA codes and emails from Mailinator for testing
"""

import requests
import time
import re
from typing import Optional, Dict, Any, List
from utilities.logger import get_logger

logger = get_logger(__name__)


class MailinatorHelper:
    """Helper class for Mailinator email operations"""
    
    BASE_URL = "https://www.mailinator.com/api/v2"
    PUBLIC_INBOX_URL = "https://www.mailinator.com/v4/public/inboxes.jsp"
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Mailinator helper
        
        Args:
            api_token: Mailinator API token (optional, uses public API if not provided)
        """
        self.api_token = api_token
        self.session = requests.Session()
        
        if api_token:
            self.session.headers.update({
                "Authorization": f"Bearer {api_token}"
            })
    
    def get_inbox_messages(
        self,
        email: str,
        max_wait_seconds: int = 60,
        check_interval: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get messages from inbox, waiting if necessary
        
        Args:
            email: Email address (e.g., "test@mailinator.com")
            max_wait_seconds: Maximum time to wait for messages
            check_interval: Seconds between checks
            
        Returns:
            List of message objects
        """
        inbox_name = email.split('@')[0]
        logger.info(f"Checking inbox for: {inbox_name}")
        
        elapsed = 0
        while elapsed < max_wait_seconds:
            try:
                if self.api_token:
                    # Use API if token is available
                    url = f"{self.BASE_URL}/domains/private/inboxes/{inbox_name}"
                    response = self.session.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        messages = data.get('msgs', [])
                        
                        if messages:
                            logger.info(f"Found {len(messages)} message(s) in inbox")
                            return messages
                else:
                    # Use public API v3 endpoint
                    url = f"https://www.mailinator.com/api/v2/domains/public/inboxes/{inbox_name}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            messages = data.get('msgs', [])
                            
                            if messages:
                                logger.info(f"Found {len(messages)} message(s) in inbox")
                                return messages
                        except Exception:
                            # Fallback: Try to scrape from HTML if JSON fails
                            logger.debug("JSON parsing failed, trying HTML scraping")
                            pass
                
                logger.debug(f"No messages yet, waiting... ({elapsed}s/{max_wait_seconds}s)")
                time.sleep(check_interval)
                elapsed += check_interval
                
            except Exception as e:
                logger.debug(f"Error checking inbox: {e}")
                time.sleep(check_interval)
                elapsed += check_interval
        
        logger.warning(f"No messages found after {max_wait_seconds} seconds")
        return []
    
    def get_message_content(
        self,
        email: str,
        message_id: str
    ) -> Optional[str]:
        """
        Get message content by ID
        
        Args:
            email: Email address
            message_id: Message ID
            
        Returns:
            Message content (HTML or text)
        """
        inbox_name = email.split('@')[0]
        
        try:
            if self.api_token:
                # Use API
                url = f"{self.BASE_URL}/domains/private/inboxes/{inbox_name}/messages/{message_id}"
                response = self.session.get(url)
            else:
                # Use public API v2
                url = f"https://www.mailinator.com/api/v2/domains/public/messages/{message_id}"
                response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Try to get HTML content first, then plain text
                content = (
                    data.get('parts', [{}])[0].get('body') if data.get('parts') else None or
                    data.get('data', {}).get('parts', [{}])[0].get('body') if data.get('data', {}).get('parts') else None or
                    data.get('body') or
                    str(data)
                )
                
                return content
            
            logger.error(f"Failed to get message content: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting message content: {e}")
            return None
    
    def extract_mfa_code(
        self,
        email: str,
        max_wait_seconds: int = 60,
        code_pattern: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract MFA code from most recent email
        
        Args:
            email: Email address to check
            max_wait_seconds: Maximum time to wait for email
            code_pattern: Regex pattern to extract code (default: 6-digit number)
            
        Returns:
            MFA code if found, None otherwise
        """
        logger.info(f"Waiting for MFA code in: {email}")
        
        # Default pattern: 6-digit code
        if not code_pattern:
            code_pattern = r'\b(\d{6})\b'
        
        # Get messages
        messages = self.get_inbox_messages(email, max_wait_seconds)
        
        if not messages:
            logger.error("No messages found in inbox")
            return None
        
        # Check most recent message first
        for message in messages:
            message_id = message.get('id') or message.get('_id')
            subject = message.get('subject', '')
            
            logger.info(f"Checking message: {subject}")
            
            # Get message content
            content = self.get_message_content(email, message_id)
            
            if content:
                # Search for MFA code
                matches = re.findall(code_pattern, content)
                
                if matches:
                    mfa_code = matches[0]
                    logger.info(f"✅ MFA code found: {mfa_code}")
                    return mfa_code
        
        logger.error("MFA code not found in any messages")
        return None
    
    def extract_verification_link(
        self,
        email: str,
        max_wait_seconds: int = 60,
        link_pattern: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract verification link from email
        
        Args:
            email: Email address to check
            max_wait_seconds: Maximum time to wait for email
            link_pattern: Regex pattern to extract link
            
        Returns:
            Verification link if found, None otherwise
        """
        logger.info(f"Waiting for verification link in: {email}")
        
        # Default pattern: URL with verify/confirm/activate
        if not link_pattern:
            link_pattern = r'https?://[^\s<>"]+(?:verify|confirm|activate)[^\s<>"]*'
        
        # Get messages
        messages = self.get_inbox_messages(email, max_wait_seconds)
        
        if not messages:
            logger.error("No messages found in inbox")
            return None
        
        # Check most recent message first
        for message in messages:
            message_id = message.get('id') or message.get('_id')
            subject = message.get('subject', '')
            
            logger.info(f"Checking message: {subject}")
            
            # Get message content
            content = self.get_message_content(email, message_id)
            
            if content:
                # Search for verification link
                matches = re.findall(link_pattern, content, re.IGNORECASE)
                
                if matches:
                    link = matches[0]
                    logger.info(f"✅ Verification link found: {link[:50]}...")
                    return link
        
        logger.error("Verification link not found in any messages")
        return None
    
    def clear_inbox(self, email: str) -> bool:
        """
        Clear all messages from inbox (requires API token)
        
        Args:
            email: Email address
            
        Returns:
            True if successful, False otherwise
        """
        if not self.api_token:
            logger.warning("Clear inbox requires API token")
            return False
        
        inbox_name = email.split('@')[0]
        
        try:
            url = f"{self.BASE_URL}/domains/private/inboxes/{inbox_name}"
            response = self.session.delete(url)
            
            if response.status_code in [200, 204]:
                logger.info(f"Inbox cleared: {inbox_name}")
                return True
            
            logger.error(f"Failed to clear inbox: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Error clearing inbox: {e}")
            return False


# Convenience function for quick MFA retrieval
def get_mfa_code_from_email(
    email: str,
    max_wait_seconds: int = 60,
    api_token: Optional[str] = None
) -> Optional[str]:
    """
    Quick function to get MFA code from Mailinator email
    
    Args:
        email: Email address (e.g., "test@mailinator.com")
        max_wait_seconds: Maximum time to wait for email
        api_token: Mailinator API token (optional)
        
    Returns:
        MFA code if found, None otherwise
    """
    helper = MailinatorHelper(api_token)
    return helper.extract_mfa_code(email, max_wait_seconds)
