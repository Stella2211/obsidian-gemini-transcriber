#!/bin/bash

# Obsidian Gemini Transcriber Service Setup Script

set -e

SERVICE_NAME="obsidian-transcriber"
SERVICE_TEMPLATE="${SERVICE_NAME}.service.template"
SERVICE_FILE="${SERVICE_NAME}.service"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~${CURRENT_USER})

# Find Python executable
if command -v python3 &> /dev/null; then
    PYTHON_PATH=$(command -v python3)
elif command -v python &> /dev/null; then
    PYTHON_PATH=$(command -v python)
else
    echo "Error: Python not found in PATH"
    exit 1
fi

echo "=== Obsidian Gemini Transcriber Service Setup ==="
echo "Current user: $CURRENT_USER"
echo "Working directory: $CURRENT_DIR"
echo "Python path: $PYTHON_PATH"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as your normal user with sudo when needed."
   exit 1
fi

# Function to generate service file from template
generate_service_file() {
    echo "Generating service file from template..."

    if [[ ! -f "${CURRENT_DIR}/${SERVICE_TEMPLATE}" ]]; then
        echo "Error: Template file ${SERVICE_TEMPLATE} not found!"
        echo "Creating template file..."

        cat > "${CURRENT_DIR}/${SERVICE_TEMPLATE}" << 'EOF'
[Unit]
Description=Obsidian Gemini Transcriber Service
After=network.target

[Service]
Type=simple
User={{USER}}
WorkingDirectory={{WORKING_DIR}}
Environment="PATH={{USER_HOME}}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH={{WORKING_DIR}}"
ExecStart={{PYTHON_PATH}} {{WORKING_DIR}}/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    fi

    # Generate service file from template
    sed -e "s|{{USER}}|${CURRENT_USER}|g" \
        -e "s|{{WORKING_DIR}}|${CURRENT_DIR}|g" \
        -e "s|{{USER_HOME}}|${USER_HOME}|g" \
        -e "s|{{PYTHON_PATH}}|${PYTHON_PATH}|g" \
        "${CURRENT_DIR}/${SERVICE_TEMPLATE}" > "${CURRENT_DIR}/${SERVICE_FILE}"

    echo "Service file generated: ${SERVICE_FILE}"
}

# Function to install the service
install_service() {
    echo "Installing service..."

    # Generate service file from template
    generate_service_file

    # Copy service file to systemd directory
    sudo cp "${CURRENT_DIR}/${SERVICE_FILE}" "/etc/systemd/system/${SERVICE_FILE}"

    # Reload systemd
    sudo systemctl daemon-reload

    # Enable service
    sudo systemctl enable "${SERVICE_NAME}.service"

    echo "Service installed and enabled."
    echo "The service will start automatically on boot."
    echo ""
    echo "Configuration:"
    echo "  Working Directory: ${CURRENT_DIR}"
    echo "  Python Path: ${PYTHON_PATH}"
    echo "  User: ${CURRENT_USER}"
}

# Function to start the service
start_service() {
    echo "Starting service..."
    sudo systemctl start "${SERVICE_NAME}.service"
    echo "Service started."
}

# Function to stop the service
stop_service() {
    echo "Stopping service..."
    sudo systemctl stop "${SERVICE_NAME}.service"
    echo "Service stopped."
}

# Function to check service status
check_status() {
    echo "Service status:"
    sudo systemctl status "${SERVICE_NAME}.service" --no-pager
}

# Function to view logs
view_logs() {
    echo "Recent logs (last 50 lines):"
    sudo journalctl -u "${SERVICE_NAME}.service" -n 50 --no-pager
}

# Function to follow logs in real-time
follow_logs() {
    echo "Following logs (Ctrl+C to exit):"
    sudo journalctl -u "${SERVICE_NAME}.service" -f
}

# Function to uninstall the service
uninstall_service() {
    echo "Uninstalling service..."

    # Stop and disable service
    sudo systemctl stop "${SERVICE_NAME}.service" 2>/dev/null || true
    sudo systemctl disable "${SERVICE_NAME}.service" 2>/dev/null || true

    # Remove service file
    sudo rm -f "/etc/systemd/system/${SERVICE_FILE}"

    # Reload systemd
    sudo systemctl daemon-reload

    # Remove generated service file
    rm -f "${CURRENT_DIR}/${SERVICE_FILE}"

    echo "Service uninstalled."
}

# Function to update the service
update_service() {
    echo "Updating service configuration..."

    # Generate new service file
    generate_service_file

    # Copy updated service file
    sudo cp "${CURRENT_DIR}/${SERVICE_FILE}" "/etc/systemd/system/${SERVICE_FILE}"

    # Reload systemd
    sudo systemctl daemon-reload

    # Restart service if it's running
    if sudo systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        echo "Restarting service with new configuration..."
        sudo systemctl restart "${SERVICE_NAME}.service"
    fi

    echo "Service configuration updated."
}

# Main menu
case "${1:-}" in
    install)
        install_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        start_service
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    follow)
        follow_logs
        ;;
    update)
        update_service
        ;;
    uninstall)
        uninstall_service
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|follow|update|uninstall}"
        echo ""
        echo "Commands:"
        echo "  install   - Install and enable the service"
        echo "  start     - Start the service"
        echo "  stop      - Stop the service"
        echo "  restart   - Restart the service"
        echo "  status    - Check service status"
        echo "  logs      - View recent logs"
        echo "  follow    - Follow logs in real-time"
        echo "  update    - Update service configuration"
        echo "  uninstall - Remove the service"
        echo ""
        echo "Quick setup:"
        echo "  1. Run: ./setup_service.sh install"
        echo "  2. Run: ./setup_service.sh start"
        echo "  3. Check: ./setup_service.sh status"
        echo ""
        echo "Current environment:"
        echo "  Working Directory: ${CURRENT_DIR}"
        echo "  Python Path: ${PYTHON_PATH}"
        echo "  User: ${CURRENT_USER}"
        exit 1
        ;;
esac