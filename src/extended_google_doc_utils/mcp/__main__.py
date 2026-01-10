"""Entry point for running the MCP server.

Usage:
    python -m extended_google_doc_utils.mcp.server

Or:
    python -m extended_google_doc_utils.mcp
"""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # MCP uses stdout for protocol, stderr for logs
)


def main() -> None:
    """Run the Google Docs MCP server."""
    from extended_google_doc_utils.mcp.server import run_server

    try:
        run_server()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
