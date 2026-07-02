export type EndpointType = "build" | "ncp" | "nim-local" | "vllm" | "ollama" | "custom";
export interface NemoClawdOnboardConfig {
    endpointType: EndpointType;
    endpointUrl: string;
    ncpPartner: string | null;
    model: string;
    profile: string;
    credentialEnv: string;
    onboardedAt: string;
}
export declare function loadOnboardConfig(): NemoClawdOnboardConfig | null;
export declare function saveOnboardConfig(config: NemoClawdOnboardConfig): void;
export declare function clearOnboardConfig(): void;
//# sourceMappingURL=config.d.ts.map