from mcp.server.fastmcp import FastMCP
import datetime
import random
from zoneinfo import ZoneInfo

# Initialize the MCP Server
mcp = FastMCP("My Demo Tools")

# --- TOOL 1: Get Time (Upgraded) ---
@mcp.tool()
def get_time(timezone: str = "Local") -> str:
    """
    Returns the current time.
    timezone: Can be 'Local' or a specific IANA timezone like 'America/New_York',
    'Europe/London', 'Asia/Tokyo', 'Asia/Kolkata', 'Australia/Sydney'.
    """
    try:
        if timezone.lower() == "local":
            # Get system local time
            now = datetime.datetime.now()
            location = "Local System Time"
        else:
            # Get specific timezone time
            now = datetime.datetime.now(ZoneInfo(timezone))
            location = timezone

        return f"Time in {location}: {now.strftime('%H:%M:%S')}"
    except Exception:
        return f"Error: '{timezone}' is not a valid timezone. Try formats like 'Asia/Tokyo' or 'America/New_York'."

# --- TOOL 2: Calculator ---
@mcp.tool()
def calculate_operation(operation: str, a: int, b: int) -> str:
    """
    Performs basic math.
    operation: 'add', 'subtract', 'multiply', 'divide'
    """
    if operation == "add": return str(a + b)
    elif operation == "subtract": return str(a - b)
    elif operation == "multiply": return str(a * b)
    elif operation == "divide": return str(a / b) if b != 0 else "Error: Div/0"
    else: return "Unknown operation"

# --- TOOL 3: System Status ---
@mcp.tool()
def check_system_status(system_name: str) -> str:
    """Checks status of a system (e.g. 'database', 'api')."""
    return f"System '{system_name}' is: {random.choice(['Online', 'Offline', 'Maintenance'])}"

if __name__ == "__main__":
    mcp.run()