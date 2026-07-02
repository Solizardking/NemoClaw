export interface NemoClawdState {
    lastRunId: string | null;
    lastAction: string | null;
    blueprintVersion: string | null;
    sandboxName: string | null;
    migrationSnapshot: string | null;
    hostBackupPath: string | null;
    createdAt: string | null;
    updatedAt: string;
}
export declare function loadState(): NemoClawdState;
export declare function saveState(state: NemoClawdState): void;
export declare function clearState(): void;
//# sourceMappingURL=state.d.ts.map