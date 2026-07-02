import type { PluginLogger, NemoClawdConfig } from "../index.js";
export interface LaunchOptions {
    force: boolean;
    profile: string;
    logger: PluginLogger;
    pluginConfig: NemoClawdConfig;
}
export declare function cliLaunch(opts: LaunchOptions): Promise<void>;
//# sourceMappingURL=launch.d.ts.map