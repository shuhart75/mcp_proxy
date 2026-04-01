# Confluence Orchestrator

This extension is the recommended stage-1 integration path for GigaCode.

It does not provide its own MCP transport. Instead it assumes an existing, working Atlassian MCP server is already connected to GigaCode and focuses on:

- fetching a large Confluence page once
- splitting it into bounded chunks
- delegating chunk edits to subagents
- merging chunk outputs locally with scripts
- reviewing the merged document with a controller subagent
- writing the final page back through the existing Atlassian MCP server

It also supports a multi-page consistency workflow:

- fetch each target page once
- prepare one local workspace per page
- optionally edit only the chunks that need changes
- review the full page set with a cross-page controller subagent
- stop after the report for review-only tasks
- write back only after cross-page approval for fix tasks

Preferred Atlassian MCP tools:

- `mcp__Atlassian__confluence_get_page`
- `mcp__Atlassian__confluence_update_page`
- `mcp__Atlassian__confluence_search`

If the Atlassian MCP exposes many more tools, prefer configuring `includeTools` to keep only the small Confluence subset needed for this workflow.
