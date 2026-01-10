"""Google Docs to Markdown Converter.

Main converter class providing the public API for bidirectional conversion
between Google Docs and MEBDF (Markdown Extensions for Basic Doc Formatting).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from extended_google_doc_utils.converter.exceptions import (
    AnchorNotFoundError,
)
from extended_google_doc_utils.converter.hierarchy import get_hierarchy as _get_hierarchy
from extended_google_doc_utils.converter.tab_utils import (
    get_tab_content,
    resolve_tab_id,
)
from extended_google_doc_utils.converter.types import (
    ExportResult,
    HierarchyResult,
    ImportResult,
    TabReference,
)

if TYPE_CHECKING:
    from extended_google_doc_utils.auth.credential_manager import OAuthCredentials


class GoogleDocsConverter:
    """Converter for bidirectional Google Docs <-> MEBDF conversion.

    This is the main public API for the converter library. It provides
    methods for:
    - Getting document hierarchy (headings with anchor IDs)
    - Exporting tabs or sections to MEBDF markdown
    - Importing MEBDF markdown to tabs or sections

    Example:
        ```python
        from extended_google_doc_utils.converter import GoogleDocsConverter, TabReference

        converter = GoogleDocsConverter(credentials=creds)
        tab = TabReference(document_id="1ABC...")

        # Get hierarchy
        hierarchy = converter.get_hierarchy(tab)
        print(hierarchy.markdown)

        # Export full tab
        result = converter.export_tab(tab)
        print(result.content)
        ```
    """

    def __init__(self, credentials: OAuthCredentials):
        """Initialize the converter with OAuth credentials.

        Args:
            credentials: OAuth credentials from CredentialManager.
        """
        self._oauth_credentials = credentials

        # Convert OAuthCredentials to google.oauth2.credentials.Credentials
        self._google_credentials = Credentials(
            token=credentials.access_token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=credentials.scopes,
        )
        self._service = None

    @property
    def credentials(self) -> Credentials:
        """Return Google API credentials."""
        return self._google_credentials

    @property
    def service(self):
        """Lazy-load the Google Docs API service."""
        if self._service is None:
            self._service = build("docs", "v1", credentials=self._google_credentials)
        return self._service

    @property
    def drive_service(self):
        """Lazy-load the Google Drive API service."""
        if not hasattr(self, "_drive_service") or self._drive_service is None:
            self._drive_service = build("drive", "v3", credentials=self._google_credentials)
        return self._drive_service

    def _get_document(self, document_id: str) -> dict[str, Any]:
        """Fetch a document from the Google Docs API.

        Args:
            document_id: The document ID.

        Returns:
            The document resource from the API.
        """
        return self.service.documents().get(documentId=document_id).execute()

    # -------------------------------------------------------------------------
    # Discovery Operations
    # -------------------------------------------------------------------------

    def list_documents(
        self, max_results: int = 25, query: str | None = None
    ) -> list[dict[str, Any]]:
        """List Google Docs accessible by the user.

        Args:
            max_results: Maximum number of documents to return (default 25).
            query: Optional search query to filter documents.

        Returns:
            List of document summaries with id, title, last_modified, owner.
        """
        # Build query to filter for Google Docs only
        base_query = "mimeType='application/vnd.google-apps.document'"
        if query:
            base_query = f"{base_query} and name contains '{query}'"

        response = (
            self.drive_service.files()
            .list(
                q=base_query,
                pageSize=max_results,
                fields="files(id,name,modifiedTime,owners)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        documents = []
        for file in response.get("files", []):
            owners = file.get("owners", [{}])
            owner_email = owners[0].get("emailAddress", "") if owners else ""
            documents.append(
                {
                    "document_id": file.get("id", ""),
                    "title": file.get("name", ""),
                    "last_modified": file.get("modifiedTime", ""),
                    "owner": owner_email,
                }
            )
        return documents

    def get_metadata(self, document_id: str) -> dict[str, Any]:
        """Get metadata for a document including tabs.

        Args:
            document_id: Google Doc ID.

        Returns:
            Document metadata including title, tabs, permissions.
        """
        document = self._get_document(document_id)

        # Extract tabs from document
        tabs = []
        doc_tabs = document.get("tabs", [])

        # Single-tab documents may not have explicit tabs structure
        if not doc_tabs:
            tabs.append({"tab_id": "", "title": "Main", "index": 0})
        else:
            for i, tab in enumerate(doc_tabs):
                tab_props = tab.get("tabProperties", {})
                tabs.append(
                    {
                        "tab_id": tab_props.get("tabId", ""),
                        "title": tab_props.get("title", f"Tab {i + 1}"),
                        "index": tab_props.get("index", i),
                    }
                )

        return {
            "document_id": document_id,
            "title": document.get("title", ""),
            "tabs": tabs,
            # TODO: Add permission checking when needed
            "can_edit": True,
            "can_comment": True,
        }

    # -------------------------------------------------------------------------
    # Hierarchy Operations
    # -------------------------------------------------------------------------

    def get_hierarchy(self, tab: TabReference) -> HierarchyResult:
        """Get the heading hierarchy of a tab.

        Returns only headings as pure markdown with anchor IDs.
        Format: `## {^ anchor_id}Heading Text`

        Args:
            tab: Reference to the document tab.

        Returns:
            HierarchyResult with headings and markdown representation.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
        """
        document = self._get_document(tab.document_id)
        tab_id = resolve_tab_id(document, tab)
        body = get_tab_content(document, tab_id)

        return _get_hierarchy(body)

    # -------------------------------------------------------------------------
    # Export Operations (Google Docs -> MEBDF)
    # -------------------------------------------------------------------------

    def export_tab(self, tab: TabReference) -> ExportResult:
        """Export entire tab to MEBDF markdown.

        Args:
            tab: Reference to the document tab.

        Returns:
            ExportResult with MEBDF content and any warnings.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
        """
        # Import here to avoid circular imports
        from extended_google_doc_utils.converter.gdoc_to_mebdf import export_body

        document = self._get_document(tab.document_id)
        tab_id = resolve_tab_id(document, tab)
        body = get_tab_content(document, tab_id)

        return export_body(document, body, tab_id)

    def export_section(self, tab: TabReference, anchor_id: str) -> ExportResult:
        """Export a specific section to MEBDF markdown.

        The section includes content from the heading through all subsections
        until the next heading of equal or higher level.

        Args:
            tab: Reference to the document tab.
            anchor_id: Heading anchor ID from hierarchy. Empty string for preamble.

        Returns:
            ExportResult with MEBDF content and any warnings.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
            AnchorNotFoundError: If anchor_id doesn't exist in the document.
        """
        # Import here to avoid circular imports
        from extended_google_doc_utils.converter.gdoc_to_mebdf import export_section
        from extended_google_doc_utils.converter.section_utils import find_section

        document = self._get_document(tab.document_id)
        tab_id = resolve_tab_id(document, tab)
        body = get_tab_content(document, tab_id)

        # Find section boundaries
        section = find_section(body, anchor_id)
        if section is None:
            raise AnchorNotFoundError(anchor_id)

        return export_section(document, body, tab_id, section)

    # -------------------------------------------------------------------------
    # Import Operations (MEBDF -> Google Docs)
    # -------------------------------------------------------------------------

    def import_tab(self, tab: TabReference, content: str) -> ImportResult:
        """Import MEBDF markdown to replace entire tab content.

        Args:
            tab: Reference to the document tab.
            content: MEBDF markdown content.

        Returns:
            ImportResult indicating success and any warnings.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
            MebdfParseError: If content has invalid MEBDF syntax.
            EmbeddedObjectNotFoundError: If placeholder references missing object.
        """
        # Import here to avoid circular imports
        from extended_google_doc_utils.converter.mebdf_parser import MebdfParser
        from extended_google_doc_utils.converter.mebdf_to_gdoc import (
            build_import_requests,
        )

        document = self._get_document(tab.document_id)
        tab_id = resolve_tab_id(document, tab)
        body = get_tab_content(document, tab_id)

        # Parse MEBDF content
        parser = MebdfParser()
        ast = parser.parse(content)

        # Build API requests
        requests, preserved, warnings = build_import_requests(
            document, body, tab_id, ast, replace_all=True
        )

        # Execute batch update
        if requests:
            self.service.documents().batchUpdate(
                documentId=tab.document_id, body={"requests": requests}
            ).execute()

        return ImportResult(
            success=True, requests=requests, preserved_objects=preserved, warnings=warnings
        )

    def import_section(
        self, tab: TabReference, anchor_id: str, content: str
    ) -> ImportResult:
        """Import MEBDF markdown to replace a specific section.

        Only the target section is modified; content before and after
        remains unchanged.

        Args:
            tab: Reference to the document tab.
            anchor_id: Heading anchor ID for the section. Empty string for preamble.
            content: MEBDF markdown content for the section.

        Returns:
            ImportResult indicating success and any warnings.

        Raises:
            MultipleTabsError: If tab_id is empty and document has multiple tabs.
            AnchorNotFoundError: If anchor_id doesn't exist in the document.
            MebdfParseError: If content has invalid MEBDF syntax.
            EmbeddedObjectNotFoundError: If placeholder references missing object.
        """
        # Import here to avoid circular imports
        from extended_google_doc_utils.converter.mebdf_parser import MebdfParser
        from extended_google_doc_utils.converter.mebdf_to_gdoc import (
            build_section_import_requests,
        )
        from extended_google_doc_utils.converter.section_utils import find_section

        document = self._get_document(tab.document_id)
        tab_id = resolve_tab_id(document, tab)
        body = get_tab_content(document, tab_id)

        # Find section boundaries
        section = find_section(body, anchor_id)
        if section is None:
            raise AnchorNotFoundError(anchor_id)

        # Parse MEBDF content
        parser = MebdfParser()
        ast = parser.parse(content)

        # Build API requests for section replacement
        requests, preserved, warnings = build_section_import_requests(
            document, body, tab_id, section, ast
        )

        # Execute batch update
        if requests:
            self.service.documents().batchUpdate(
                documentId=tab.document_id, body={"requests": requests}
            ).execute()

        return ImportResult(
            success=True, requests=requests, preserved_objects=preserved, warnings=warnings
        )
