"""Entry point for running the MCP server.

Usage:
    python -m extended_google_doc_utils.mcp
    python -m extended_google_doc_utils.mcp --credentials /path/to/token.json
"""

import argparse
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
    parser = argparse.ArgumentParser(description="Google Docs MCP Server")
    parser.add_argument(
        "--credentials",
        type=str,
        help="Path to OAuth credentials JSON file (default: .credentials/token.json)",
    )
    args = parser.parse_args()

    from extended_google_doc_utils.mcp.server import run_server

    try:
        run_server(credentials_path=args.credentials)
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
