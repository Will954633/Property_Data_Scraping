#!/usr/bin/env python3
"""
Gold Coast Database Update Orchestrator
Last Updated: 31/01/2026, 8:08 am (Brisbane Time)

Production-grade orchestration system for managing 25 parallel workers.

Features:
- Spawns 25 workers with 30-second stagger
- Automatic resume from interruption
- Centralized logging and monitoring
- Worker health checks and auto-restart
- Error tracking across all workers
- Survives machine restarts
- Task scheduler compatible
"""

import os
import sys
import time
import json
import subprocess
import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from pymongo import MongoClient

# Configuration
NUM_WORKERS = 25
STAGGER_DELAY = 30  # seconds between worker starts
HEALTH_CHECK_INTERVAL = 60  # seconds
MAX_WORKER_IDLE_TIME = 300  # 5 minutes - restart if no updates
LOG_DIR = Path(__file__).parent / "orchestrator_logs"
WORKER_LOG_DIR = LOG_DIR / "workers"
CENTRAL_LOG = LOG_DIR / "central.log"
ERROR_LOG = LOG_DIR / "errors.log"
STATE_FILE = LOG_DIR / "orchestrator_state.json"

# Create log directories
LOG_DIR.mkdir(exist_ok=True)
WORKER_LOG_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CENTRAL_LOG),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Error logger
error_logger = logging.getLogger('errors')
error_handler = logging.FileHandler(ERROR_LOG)
error_handler.setFormatter(logging.Formatter('%(asctime)s - WORKER_%(worker_id)s - %(message)s'))
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)


class WorkerProcess:
    """Manages a single worker process"""
    
    def __init__(self, worker_id: int, total_workers: int):
        self.worker_id = worker_id
        self.total_workers = total_workers
        self.process: Optional[subprocess.Popen] = None
        self.log_file = WORKER_LOG_DIR / f"worker_{worker_id}.log"
        self.error_file = WORKER_LOG_DIR / f"worker_{worker_id}_errors.log"
        self.start_time: Optional[datetime] = None
        self.last_activity: Optional[datetime] = None
        self.properties_processed = 0
        self.errors = []
        
    def start(self):
        """Start the worker process"""
        try:
            env = os.environ.copy()
            env['WORKER_ID'] = str(self.worker_id)
            env['TOTAL_WORKERS'] = str(self.total_workers)
            env['MONGODB_URI'] = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
            
            # Open log files
            log_f = open(self.log_file, 'a')
            err_f = open(self.error_file, 'a')
            
            # Start worker process
            script_path = Path(__file__).parent / "update_gold_coast_database.py"
            self.process = subprocess.Popen(
                [sys.executable, str(script_path)],
                env=env,
                stdout=log_f,
                stderr=err_f,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
            
            self.start_time = datetime.now()
            self.last_activity = datetime.now()
            
            logger.info(f"Worker {self.worker_id} started (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start worker {self.worker_id}: {e}")
            error_logger.error(f"Failed to start: {e}", extra={'worker_id': self.worker_id})
            return False
    
    def is_running(self) -> bool:
        """Check if worker process is running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def stop(self):
        """Stop the worker process"""
        if self.process and self.is_running():
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                
                logger.info(f"Worker {self.worker_id} stopped")
            except Exception as e:
                logger.error(f"Error stopping worker {self.worker_id}: {e}")
    
    def check_health(self, mongo_client) -> bool:
        """Check worker health by looking at recent database updates"""
        try:
            db = mongo_client['Gold_Coast']
            
            # Check for recent updates from this worker
            recent_cutoff = datetime.now() - timedelta(seconds=MAX_WORKER_IDLE_TIME)
            
            # Check across all collections
            has_recent_activity = False
            for collection_name in db.list_collection_names():
                if collection_name == 'system.indexes':
                    continue
                
                collection = db[collection_name]
                recent_count = collection.count_documents({
                    'updated_at': {'$gte': recent_cutoff},
                    'scraped_data.worker_id': self.worker_id
                })
                
                if recent_count > 0:
                    has_recent_activity = True
                    self.last_activity = datetime.now()
                    break
            
            # Check if worker is idle too long
            if not has_recent_activity:
                idle_time = (datetime.now() - self.last_activity).total_seconds()
                if idle_time > MAX_WORKER_IDLE_TIME:
                    logger.warning(f"Worker {self.worker_id} idle for {idle_time:.0f}s")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed for worker {self.worker_id}: {e}")
            return False
    
    def get_stats(self, mongo_client) -> Dict:
        """Get worker statistics"""
        try:
            db = mongo_client['Gold_Coast']
            total_processed = 0
            
            for collection_name in db.list_collection_names():
                if collection_name == 'system.indexes':
                    continue
                
                collection = db[collection_name]
                count = collection.count_documents({
                    'scraped_data.worker_id': self.worker_id
                })
                total_processed += count
            
            self.properties_processed = total_processed
            
            return {
                'worker_id': self.worker_id,
                'running': self.is_running(),
                'properties_processed': total_processed,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'last_activity': self.last_activity.isoformat() if self.last_activity else None,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for worker {self.worker_id}: {e}")
            return {}


class Orchestrator:
    """Main orchestrator for managing all workers"""
    
    def __init__(self):
        self.workers: List[WorkerProcess] = []
        self.mongo_client: Optional[MongoClient] = None
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def connect_mongodb(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
            self.mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
            self.mongo_client.admin.command('ping')
            logger.info("Connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False
    
    def load_state(self) -> Dict:
        """Load orchestrator state from file"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        return {}
    
    def save_state(self):
        """Save orchestrator state to file"""
        try:
            state = {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'workers': [w.get_stats(self.mongo_client) for w in self.workers],
                'last_update': datetime.now().isoformat()
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_overall_progress(self) -> Dict:
        """Get overall progress across all workers"""
        try:
            db = self.mongo_client['Gold_Coast']
            
            total_with_scraped = 0
            total_updated = 0
            
            for collection_name in db.list_collection_names():
                if collection_name == 'system.indexes':
                    continue
                
                collection = db[collection_name]
                total_with_scraped += collection.count_documents({'scraped_data': {'$exists': True}})
                total_updated += collection.count_documents({'updated_at': {'$exists': True}})
            
            remaining = total_with_scraped - total_updated
            progress_pct = (total_updated / total_with_scraped * 100) if total_with_scraped > 0 else 0
            
            return {
                'total_properties': total_with_scraped,
                'updated': total_updated,
                'remaining': remaining,
                'progress_percent': progress_pct
            }
            
        except Exception as e:
            logger.error(f"Failed to get overall progress: {e}")
            return {}
    
    def start_workers(self):
        """Start all workers with staggered delays"""
        logger.info(f"Starting {NUM_WORKERS} workers with {STAGGER_DELAY}s stagger...")
        
        for i in range(NUM_WORKERS):
            worker = WorkerProcess(i, NUM_WORKERS)
            self.workers.append(worker)
            
            if worker.start():
                logger.info(f"Worker {i} started, waiting {STAGGER_DELAY}s before next...")
                time.sleep(STAGGER_DELAY)
            else:
                logger.error(f"Failed to start worker {i}")
        
        logger.info(f"All {NUM_WORKERS} workers started")
    
    def monitor_workers(self):
        """Monitor and restart failed workers"""
        while self.running:
            try:
                # Check each worker
                for worker in self.workers:
                    if not worker.is_running():
                        logger.warning(f"Worker {worker.worker_id} not running, restarting...")
                        worker.start()
                    elif not worker.check_health(self.mongo_client):
                        logger.warning(f"Worker {worker.worker_id} unhealthy, restarting...")
                        worker.stop()
                        time.sleep(5)
                        worker.start()
                
                # Log progress
                progress = self.get_overall_progress()
                if progress:
                    logger.info(
                        f"Progress: {progress['updated']:,}/{progress['total_properties']:,} "
                        f"({progress['progress_percent']:.2f}%) - "
                        f"{progress['remaining']:,} remaining"
                    )
                
                # Save state
                self.save_state()
                
                # Wait before next check
                time.sleep(HEALTH_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(HEALTH_CHECK_INTERVAL)
    
    def shutdown(self):
        """Shutdown all workers gracefully"""
        logger.info("Shutting down orchestrator...")
        self.running = False
        
        for worker in self.workers:
            worker.stop()
        
        if self.mongo_client:
            self.mongo_client.close()
        
        self.save_state()
        logger.info("Orchestrator shutdown complete")
    
    def run(self):
        """Main orchestrator run loop"""
        logger.info("="*70)
        logger.info("GOLD COAST DATABASE UPDATE ORCHESTRATOR STARTING")
        logger.info("="*70)
        
        self.start_time = datetime.now()
        self.running = True
        
        # Connect to MongoDB
        if not self.connect_mongodb():
            logger.error("Failed to connect to MongoDB, exiting")
            return
        
        # Check if resuming
        state = self.load_state()
        if state:
            logger.info("Resuming from previous state...")
        
        # Get initial progress
        progress = self.get_overall_progress()
        logger.info(f"Initial state: {progress['updated']:,}/{progress['total_properties']:,} updated")
        
        # Start workers
        self.start_workers()
        
        # Monitor workers
        try:
            self.monitor_workers()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.shutdown()


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
