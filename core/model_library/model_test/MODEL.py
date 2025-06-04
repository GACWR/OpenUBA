import pandas as pd
import numpy as np
from datetime import datetime
import logging

loaded_data = None

def set_data(data):
    global loaded_data
    loaded_data = data

def calculate_user_risk(user_data):
    risk_score = 0
    risk_factors = []
    
    try:
        # 1. Denied Access Attempts (30% of score)
        denied_requests = user_data[user_data['sc-filter-result'] == 'DENIED']
        denied_count = len(denied_requests)
        if denied_count > 0:
            denied_score = min(30, denied_count * 5)  # Cap at 30
            risk_score += denied_score
            risk_factors.append(f"Denied access attempts: {denied_count} requests")
        
        # 2. Time-based Analysis (20% of score)
        try:
            # Convert time to datetime
            user_data['datetime'] = pd.to_datetime(user_data['date'] + ' ' + user_data['time'])
            user_data['hour'] = user_data['datetime'].dt.hour
            
            # Off-hours activity (outside 8am-6pm)
            off_hours = user_data[~user_data['hour'].between(8, 18)]
            off_hours_count = len(off_hours)
            if off_hours_count > 0:
                off_hours_score = min(20, off_hours_count)
                risk_score += off_hours_score
                risk_factors.append(f"Off-hours activity: {off_hours_count} requests")
                
            # Rapid succession requests (potential automation/scanning)
            if len(user_data) >= 2:
                user_data = user_data.sort_values('datetime')
                time_diffs = user_data['datetime'].diff()
                rapid_requests = time_diffs[time_diffs.dt.total_seconds() < 1].count()
                if rapid_requests > 5:
                    risk_score += min(15, rapid_requests)
                    risk_factors.append(f"Rapid succession requests: {rapid_requests} instances")
        except Exception as e:
            logging.warning(f"Time analysis error: {str(e)}")
        
        # 3. HTTP Status Code Analysis (25% of score)
        error_codes = user_data[user_data['sc-status'].astype(str).str.startswith(('4', '5'))]
        error_count = len(error_codes)
        if error_count > 0:
            error_score = min(25, error_count * 5)
            risk_score += error_score
            risk_factors.append(f"HTTP errors: {error_count} requests")
        
        # 4. Resource Access Patterns (25% of score)
        sensitive_patterns = ['/admin', '/config', '/login', '/user', '/password', '/auth', 
                            'ssh', 'telnet', 'ftp', '.git', '.env', '.config']
        sensitive_access = user_data[user_data['cs-uri-path'].str.contains('|'.join(sensitive_patterns), 
                                                                         case=False, na=False)]
        sensitive_count = len(sensitive_access)
        if sensitive_count > 0:
            sensitive_score = min(25, sensitive_count * 5)
            risk_score += sensitive_score
            risk_factors.append(f"Sensitive resource access: {sensitive_count} requests")
            
        # Cap total risk score at 100
        risk_score = min(100, risk_score)
        
    except Exception as e:
        logging.error(f"Error calculating risk: {str(e)}")
        risk_score = 0
        risk_factors.append(f"Error calculating risk: {str(e)}")
    
    return risk_score, risk_factors

def execute():
    print("model_test testing...")
    return_object = {}
    
    try:
        # Get the dataframe from the model context
        df = loaded_data.data  # This is our proxy log dataframe
        
        # Group by username and calculate risk for each user
        unique_users = df['cs-username'].unique()
        
        for user in unique_users:
            if pd.isna(user) or user in ['', 'NA', 'NONE', '-', 'cs-username']:
                continue
                
            user_data = df[df['cs-username'] == user]
            risk_score, risk_factors = calculate_user_risk(user_data)
            
            return_object[user] = {
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "last_seen": str(user_data['time'].iloc[-1]) if len(user_data) > 0 else "unknown",
                "total_requests": len(user_data)
            }
    
    except Exception as e:
        print(f"Error in model execution: {str(e)}")
        return_object["error"] = str(e)
    
    print("model end run...")
    return return_object 