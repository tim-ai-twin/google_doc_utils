# Edit Google Doc

When the user wants to edit, update, fix, or modify content in a Google Doc, delegate to the `@edit-google-doc` agent. It runs in its own context window, which keeps large document content out of this conversation's context budget.

Example: if the user says "fix the typo in the introduction of document 1ABC...", invoke the `@edit-google-doc` agent with the user's request and document ID.

The agent handles: document discovery, structure analysis, targeted section reading/writing, multi-tab support, and cleanup.
