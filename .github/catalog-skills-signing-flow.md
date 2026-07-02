<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Publishing a Nemo Clawd skill to the NVIDIA Verified Skills catalog

The `skills/` directory at the repo root is the NVSkills CI watched location.
Whatever lives there is what gets signed and published. There is no
allowlist, manifest, or generator script.
Nemo Clawd hard-copies customer-facing source skills into `skills/` so NVSkills
CI can read the catalog path directly.

Nemo Clawd currently maintains one customer-facing skill,
`nemoclawd-user-guide`. That skill routes coding assistants to local docs,
canonical Markdown docs, Solana onboarding, the bundled MCP server, and
agent-auth guidance. Do not publish copied documentation pages as generated
`nemoclawd-user-*` skills.

## Add a skill to the catalog

```bash
mkdir -p skills
rm -rf skills/nemoclawd-user-guide
cp -R .agents/skills/nemoclawd-user-guide skills/
git add skills/nemoclawd-user-guide
git commit -m "chore(skills): publish nemoclawd-user-guide"
```

Open the PR, comment `/nvskills-ci`, wait for the signing job to push back
`skill.oms.sig` and `skill-card.md`, then merge.
NVSkills CI signs one skill at a time.

## Update an already-published skill

```bash
rm -rf skills/nemoclawd-user-guide
cp -R .agents/skills/nemoclawd-user-guide skills/
git add -A skills/nemoclawd-user-guide
git commit -m "chore(skills): refresh nemoclawd-user-guide"
```

Use `git add -A` so newly added files in the refreshed skill are staged
alongside removals tracked by `git commit -a`.

## Spot-checking for drift

Source (`/.agents/skills/nemoclawd-user-guide/`) and published
(`/skills/nemoclawd-user-guide/`) can drift if a source-side edit lands without
a corresponding refresh PR.
To check, ask an agent to compare the two directories before requesting signing.

## What goes in the catalog

Only customer-facing skills, identified by the `nemoclawd-user-*` naming
convention.
Internal skills (`nemoclaw-maintainer-*`, `nemoclaw-contributor-*`) must not be
copied into `skills/`.
