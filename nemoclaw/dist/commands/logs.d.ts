import type { PluginLogger, NemoClawdConfig } from "../index.js";
export interface LogsOptions {
    follow: boolean;
    lines: number;
    runId?: string;
    logger: PluginLogger;
    pluginConfig: NemoClawdConfig;
}
export declare function cliLogs(opts: LogsOptions): Promise<void>;
//# sourceMappingURL=logs.d.ts.map