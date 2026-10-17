# DD-028: A hosted MCP server narrows the toolkit by capability

Status: Accepted

Date: 2026-10-17

Extends: [DD-008](dd-008-one-toolkit-thin-surfaces.md)

## Context

The aussiefy website (`aussiefy.au`) serves the MCP tools to agents over HTTP, from the pinned package. A
public server can't offer everything a local install does. Unlocking gated entries and the exact
`document_config` overrides are local choices. A text with no length limit is a cost the host carries. The
default translator reads the host's `$AUSSIEFY_HOME`. ChatGPT also treats an unannotated tool as a write
action that needs confirmation. A `public=True` switch would put the website's policy in the package. A
fork of the tools would break DD-008's single toolkit.

## Decision

`build_server()` takes capability options. The defaults serve everything, so local behaviour is unchanged:

- `allow_unlock=False` drops `unlock` and `include_gated` from the schemas and descriptions.
- `allow_document_config=False` drops `document_config`, makes `document_type` an enum without `custom`, and
  leaves the Custom and `document_config` guidance out of the instructions.
- `max_chars` caps every text field (`text` and `original`) in the schema, so an over-cap call is refused
  before any work.
- `max_query_chars` caps lookup's `query` separately. A meaning or a term is short, and a long query costs
  more than a translate of the same length while matching nothing past its first thousand characters.
- `lookup_limit` caps lookup's `limit`, and lowers its default when the cap is lower.
- `translator` is the one every tool uses. A host passes one built with `lookup_embedder="bundled"`.

A hidden parameter keeps its toolkit default. An argument sent for it anyway never reaches the toolkit: the
SDK drops it. A host that wants to tell the caller refuses it in its own middleware, which sees the raw
arguments. Every tool, on
every server, is annotated read-only, non-destructive, idempotent and closed-world.

## Consequences

- The package gives the SDK no auth. The host composes authentication and metering around the server: it
  mounts the SDK's auth routes and middleware once, and picks the server for the caller's tier on each
  request.
- The host decides its capabilities. The package knows nothing about tiers, accounts or the site, so one
  server is built per set of capabilities.
- Parity still holds: the default server mirrors the toolkit exactly, and a narrowed server mirrors it less
  the hidden parameters (`tests/functional/test_mcp_capabilities.py`).
- A tool description gives each parameter a server can hide its own line, so a narrowed server can drop the
  line. A test checks that no hidden name is left behind.
