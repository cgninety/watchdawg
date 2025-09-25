# WatchDAWG - GPU Temperature Watchdog for T-Rex Mining

A Python program that monitors GPU temperature and gracefully shuts down T-Rex mining software when the temperature exceeds a configurable threshold.

## 🚀 Quick Start

```bash
git clone https://github.com/cgninety/watchdawg.git
cd watchdawg
setup.bat          # Windows users
./run_watchdog.bat # Start monitoring
```

## Features

- **Temperature Monitoring**: Uses `nvidia-smi` to monitor GPU temperature
- **Graceful Shutdown**: Sends proper termination signals to T-Rex processes for clean shutdown
- **Configurable**: JSON-based configuration for easy customization
- **Logging**: Comprehensive logging to both console and file
- **Process Detection**: Automatically detects T-Rex mining processes by name and command line
- **Cross-Platform**: Works on Windows and Linux

## Requirements

- NVIDIA GPU with NVIDIA drivers installed
- Python 3.7 or higher
- `nvidia-smi` utility (comes with NVIDIA drivers)
- Git (for cloning the repository)

## Installation

### Method 1: Clone from GitHub (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/cgninety/watchdawg.git
cd watchdawg
```

2. **Run the setup script (Windows):**
```cmd
setup.bat
```
This will automatically create a virtual environment, install dependencies, and create the default configuration.

3. **Or manually install (Windows/Linux):**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create default configuration
python gpu_watchdog.py --create-config
```

### Method 2: Download Individual Files

If you prefer not to use Git:

1. Download the following files from https://github.com/cgninety/watchdawg:
   - `gpu_watchdog.py`
   - `requirements.txt` 
   - `gpu_watchdog_config.json` (optional, will be created automatically)

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Create default configuration file:
```bash
python gpu_watchdog.py --create-config
```

## Configuration

The program uses a JSON configuration file (`gpu_watchdog_config.json`) with the following options:

- `temp_threshold`: Temperature threshold in Celsius (default: 85.0)
- `check_interval`: How often to check temperature in seconds (default: 10)
- `grace_period`: Time to wait for graceful shutdown before force killing (default: 30)
- `trex_process_names`: List of T-Rex process names to look for
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Example Configuration

```json
{
    "temp_threshold": 85.0,
    "check_interval": 10,
    "grace_period": 30,
    "trex_process_names": ["t-rex.exe", "trex.exe", "t-rex", "trex"],
    "log_level": "INFO"
}
```

## Usage

### Quick Start (Windows)

After installation, simply run:
```cmd
run_watchdog.bat
```

### Basic Usage

Run the watchdog with default settings:
```bash
python gpu_watchdog.py
```

### Command Line Options

```bash
# Use custom configuration file
python gpu_watchdog.py --config my_config.json

# Override temperature threshold
python gpu_watchdog.py --temp-threshold 80

# Override check interval
python gpu_watchdog.py --check-interval 15

# Create default configuration file
python gpu_watchdog.py --create-config
```

### Running as a Service (Windows)

You can run this as a Windows service using tools like NSSM:

1. Download NSSM from https://nssm.cc/
2. Install the service:
```cmd
nssm install GPUWatchdog "C:\path\to\python.exe" "C:\path\to\gpu_watchdog.py"
```

## How It Works

1. **Temperature Monitoring**: The program continuously monitors GPU temperature using `nvidia-smi`
2. **Process Detection**: When temperature exceeds threshold, it searches for T-Rex mining processes
3. **Graceful Shutdown**: 
   - Sends `CTRL_C_EVENT` on Windows or `SIGTERM` on Linux
   - Waits for the configured grace period for processes to shut down cleanly
   - Force kills any remaining processes if they don't respond
4. **Logging**: All actions are logged to both console and `gpu_watchdog.log` file

## Process Detection

The watchdog detects T-Rex processes by:
- Process name matching (t-rex.exe, trex.exe, etc.)
- Command line argument scanning for "t-rex" or "trex"

## Safety Features

- **Graceful Shutdown**: Gives T-Rex time to save state and close cleanly
- **Error Handling**: Continues monitoring even if individual checks fail
- **Logging**: Comprehensive logging for troubleshooting
- **Configuration Validation**: Validates settings on startup

## Troubleshooting

### Common Issues

1. **"nvidia-smi not found"**: Ensure NVIDIA drivers are installed and nvidia-smi is in PATH
2. **Permission errors**: Run as administrator on Windows or with appropriate permissions on Linux
3. **Process not detected**: Check the `trex_process_names` configuration to ensure it matches your T-Rex executable name

### Logs

Check the `gpu_watchdog.log` file for detailed information about:
- Temperature readings
- Process detection
- Shutdown attempts
- Errors and warnings

## License

This project is open source and available under the MIT License.