import logging
from neo_api_client import NeoAPI

class NeoClient:
    """Kotak Neo API Client wrapper"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def initialize_client(self, credentials):
        """Initialize the Kotak Neo API client"""
        try:
            # Initialize client with environment-based configuration
            environment = 'prod'  # Use 'prod' for live trading, 'uat' for testing
            
            # Initialize client
            client = NeoAPI(
                consumer_key=credentials['consumer_key'],
                consumer_secret=credentials['consumer_secret'],
                environment=environment,
                access_token=None,
                neo_fin_key=credentials['neo_fin_key']
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
