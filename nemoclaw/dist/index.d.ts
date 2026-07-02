/**
 * Nemo Clawd — Clawd Plugin for OpenShell
 *
 * Uses the real Clawd plugin API. Types defined locally are minimal stubs
 * that match the Clawd SDK interfaces available at runtime via
 * `clawd/plugin-sdk`. We define them here because the SDK package is only
 * available inside the Clawd host process and cannot be imported at build
 * time.
 */
import type { Command } from "commander";
/** Subset of ClawdConfig that we actually read. */
export interface ClawdConfig {
    [key: string]: unknown;
}
/** Logger provided by the plugin host. */
export interface PluginLogger {
    info(message: string): void;
    warn(message: string): void;
    error(message: string): void;
    debug(message: string): void;
}
/** Context passed to slash-command handlers. */
export interface PluginCommandContext {
    senderId?: string;
    channel: string;
    isAuthorizedSender: boolean;
    args?: string;
    commandBody: string;
    config: ClawdConfig;
    from?: string;
    to?: string;
    accountId?: string;
}
/** Return value from a slash-command handler. */
export interface PluginCommandResult {
    text?: string;
    mediaUrl?: string;
    mediaUrls?: string[];
}
/** Registration shape for a slash command. */
export interface PluginCommandDefinition {
    name: string;
    description: string;
    acceptsArgs?: boolean;
    requireAuth?: boolean;
    handler: (ctx: PluginCommandContext) => PluginCommandResult | Promise<PluginCommandResult>;
}
/** Context passed to the CLI registrar callback. */
export interface PluginCliContext {
    program: Command;
    config: ClawdConfig;
    workspaceDir?: string;
    logger: PluginLogger;
}
/** CLI registrar callback type. */
export type PluginCliRegistrar = (ctx: PluginCliContext) => void | Promise<void>;
/** Auth method for a provider plugin. */
export interface ProviderAuthMethod {
    type: string;
    envVar?: string;
    headerName?: string;
    label?: string;
}
/** Model entry in a provider's model catalog. */
export interface ModelProviderEntry {
    id: string;
    label: string;
    contextWindow?: number;
    maxOutput?: number;
}
/** Model catalog shape. */
export interface ModelProviderConfig {
    chat?: ModelProviderEntry[];
    completion?: ModelProviderEntry[];
}
/** Registration shape for a custom model provider. */
export interface ProviderPlugin {
    id: string;
    label: string;
    docsPath?: string;
    aliases?: string[];
    envVars?: string[];
    models?: ModelProviderConfig;
    auth: ProviderAuthMethod[];
}
/** Background service registration. */
export interface PluginService {
    id: string;
    start: (ctx: {
        config: ClawdConfig;
        logger: PluginLogger;
    }) => void | Promise<void>;
    stop?: (ctx: {
        config: ClawdConfig;
        logger: PluginLogger;
    }) => void | Promise<void>;
}
/**
 * The API object injected into the plugin's register function by the Clawd
 * host. Only the methods we actually call are listed here.
 */
export interface ClawdPluginApi {
    id: string;
    name: string;
    version?: string;
    config: ClawdConfig;
    pluginConfig?: Record<string, unknown>;
    logger: PluginLogger;
    registerCommand: (command: PluginCommandDefinition) => void;
    registerCli: (registrar: PluginCliRegistrar, opts?: {
        commands?: string[];
    }) => void;
    registerProvider: (provider: ProviderPlugin) => void;
    registerService: (service: PluginService) => void;
    resolvePath: (input: string) => string;
    on: (hookName: string, handler: (...args: unknown[]) => void) => void;
}
export interface NemoClawdConfig {
    blueprintVersion: string;
    blueprintRegistry: string;
    sandboxName: string;
    inferenceProvider: string;
}
export declare function getPluginConfig(api: ClawdPluginApi): NemoClawdConfig;
export default function register(api: ClawdPluginApi): void;
//# sourceMappingURL=index.d.ts.map