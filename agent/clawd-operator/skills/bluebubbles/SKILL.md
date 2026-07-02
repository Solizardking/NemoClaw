---
name: bluebubbles
description: Review or update the BlueBubbles extension manifest pointer and channel capability metadata.
---

# BlueBubbles manifest

Use this skill when working on the BlueBubbles channel capability metadata or planning a runtime adapter.

## Layout
- Registry entry: `extensions/registry.json` with `id` set to `bluebubbles`.
- Pointer file: `extensions/bluebubbles/clawd.extension.json`.
- The `extensions/bluebubbles/` directory is manifest-only. It must contain only `clawd.extension.json`.
- Do not add runtime source, tests, lockfiles, generated output, `node_modules`, `.env` files, provider key JSON files, or copied upstream SDK trees under `extensions/bluebubbles/`.

## Registry metadata
- Keep the registry entry focused on extension identity, capability boundaries, configuration namespace, and sensitive environment variables.
- Use `kind: "channel"` and include the `bluebubbles` channel name.
- Keep secret-bearing configuration names in the registry metadata. Do not commit local credential values.
- Runtime adapters should live in first-party NemoClaw packages or be fetched from trusted upstreams at install time, not vendored into `extensions/bluebubbles/`.

## Runtime planning notes
- BlueBubbles posts JSON to a gateway HTTP server.
- Normalize sender/chat IDs defensively (payloads vary by version).
- Skip messages marked as from self.
- Route inbound messages into the core reply pipeline through the owning runtime adapter.
- For attachments and stickers, preserve inbound media metadata and avoid logging credential-bearing URLs.

## Config metadata
- Registry namespace: `channels.bluebubbles`.
- Environment variables: `BLUEBUBBLES_SERVER_URL`, `BLUEBUBBLES_PASSWORD`.
- Secret environment variables: `BLUEBUBBLES_PASSWORD`.

## Message tool notes
- Reactions require a target, such as a phone number or chat identifier, in addition to a message ID.
