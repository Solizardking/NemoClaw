## Description: <br>
Guides human users' AI agents through the Solana-native Nemo Clawd install, MCP tools, xAI Grok setup, sandbox policies, and safe operating workflows. <br>

This skill is ready for local development use and requires a fresh catalog signature before publication. <br>

## Owner
Nemo Clawd maintainers <br>

### License/Terms of Use: <br>
Apache 2.0 <br>

## Use Case: <br>
Developers and operators using AI coding assistants to install, configure, operate, troubleshoot, or secure `nemoclawd` Solana agents. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Agent-assisted setup could expose wallet secrets, API keys, or unsafe mainnet transaction steps. <br>
Mitigation: Require redacted placeholders, explicit user confirmation for mainnet actions, and local validation commands after setup. <br>

## Reference(s): <br>
- `README.md` <br>
- `install.sh` <br>
- `nemo-clawd-mcp/README.md` <br>
- `nemoclaw-blueprint/` <br>
- `src/commands/` <br>

## Skill Output: <br>
**Output Type(s):** [Documentation routing, Configuration instructions, Shell commands] <br>
**Output Format:** [Markdown with inline bash code blocks] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [None] <br>

## Evaluation Agents Used: <br>
- Codex (`codex`) <br>

## Evaluation Tasks: <br>
Local rewrite evaluation pending after the `nemoclawd-user-guide` rename. <br>

## Evaluation Metrics Used: <br>
Security, correctness, discoverability, effectiveness, and efficiency. <br>

## Evaluation Results: <br>
Pending re-run. The previous user-guide benchmark no longer applies after the Nemo Clawd rewrite. <br>

## Skill Version(s): <br>
0.5.0 (source: package.json) <br>

## Ethical Considerations: <br>
Operators should treat live Solana trading and wallet automation as high-risk. Use restrictive policies, avoid sharing secrets, and verify transactions before approval. <br>
