#!/usr/bin/env python3
"""
GPU Temperature Watchdog
Monitors GPU temperature and gracefully shuts down T-Rex mining software
when temperature exceeds configured threshold.
"""

import time
import psutil
import subprocess
import logging
import json
import os
import signal
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration class for GPU watchdog"""
    temp_threshold: float = 85.0  # Temperature threshold in Celsius
    check_interval: int = 10  # Check interval in seconds
    grace_period: int = 30  # Grace period for graceful shutdown in seconds
    trex_process_names: List[str] = field(default_factory=lambda: ["t-rex.exe", "trex.exe", "t-rex", "trex"])
    log_level: str = "INFO"


class GPUWatchdog:
    """GPU temperature monitoring watchdog"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = self._setup_logging()
        self.running = True
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("GPUWatchdog")
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # File handler
        file_handler = logging.FileHandler("gpu_watchdog.log")
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
        
    def get_gpu_temperature(self) -> Optional[float]:
        """Get current GPU temperature using nvidia-smi"""
        try:
            # Check if nvidia-smi is available
            result = subprocess.run([
                "nvidia-smi",
                "--query-gpu=temperature.gpu",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Get the first GPU temperature (or max if multiple GPUs)
                temps: List[float] = []
                for temp_str in result.stdout.strip().split('\n'):
                    temp_str = temp_str.strip()
                    if temp_str and temp_str.replace('.', '').isdigit():
                        temps.append(float(temp_str))
                
                if temps:
                    max_temp = max(temps)
                    self.logger.debug(f"GPU temperatures: {temps}, Max: {max_temp}°C")
                    return max_temp
                else:
                    self.logger.error("No valid temperature readings found in nvidia-smi output")
                    return None
            else:
                self.logger.error(f"nvidia-smi error: {result.stderr}")
                return None
                
        except FileNotFoundError:
            self.logger.error("nvidia-smi not found. Please ensure NVIDIA drivers are installed and nvidia-smi is in PATH")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error("nvidia-smi command timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error getting GPU temperature: {e}")
            return None
    
    def find_trex_processes(self) -> List[psutil.Process]:
        """Find all T-Rex mining processes"""
        trex_processes: List[psutil.Process] = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    process_name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                    
                    # Check if process name matches T-Rex variants
                    if any(trex_name.lower() in process_name for trex_name in self.config.trex_process_names):
                        trex_processes.append(proc)
                        self.logger.debug(f"Found T-Rex process: {proc.info['name']} (PID: {proc.info['pid']})")
                    
                    # Also check command line for t-rex
                    elif 't-rex' in cmdline or 'trex' in cmdline:
                        trex_processes.append(proc)
                        self.logger.debug(f"Found T-Rex process by cmdline: {proc.info['name']} (PID: {proc.info['pid']})")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error finding T-Rex processes: {e}")
            
        return trex_processes
    
    def graceful_shutdown_trex(self, processes: List[psutil.Process]) -> bool:
        """Gracefully shutdown T-Rex processes"""
        if not processes:
            self.logger.info("No T-Rex processes found to shutdown")
            return True
            
        self.logger.warning(f"Initiating graceful shutdown of {len(processes)} T-Rex process(es)")
        
        # Send SIGTERM (or CTRL_C_EVENT on Windows) for graceful shutdown
        terminated_processes: List[psutil.Process] = []
        
        for proc in processes:
            try:
                self.logger.info(f"Sending graceful shutdown signal to T-Rex process {proc.pid}")
                
                if os.name == 'nt':  # Windows
                    # Try to send CTRL_C_EVENT first (graceful for T-Rex)
                    try:
                        # Send CTRL_C_EVENT to the process group
                        self.logger.info(f"Sending CTRL_C_EVENT to process {proc.pid}")
                        proc.send_signal(signal.CTRL_C_EVENT)
                        
                        # Give it a moment to start shutting down gracefully
                        time.sleep(2)
                        
                        # Check if process is still running
                        if proc.is_running():
                            self.logger.info(f"Process {proc.pid} still running after CTRL_C, will wait for grace period")
                        else:
                            self.logger.info(f"Process {proc.pid} gracefully shut down via CTRL_C")
                            continue
                            
                    except (OSError, psutil.AccessDenied) as e:
                        # CTRL_C_EVENT might not work, fallback to terminate
                        self.logger.warning(f"CTRL_C_EVENT failed for process {proc.pid}: {e}, using terminate()")
                        proc.terminate()
                else:  # Unix-like
                    # Send SIGINT first (equivalent to Ctrl+C)
                    try:
                        proc.send_signal(signal.SIGINT)
                        time.sleep(2)
                        if not proc.is_running():
                            self.logger.info(f"Process {proc.pid} gracefully shut down via SIGINT")
                            continue
                    except:
                        # Fallback to SIGTERM
                        proc.terminate()
                    
                terminated_processes.append(proc)
                
            except psutil.NoSuchProcess:
                self.logger.info(f"Process {proc.pid} already terminated")
            except Exception as e:
                self.logger.error(f"Error terminating process {proc.pid}: {e}")
        
        # Wait for graceful shutdown
        if terminated_processes:
            self.logger.info(f"Waiting {self.config.grace_period} seconds for {len(terminated_processes)} process(es) to shut down gracefully...")
            
            # Show countdown for user feedback
            for remaining in range(self.config.grace_period, 0, -5):
                alive_count = sum(1 for proc in terminated_processes if proc.is_running())
                if alive_count == 0:
                    self.logger.info("All T-Rex processes have shut down gracefully!")
                    break
                self.logger.info(f"Still waiting... {alive_count} process(es) running, {remaining} seconds remaining")
                time.sleep(5)
            
            _, alive = psutil.wait_procs(terminated_processes, timeout=0)  # Just check status now
        else:
            self.logger.info("No processes needed termination")
            alive = []
        
        # Force kill any remaining processes
        if alive:
            self.logger.warning(f"Force killing {len(alive)} remaining T-Rex process(es)")
            for proc in alive:
                try:
                    proc.kill()
                    self.logger.info(f"Force killed process {proc.pid}")
                except Exception as e:
                    self.logger.error(f"Error force killing process {proc.pid}: {e}")
        
        self.logger.info("T-Rex shutdown procedure completed")
        return True
    
    def run(self):
        """Main watchdog loop"""
        self.logger.info(f"GPU Watchdog started - Temperature threshold: {self.config.temp_threshold}°C")
        self.logger.info(f"Check interval: {self.config.check_interval} seconds")
        
        try:
            while self.running:
                # Get current GPU temperature
                current_temp = self.get_gpu_temperature()
                
                if current_temp is None:
                    self.logger.warning("Could not read GPU temperature, skipping check")
                    time.sleep(self.config.check_interval)
                    continue
                
                self.logger.debug(f"Current GPU temperature: {current_temp}°C")
                
                # Check if temperature exceeds threshold
                if current_temp >= self.config.temp_threshold:
                    self.logger.critical(
                        f"GPU temperature {current_temp}°C exceeds threshold {self.config.temp_threshold}°C!"
                    )
                    
                    # Find and shutdown T-Rex processes
                    trex_processes = self.find_trex_processes()
                    
                    if trex_processes:
                        self.graceful_shutdown_trex(trex_processes)
                        
                        # Wait a bit after shutdown before next check
                        self.logger.info("Waiting 60 seconds after T-Rex shutdown...")
                        time.sleep(60)
                    else:
                        self.logger.warning("No T-Rex processes found to shutdown")
                        time.sleep(self.config.check_interval)
                else:
                    # Temperature is within safe range
                    time.sleep(self.config.check_interval)
                    
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down watchdog...")
        except Exception as e:
            self.logger.error(f"Unexpected error in watchdog loop: {e}")
        finally:
            self.running = False
            self.logger.info("GPU Watchdog stopped")


def load_config(config_file: str = "gpu_watchdog_config.json") -> Config:
    """Load configuration from JSON file"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            return Config(**config_data)
        except Exception as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration")
    
    return Config()


def save_default_config(config_file: str = "gpu_watchdog_config.json"):
    """Save default configuration to JSON file"""
    default_config = {
        "temp_threshold": 85.0,
        "check_interval": 10,
        "grace_period": 30,
        "trex_process_names": ["t-rex.exe", "trex.exe", "t-rex", "trex"],
        "log_level": "INFO"
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"Default configuration saved to {config_file}")
    except Exception as e:
        print(f"Error saving config file: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPU Temperature Watchdog for T-Rex Mining")
    parser.add_argument("--config", "-c", default="gpu_watchdog_config.json",
                       help="Configuration file path")
    parser.add_argument("--create-config", action="store_true",
                       help="Create default configuration file and exit")
    parser.add_argument("--temp-threshold", "-t", type=float,
                       help="Temperature threshold in Celsius")
    parser.add_argument("--check-interval", "-i", type=int,
                       help="Check interval in seconds")
    parser.add_argument("--test-mode", action="store_true",
                       help="Test mode - shows what would happen without actually killing processes")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run - check current temperature and processes without monitoring")
    
    args = parser.parse_args()
    
    if args.create_config:
        save_default_config(args.config)
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.temp_threshold:
        config.temp_threshold = args.temp_threshold
    if args.check_interval:
        config.check_interval = args.check_interval
    
    # Create watchdog
    watchdog = GPUWatchdog(config)
    
    if args.dry_run:
        print("=== DRY RUN MODE ===")
        temp = watchdog.get_gpu_temperature()
        if temp:
            print(f"Current GPU Temperature: {temp}°C")
            print(f"Threshold: {config.temp_threshold}°C")
            if temp >= config.temp_threshold:
                print("⚠️  Temperature EXCEEDS threshold!")
                processes = watchdog.find_trex_processes()
                if processes:
                    print(f"Found {len(processes)} T-Rex process(es):")
                    for proc in processes:
                        try:
                            print(f"  - PID {proc.pid}: {proc.name()}")
                        except:
                            print(f"  - PID {proc.pid}: <process info unavailable>")
                else:
                    print("No T-Rex processes found")
            else:
                print("✅ Temperature is within safe range")
        else:
            print("❌ Could not read GPU temperature")
        return
    
    if args.test_mode:
        print("=== TEST MODE - No processes will actually be killed ===")
        # Modify config for testing
        original_method = watchdog.graceful_shutdown_trex
        def test_shutdown(processes):
            print(f"TEST: Would shutdown {len(processes)} processes with {config.grace_period}s grace period")
            for proc in processes:
                try:
                    print(f"TEST: Would send shutdown signal to PID {proc.pid}: {proc.name()}")
                except:
                    print(f"TEST: Would send shutdown signal to PID {proc.pid}")
            return True
        watchdog.graceful_shutdown_trex = test_shutdown
    
    # Run watchdog
    watchdog.run()


if __name__ == "__main__":
    main()