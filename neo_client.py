import logging
from neo_api_client import NeoAPI

class NeoClient:
    """Kotak Neo API Client wrapper"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def initialize_client_with_tokens(self, access_token, session_token, sid=None):
        """Initialize the Kotak Neo API client with existing tokens"""
        try:
            # Initialize client with tokens directly
            client = NeoAPI(
                consumer_key="dummy_key",  # Required but not used when access_token provided
                consumer_secret="dummy_secret",  # Required but not used when access_token provided
                environment='prod',
                access_token=access_token,
                neo_fin_key="neotradeapi"
            )
            
            # Set additional session data if available
            if session_token:
                client.session_token = session_token
            if sid:
                client.sid = sid
            
            self.logger.info("Neo API client initialized successfully with tokens!")
            return client
            
        except Exception as e:
            self.logger.error(f"Error initializing Neo API client with tokens: {str(e)}")
            return None
    
    def initialize_client(self, credentials):
        """Initialize the Kotak Neo API client"""
        try:
            # Check if tokens are provided in credentials
            if 'access_token' in credentials and credentials['access_token']:
                return self.initialize_client_with_tokens(
                    credentials['access_token'],
                    credentials.get('session_token'),
                    credentials.get('sid')
                )
            
            # Fallback to traditional initialization
            if not credentials.get('consumer_key') or not credentials.get('consumer_secret'):
                self.logger.error("Consumer key and secret are required for traditional initialization")
                return None
                
            client = NeoAPI(
                consumer_key=credentials['consumer_key'],
                consumer_secret=credentials['consumer_secret'],
                environment='prod',
                access_token=None,
                neo_fin_key=credentials.get('neo_fin_key', 'neotradeapi')
            )
            
            self.logger.info("Neo API client initialized successfully!")
            return client
            
        except Exception as e:
            self.logger.error(f"Error initializing Neo API client: {str(e)}")
            return None
    
    def login_with_totp(self, client, mobile_number, ucc, totp, mpin):
        """Login using TOTP (Time-based One-Time Password)"""
        try:
            self.logger.info("🔐 Attempting TOTP login...")
            
            # Step 1: TOTP Login
            totp_response = client.totp_login(
                mobile_number=mobile_number,
                ucc=ucc,
                totp=totp
            )
            self.logger.info("✅ TOTP login successful!")
            self.logger.debug(f"Login Response: {totp_response}")
            
            # Step 2: TOTP Validation
            validation_response = client.totp_validate(mpin=mpin)
            self.logger.info("✅ TOTP validation successful!")
            self.logger.debug(f"Validation Response: {validation_response}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ TOTP Login failed: {str(e)}")
            return False
