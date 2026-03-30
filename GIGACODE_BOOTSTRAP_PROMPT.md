# GigaCode Bootstrap Prompt

Use this prompt when you hand the project folder to GigaCode and want it to finish the local setup.

```text
You are working with the project in /home/reutov/confluence-section-mcp.

Goal:
Make this project usable as the only MCP server exposed to GigaCode for Confluence page editing, while the original mcp-atlassian server stays hidden behind it as an upstream backend.

Context:
- This project already implements a section-aware MCP proxy and a parallel section orchestrator.
- The proxy can run in `mcp` mode and spawn an upstream MCP server over stdio.
- The upstream server should be the existing Atlassian server:
  - command: /home/reutov/.gigacode/.venv/bin/python
  - args: /home/reutov/.gigacode/.venv/bin/mcp-atlassian
- The example config is in `examples/gigacode-mcp-config.json`.
- The main docs are in `README.md`.

What to do:
1. Inspect the project and confirm the intended startup command and env vars.
2. Verify whether the local GigaCode MCP config format requires absolute paths and whether `$HOME` expansion is safe. Prefer absolute paths if there is any doubt.
3. Adjust the example config if needed so that only this proxy is visible to GigaCode.
4. Verify the exact input and output shape of the upstream `getConfluencePage` and `updateConfluencePage` tools from `mcp-atlassian`.
5. If the upstream tool argument names or response format differ from the assumptions in this project, patch the adapter accordingly.
6. Add or update documentation with the final working setup steps.
7. If possible, run a safe local smoke test without touching production Confluence content.

Important constraints:
- Do not expose the original Atlassian MCP server directly to GigaCode.
- Keep the proxy as the single visible MCP server.
- Do not assume the upstream tool response shape; inspect it.
- Preserve the section-aware workflow:
  - read page once,
  - split into sections,
  - edit sections separately,
  - merge locally,
  - perform one final write via the proxy.

Files to inspect first:
- README.md
- examples/gigacode-mcp-config.json
- src/confluence_section_mcp/adapters.py
- src/confluence_section_mcp/server.py
- src/confluence_section_mcp/orchestrator.py

Expected outcome:
- A final MCP config that points GigaCode only to this proxy.
- Any code fixes needed for real `mcp-atlassian` compatibility.
- Updated docs describing the exact setup.
```
