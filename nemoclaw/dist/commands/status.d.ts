import type { PluginLogger, NemoClawdConfig } from "../index.js";
export interface StatusOptions {
    json: boolean;
    logger: PluginLogger;
    pluginConfig: NemoClawdConfig;
}
export declare function cliStatus(opts: StatusOptions): Promise<void>;
//# sourceMappingURL=status.d.ts.map