import type { PluginLogger, NemoClawdConfig } from "../index.js";
export interface EjectOptions {
    runId?: string;
    confirm: boolean;
    logger: PluginLogger;
    pluginConfig: NemoClawdConfig;
}
export declare function cliEject(opts: EjectOptions): Promise<void>;
//# sourceMappingURL=eject.d.ts.map