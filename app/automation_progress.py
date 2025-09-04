"""
Progress tracking for VPN automation
"""
import threading
import time
import uuid
from typing import Dict, Callable, Optional
from datetime import datetime, timedelta

class AutomationProgressTracker:
    def __init__(self):
        self.progress_data = {}
        self.lock = threading.Lock()
        
    def create_job(self, job_id: str = None) -> str:
        """Create a new automation job and return its ID"""
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        with self.lock:
            self.progress_data[job_id] = {
                'job_id': job_id,
                'status': 'initialized',
                'step': 0,
                'total_steps': 18,
                'description': 'Initializing automation...',
                'success': True,
                'percentage': 0.0,
                'start_time': datetime.now(),
                'last_update': datetime.now(),
                'error_message': None,
                'completed': False,
                'result': None
            }
        
        return job_id
    
    def update_progress(self, job_id: str, progress_data: Dict):
        """Update progress for a specific job"""
        with self.lock:
            if job_id in self.progress_data:
                self.progress_data[job_id].update(progress_data)
                self.progress_data[job_id]['last_update'] = datetime.now()
                
                # Debug output
                print(f"DEBUG: Progress update for {job_id}: step={progress_data.get('step', 'N/A')}, success={progress_data.get('success', 'N/A')}, description={progress_data.get('description', 'N/A')}", flush=True)
                
                # Mark as completed if step equals total_steps
                if progress_data.get('step', 0) >= self.progress_data[job_id]['total_steps']:
                    self.progress_data[job_id]['completed'] = True
                    self.progress_data[job_id]['status'] = 'completed'
    
    def get_progress(self, job_id: str) -> Optional[Dict]:
        """Get current progress for a job"""
        with self.lock:
            return self.progress_data.get(job_id, None)
    
    def set_result(self, job_id: str, result: Dict):
        """Set the final result for a job"""
        with self.lock:
            if job_id in self.progress_data:
                print(f"DEBUG: Setting result for {job_id}: success={result.get('success', 'N/A')}, error={result.get('error_message', 'N/A')}", flush=True)
                
                self.progress_data[job_id]['result'] = result
                self.progress_data[job_id]['completed'] = True
                self.progress_data[job_id]['last_update'] = datetime.now()
                
                # Set success status and display fields based on result
                if result.get('success', False):
                    self.progress_data[job_id]['status'] = 'completed'
                    self.progress_data[job_id]['success'] = True
                    self.progress_data[job_id]['description'] = 'VPN automation completed successfully!'
                    self.progress_data[job_id]['percentage'] = 100.0
                    self.progress_data[job_id]['step'] = self.progress_data[job_id]['total_steps']
                    self.progress_data[job_id]['error_message'] = None
                    print(f"DEBUG: Job {job_id} marked as successful", flush=True)
                else:
                    self.progress_data[job_id]['status'] = 'failed'
                    self.progress_data[job_id]['success'] = False
                    error_msg = result.get('error_message', 'Unknown error')
                    self.progress_data[job_id]['description'] = f'Automation failed: {error_msg}'
                    self.progress_data[job_id]['error_message'] = error_msg
                    print(f"DEBUG: Job {job_id} marked as failed with error: {error_msg}", flush=True)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up jobs older than max_age_hours"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        with self.lock:
            jobs_to_remove = [
                job_id for job_id, data in self.progress_data.items()
                if data['last_update'] < cutoff_time
            ]
            for job_id in jobs_to_remove:
                del self.progress_data[job_id]

# Global progress tracker instance
progress_tracker = AutomationProgressTracker()

def run_automation_with_progress(automation_service, sender_email: str, vpn_username: str, vpn_password: str, job_id: str):
    """Run automation in background with progress tracking"""
    
    def progress_callback(progress_data):
        """Callback to update progress"""
        progress_tracker.update_progress(job_id, progress_data)
    
    try:
        # Set the progress callback
        automation_service.set_progress_callback(progress_callback)
        
        # Update status to running
        progress_tracker.update_progress(job_id, {
            'status': 'running',
            'description': 'Starting VPN automation...'
        })
        
        # Execute the automation
        result = automation_service.execute_vpn_creation_automation(
            sender_email, vpn_username, vpn_password
        )
        
        # Set the final result
        progress_tracker.set_result(job_id, result)
        
    except Exception as e:
        # Handle any unexpected errors
        error_result = {
            'success': False,
            'error_message': f"Unexpected error: {str(e)}",
            'steps_completed': automation_service.current_step,
            'total_steps': automation_service.total_steps
        }
        progress_tracker.set_result(job_id, error_result)
