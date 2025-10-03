#!/usr/bin/env python3
"""
Celery worker and beat scheduler startup script

This script starts the Celery worker and beat scheduler for the Galactic Empire game.
Run this script to start the background task processing system.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.core.config')
os.environ.setdefault('CELERY_CONFIG_MODULE', 'app.core.celery')

def start_celery_worker():
    """Start Celery worker process"""
    print("Starting Celery worker...")
    
    cmd = [
        sys.executable, '-m', 'celery',
        'worker',
        '--app=app.core.celery:celery_app',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=default,high_priority,medium_priority,low_priority',
        '--hostname=worker@%h'
    ]
    
    return subprocess.Popen(cmd, cwd=backend_dir)

def start_celery_beat():
    """Start Celery beat scheduler process"""
    print("Starting Celery beat scheduler...")
    
    cmd = [
        sys.executable, '-m', 'celery',
        'beat',
        '--app=app.core.celery:celery_app',
        '--loglevel=info',
        '--schedule=celerybeat-schedule'
    ]
    
    return subprocess.Popen(cmd, cwd=backend_dir)

def start_flower():
    """Start Flower monitoring interface (optional)"""
    print("Starting Flower monitoring interface...")
    
    cmd = [
        sys.executable, '-m', 'celery',
        'flower',
        '--app=app.core.celery:celery_app',
        '--port=5555',
        '--address=127.0.0.1'
    ]
    
    return subprocess.Popen(cmd, cwd=backend_dir)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}. Shutting down...")
    sys.exit(0)

def main():
    """Main function to start all Celery processes"""
    print("Galactic Empire - Celery Background Task System")
    print("=" * 50)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    processes = []
    
    try:
        # Start Celery worker
        worker_process = start_celery_worker()
        processes.append(('Worker', worker_process))
        
        # Wait a moment for worker to start
        time.sleep(2)
        
        # Start Celery beat scheduler
        beat_process = start_celery_beat()
        processes.append(('Beat Scheduler', beat_process))
        
        # Optionally start Flower (uncomment if needed)
        # flower_process = start_flower()
        # processes.append(('Flower', flower_process))
        
        print("\nAll processes started successfully!")
        print("Press Ctrl+C to stop all processes")
        
        # Monitor processes
        while True:
            time.sleep(1)
            
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"Warning: {name} process has stopped unexpectedly")
                    return_code = process.returncode
                    if return_code != 0:
                        print(f"{name} exited with code {return_code}")
    
    except KeyboardInterrupt:
        print("\nShutting down all processes...")
        
        # Terminate all processes
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Force killing {name}...")
                process.kill()
        
        print("All processes stopped.")

if __name__ == '__main__':
    main()
