import type { PluginLogger, NemoClawdConfig } from "../index.js";
export { detectHostClawd, type HostClawdState } from "./migration-state.js";
export interface MigrateOptions {
    dryRun: boolean;
    profile: string;
    skipBackup: boolean;
    logger: PluginLogger;
    pluginConfig: NemoClawdConfig;
}
export declare function cliMigrate(opts: MigrateOptions): Promise<void>;
//# sourceMappingURL=migrate.d.ts.map