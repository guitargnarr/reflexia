"""
License Verification System for Reflexia Model Manager

THIS IS PROPRIETARY AND CONFIDENTIAL CODE
Copyright (c) 2025 Matthew D. Scott. All Rights Reserved.

This module provides license verification capabilities to ensure
authorized usage of the software.

For licensing inquiries: matthewdscott7@gmail.com
"""

import time
import os
import json
import hashlib
import uuid
from datetime import datetime, timedelta

class LicenseVerifier:
    """
    License verification system for Reflexia Model Manager
    
    This system verifies license keys and enforces usage restrictions
    based on the license terms.
    """
    
    LICENSE_TYPES = {
        "personal": {
            "description": "Personal Use License",
            "commercial_use": False,
            "max_instances": 1,
            "max_models": 3,
            "rag_enabled": True,
            "advanced_features": False
        },
        "professional": {
            "description": "Professional License",
            "commercial_use": True,
            "max_instances": 5,
            "max_models": 10,
            "rag_enabled": True,
            "advanced_features": True
        },
        "enterprise": {
            "description": "Enterprise License",
            "commercial_use": True,
            "max_instances": -1,  # Unlimited
            "max_models": -1,     # Unlimited
            "rag_enabled": True,
            "advanced_features": True
        },
        "educational": {
            "description": "Educational License",
            "commercial_use": False,
            "max_instances": 50,
            "max_models": 10,
            "rag_enabled": True,
            "advanced_features": True
        }
    }
    
    def __init__(self):
        """Initialize the license verifier"""
        self.license_data = None
        self.license_path = os.path.expanduser("~/.reflexia/license.json")
        self.instance_id = self._get_instance_id()
        self.load_license()
    
    def _get_instance_id(self):
        """Get or create a unique instance ID for this installation"""
        instance_id_path = os.path.expanduser("~/.reflexia/instance_id")
        os.makedirs(os.path.dirname(instance_id_path), exist_ok=True)
        
        if os.path.exists(instance_id_path):
            with open(instance_id_path, 'r') as f:
                return f.read().strip()
        else:
            instance_id = str(uuid.uuid4())
            with open(instance_id_path, 'w') as f:
                f.write(instance_id)
            return instance_id
    
    def load_license(self):
        """Load license data from file"""
        if os.path.exists(self.license_path):
            try:
                with open(self.license_path, 'r') as f:
                    self.license_data = json.load(f)
                return True
            except Exception:
                self.license_data = None
                return False
        return False
    
    def save_license(self, license_key, license_data):
        """Save license data to file"""
        os.makedirs(os.path.dirname(self.license_path), exist_ok=True)
        
        with open(self.license_path, 'w') as f:
            json.dump(license_data, f)
        
        self.license_data = license_data
        return True
    
    def activate_license(self, license_key, email):
        """
        Activate a license key
        
        Note: The actual activation process would typically
        involve a server-side validation component.
        
        Args:
            license_key (str): License key to activate
            email (str): Email associated with the license
            
        Returns:
            bool: Success status
        """
        # This is a placeholder
        # The real implementation would validate with a license server
        print("This is a placeholder. In the commercial version, this would validate your license.")
        return False
    
    def check_license(self):
        """
        Check if a valid license is installed
        
        Returns:
            dict: License status information
        """
        if not self.license_data:
            return {
                "valid": False,
                "message": "No license installed",
                "type": "none",
                "features": {
                    "commercial_use": False,
                    "max_instances": 1,
                    "rag_enabled": False,
                    "advanced_features": False
                }
            }
        
        # This is a placeholder
        # The real implementation would validate the license data
        return {
            "valid": False,
            "message": "License validation requires commercial version",
            "type": "none",
            "features": {
                "commercial_use": False,
                "max_instances": 1,
                "rag_enabled": False,
                "advanced_features": False
            }
        }
    
    def get_license_info(self):
        """
        Get information about the installed license
        
        Returns:
            dict: License information
        """
        status = self.check_license()
        
        if status["valid"]:
            return {
                "status": "active",
                "type": status["type"],
                "features": status["features"],
                "expiration": self.license_data.get("expiration", "N/A")
            }
        else:
            return {
                "status": "inactive",
                "message": status["message"],
                "type": "none",
                "features": {
                    "commercial_use": False,
                    "rag_enabled": False,
                    "advanced_features": False
                }
            }
    
    def generate_license_request(self):
        """
        Generate a license request
        
        This creates a request that can be sent to the licensing
        authority to request a license key.
        
        Returns:
            dict: License request information
        """
        import platform
        
        system_info = {
            "instance_id": self.instance_id,
            "hostname": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Create a signature based on system information
        signature_str = f"{system_info['instance_id']}:{system_info['hostname']}:{system_info['system']}:{system_info['machine']}"
        signature = hashlib.sha256(signature_str.encode()).hexdigest()
        
        return {
            "request_id": signature[:16],
            "system_info": system_info,
            "signature": signature,
            "timestamp": int(time.time())
        }