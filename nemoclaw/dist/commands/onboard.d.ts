import type { PluginLogger, NemoClawdConfig } from "../index.js";
export interface OnboardOptions {
    apiKey?: string;
    endpoint?: string;
    ncpPartner?: string;
    endpointUrl?: string;
    model?: string;
    logger: PluginLogger;
    pluginConfig: NemoClawdConfig;
}
export declare function cliOnboard(opts: OnboardOptions): Promise<void>;
//# sourceMappingURL=onboard.d.ts.map