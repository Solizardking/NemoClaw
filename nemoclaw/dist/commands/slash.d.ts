/**
 * Handler for the /nemoclawd slash command (chat interface).
 *
 * Supports subcommands:
 *   /nemoclawd status   - show sandbox/blueprint/inference state
 *   /nemoclawd eject    - rollback to host installation
 *   /nemoclawd          - show help
 */
import type { PluginCommandContext, PluginCommandResult, ClawdPluginApi } from "../index.js";
export declare function handleSlashCommand(ctx: PluginCommandContext, _api: ClawdPluginApi): PluginCommandResult;
//# sourceMappingURL=slash.d.ts.map