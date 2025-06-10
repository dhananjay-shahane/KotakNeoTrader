import logging
import os
from neo_api_client import NeoAPI

class NeoClient:
    """Kotak Neo API Client wrapper"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def initialize_neo_client(self, ucc):
        """Initialize the Kotak Neo API client - following Jupyter notebook implementation"""
        try:
            # Get credentials from environment or defaults
            consumer_key = os.environ.get('KOTAK_CONSUMER_KEY', '4OKP7bOfI5ozzCB1EI4a6DOIyJsa')
            consumer_secret = os.environ.get('KOTAK_CONSUMER_SECRET', 'cnLm3ZSJVLCOPiwTk4xAJw5G8v0a')
            neo_fin_key = os.environ.get('KOTAK_NEO_FIN_KEY', 'neotradeapi')
            
            # Get base URL - standard Kotak Neo production URL
            base_url = "https://gw-napi.kotaksecurities.com/"
            self.logger.info(f"Base URL retrieved: {base_url}")
            
            # Initialize client exactly like in notebook
            client = NeoAPI(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                environment='prod',
                access_token=None,
                neo_fin_key=neo_fin_key
            )
            
            self.logger.info("✅ Neo API client initialized successfully!")
            return client
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing Neo API client: {str(e)}")
            return None
    
    def initialize_client_with_tokens(self, access_token, session_token, sid=None):
        """Initialize the Kotak Neo API client with existing tokens"""
        try:
            # Use credentials from environment
            consumer_key = os.environ.get('KOTAK_CONSUMER_KEY', '4OKP7bOfI5ozzCB1EI4a6DOIyJsa')
            consumer_secret = os.environ.get('KOTAK_CONSUMER_SECRET', 'cnLm3ZSJVLCOPiwTk4xAJw5G8v0a')
            neo_fin_key = os.environ.get('KOTAK_NEO_FIN_KEY', 'neotradeapi')
            
            client = NeoAPI(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                environment='prod',
                access_token=access_token,
                neo_fin_key=neo_fin_key
            )
            
            # Set the session ID if provided
            if sid:
                client.session_token = sid
                self.logger.info(f"Session ID set: {sid[:10]}...")
            
            self.logger.info("Neo API client initialized with existing tokens")
            return client
            
        except Exception as e:
            self.logger.error(f"Error initializing Neo API client with tokens: {str(e)}")
            return None
    
    def validate_session(self, client):
        """Validate if the session is properly authenticated"""
        try:
            # Try to get account limits to validate session
            response = client.limits()
            if response and ('data' in response or 'Data' in response):
                self.logger.info("✅ Session validation successful")
                return True
            else:
                self.logger.warning("⚠️ Session validation failed - no data in response")
                return False
            
        except Exception as e:
            error_msg = str(e)
            if "Invalid Credentials" in error_msg or "Invalid JWT token" in error_msg:
                self.logger.error(f"❌ Session validation failed: {error_msg}")
                return False
            else:
                self.logger.warning(f"⚠️ Session validation warning: {error_msg}")
                return False
    
    def login_with_totp(self, client, mobile_number, ucc, totp, mpin):
        """Login using TOTP (Time-based One-Time Password) - following notebook implementation"""
        try:
            self.logger.info("🔐 Attempting TOTP login...")
            
            # Step 1: TOTP Login - following notebook method
            totp_response = client.login(
                mobilenumber=mobile_number,
                password=totp
            )
            self.logger.info("✅ TOTP login successful!")
            self.logger.info(f"Login Response: {totp_response}")
            
            # Step 2: TOTP Validation - following notebook method
            validation_response = client.session_2fa(OTP=mpin)
            self.logger.info("✅ TOTP validation successful!")
            self.logger.info(f"Validation Response: {validation_response}")
            
            return {
                'success': True,
                'login_response': totp_response,
                'validation_response': validation_response,
                'client': client
            }
            
        except Exception as e:
            self.logger.error(f"❌ TOTP Login failed: {str(e)}")
            return {'success': False, 'message': f'TOTP Login failed: {str(e)}'}

    def execute_totp_login(self, mobile_number, ucc, totp, mpin):
        """Execute complete TOTP login process - following notebook flow"""
        try:
            self.logger.info("🔐 Starting TOTP login process...")
            
            # Step 1: Initialize Neo API client
            client = self.initialize_neo_client(ucc)
            if not client:
                return {'success': False, 'message': 'Failed to initialize Neo API client'}
            
            # Step 2: Execute TOTP login
            login_result = self.login_with_totp(client, mobile_number, ucc, totp, mpin)
            
            if login_result['success']:
                self.logger.info("🎉 Login completed successfully!")
                
                # Extract session data from validation response
                validation_data = login_result['validation_response'].get('data', {})
                
                return {
                    'success': True,
                    'client': client,
                    'session_data': validation_data,
                    'access_token': validation_data.get('token'),
                    'session_token': validation_data.get('token'),
                    'sid': validation_data.get('sid'),
                    'ucc': validation_data.get('ucc'),
                    'greeting_name': validation_data.get('greetingName')
                }
            else:
                return login_result
                
        except Exception as e:
            self.logger.error(f"❌ TOTP Login process failed: {str(e)}")
            return {'success': False, 'message': f'TOTP Login failed: {str(e)}'}

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
            consumer_key = credentials.get('consumer_key', os.environ.get('KOTAK_CONSUMER_KEY', '4OKP7bOfI5ozzCB1EI4a6DOIyJsa'))
            consumer_secret = credentials.get('consumer_secret', os.environ.get('KOTAK_CONSUMER_SECRET', 'cnLm3ZSJVLCOPiwTk4xAJw5G8v0a'))
            neo_fin_key = credentials.get('neo_fin_key', os.environ.get('KOTAK_NEO_FIN_KEY', 'neotradeapi'))
            
            client = NeoAPI(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                environment='prod',
                access_token=None,
                neo_fin_key=neo_fin_key
            )
            
            self.logger.info("Neo API client initialized successfully!")
            return client
            
        except Exception as e:
            self.logger.error(f"Error initializing Neo API client: {str(e)}")
            return None