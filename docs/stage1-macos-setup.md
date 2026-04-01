# Stage 1 Setup on macOS

This is the recommended installation path on the target machine.

Stage 1 does not add a custom MCP server. It uses:

- the existing working Atlassian MCP server
- a native GigaCode extension from this repository
- local chunk/merge helper scripts
- GigaCode subagents for chunk editing and controller review

## 0. What you need first

- A working `mcp-atlassian` installation that already connects in GigaCode
- Git
- Python
- This repository cloned locally

## 1. Clone or update the repository

If the repository is not on the machine yet:

```bash
cd ~
git clone https://github.com/shuhart75/mcp_proxy.git
cd mcp_proxy
```

If it is already there:

```bash
cd ~/mcp_proxy
git pull
```

## 2. Install the stage-1 extension assets

Run:

```bash
cd ~/mcp_proxy
bash tools/setup_stage1_extension.sh
```

This does two things:

- creates `~/.gigacode/extensions/confluence-orchestrator` as a symlink to this repository
- copies reference setup files into `~/.gigacode/confluence-orchestrator/`

## 3. Configure Atlassian MCP with a minimal Confluence tool set

Open:

```bash
~/.gigacode/settings.json
```

Use the sample from:

```bash
~/.gigacode/confluence-orchestrator/stage1-atlassian-settings.sample.json
```

Important:

- keep only the `Atlassian` MCP server for this workflow
- use `includeTools` to reduce prompt bloat
- keep only:
  - `confluence_get_page`
  - `confluence_update_page`
  - `confluence_search`

If you still need Jira in other sessions, add it back later. For initial validation, keep the tool list minimal.

## 4. Restart GigaCode fully

Quit GigaCode completely and start it again.

## 5. Validate that the extension is visible

You should no longer be relying on a custom MCP server for this workflow. The repository contains:

- `gigacode-extension.json`
- `GIGACODE.md`
- `skills/`
- `agents/`
- `commands/`

The extension should be discoverable from:

```bash
~/.gigacode/extensions/confluence-orchestrator
```

## 6. First-use prompt in GigaCode

Start with:

```text
skill: using-confluence-orchestrator

Task: update Confluence page <PAGE_ID>.
Goal: <describe the desired change>.
```

Or use the manual command:

```text
/large-confluence-edit
```

## 7. Expected workflow inside GigaCode

1. GigaCode uses the existing Atlassian MCP to fetch the page.
2. It saves the page markdown locally.
3. It runs:

```bash
python3 scripts/chunk_confluence_markdown.py \
  --input work/confluence/<PAGE_ID>/page.md \
  --output-dir work/confluence/<PAGE_ID>/chunks \
  --max-chars 12000
```

4. It dispatches chunk subagents.
5. It merges results with:

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/confluence/<PAGE_ID>/chunks/manifest.json \
  --output work/confluence/<PAGE_ID>/merged.md
```

6. It dispatches a controller subagent.
7. If approved, it writes the merged page back through `mcp__Atlassian__confluence_update_page`.

## 8. Minimal validation

Before touching a real Confluence page, test the local scripts:

```bash
cd ~/mcp_proxy
python3 -m unittest discover -s tests -v
python3 scripts/chunk_confluence_markdown.py \
  --input tests/fixtures/local-pages/demo-page.md \
  --output-dir /tmp/confluence-stage1-check \
  --max-chars 80
python3 scripts/merge_confluence_chunks.py \
  --manifest /tmp/confluence-stage1-check/manifest.json \
  --output /tmp/confluence-stage1-check/merged.md
```

## 9. If GigaCode still does not use the extension

Check:

```bash
ls -la ~/.gigacode/extensions/confluence-orchestrator
cat ~/.gigacode/extensions/confluence-orchestrator/gigacode-extension.json
```

Also verify that `~/.gigacode/settings.json` does not contain stale extension-related keys from older workflows.
