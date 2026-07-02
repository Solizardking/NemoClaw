// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { isLikelySolanaAddress } from "./solana.mts";

export const SOLANA_KEYCHAIN_TOOL = "tools/e2e/solana-keychain.mts";
export const SOLANA_KEYCHAIN_COMMAND =
  "node --experimental-strip-types tools/e2e/solana-keychain.mts --backend memory --environment development --cluster local-validator --private-key-path ~/.config/solana/id.json --json";

export type SolanaKeychainBackendId =
  | "memory"
  | "vault"
  | "aws_kms"
  | "gcp_kms"
  | "privy"
  | "turnkey"
  | "fireblocks"
  | "cdp"
  | "crossmint"
  | "dfns"
  | "openfort"
  | "para"
  | "utila";

export type SolanaKeychainEnvironment = "development" | "test" | "ci" | "staging" | "production";
export type SolanaKeychainCluster = "local-validator" | "devnet" | "testnet" | "mainnet" | "mainnet-beta" | "custom";
export type SolanaSignerRole = "operational" | "fee-payer" | "treasury" | "user-wallet";
export type SolanaKeychainStatus = "ready" | "blocked";
export type SolanaKeychainConfig = Record<string, unknown> & { backend: SolanaKeychainBackendId };
export type KeychainFactory = (config: Record<string, unknown>) => unknown | Promise<unknown>;

export type SolanaKeychainBackendMetadata = {
  id: SolanaKeychainBackendId;
  displayName: string;
  packageName: string;
  factoryExport: string;
  custodyModel: "in-process" | "self-hosted" | "cloud-kms" | "managed-wallet" | "mpc-custody";
  productionUse: boolean;
  remote: boolean;
  requiredFieldGroups: string[][];
  secretFields: string[];
  httpsFields: string[];
  recommendedRoles: SolanaSignerRole[];
};

export type SolanaKeychainReport = {
  name: "nemoclawd-solana-keychain";
  version: 1;
  mode: "signing-config-dry-run";
  status: SolanaKeychainStatus;
  generatedAt: string;
  signing: {
    backend: SolanaKeychainBackendId;
    displayName: string;
    role: SolanaSignerRole;
    environment: SolanaKeychainEnvironment;
    cluster: SolanaKeychainCluster;
    custodyModel: SolanaKeychainBackendMetadata["custodyModel"];
    remote: boolean;
    packageName: string;
    factoryExport: string;
    address: string | null;
    validAddress: boolean | null;
  };
  config: {
    redacted: Record<string, unknown>;
    requiredFields: string[];
    missingFields: string[];
    secretFieldsPresent: string[];
  };
  guardrails: {
    signerCreationEnabled: false;
    transactionSubmissionEnabled: false;
    privateKeyMaterialAllowed: boolean;
    rawSecretLoggingAllowed: false;
    explicitAllowSigningRequired: true;
    availabilityCheckRequired: boolean;
    separateHotColdSignersRecommended: boolean;
  };
  recommendations: {
    installCommand: string;
    preferredBackendsForRole: SolanaKeychainBackendId[];
    requiredEnv: string[];
  };
  blockers: string[];
  warnings: string[];
  nextCommands: string[];
};

export type BuildSolanaKeychainReportInput = {
  backend?: string;
  config?: Record<string, unknown>;
  env?: Record<string, string | undefined>;
  environment?: SolanaKeychainEnvironment;
  cluster?: SolanaKeychainCluster;
  role?: SolanaSignerRole;
  now?: Date;
};

export type CreateNemoSolanaSignerInput = BuildSolanaKeychainReportInput & {
  allowSigning?: boolean;
  factory?: KeychainFactory;
  verifyAvailability?: boolean;
};

export const KEYCHAIN_BACKENDS: readonly SolanaKeychainBackendMetadata[] = [
  {
    id: "memory",
    displayName: "Memory",
    packageName: "@solana/keychain-memory",
    factoryExport: "createMemorySigner",
    custodyModel: "in-process",
    productionUse: false,
    remote: false,
    requiredFieldGroups: [["privateKeyPath", "privateKey"]],
    secretFields: ["privateKey", "privateKeyPath"],
    httpsFields: [],
    recommendedRoles: ["operational", "fee-payer"],
  },
  {
    id: "vault",
    displayName: "HashiCorp Vault",
    packageName: "@solana/keychain-vault",
    factoryExport: "createVaultSigner",
    custodyModel: "self-hosted",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["vaultAddr"], ["vaultToken"], ["keyName"], ["publicKey"]],
    secretFields: ["vaultToken"],
    httpsFields: ["vaultAddr"],
    recommendedRoles: ["operational", "fee-payer", "treasury"],
  },
  {
    id: "aws_kms",
    displayName: "AWS KMS",
    packageName: "@solana/keychain-aws-kms",
    factoryExport: "createAwsKmsSigner",
    custodyModel: "cloud-kms",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["keyId"], ["publicKey"]],
    secretFields: [],
    httpsFields: [],
    recommendedRoles: ["operational", "fee-payer", "treasury"],
  },
  {
    id: "gcp_kms",
    displayName: "GCP KMS",
    packageName: "@solana/keychain-gcp-kms",
    factoryExport: "createGcpKmsSigner",
    custodyModel: "cloud-kms",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["keyName"], ["publicKey"]],
    secretFields: [],
    httpsFields: [],
    recommendedRoles: ["operational", "fee-payer", "treasury"],
  },
  {
    id: "privy",
    displayName: "Privy",
    packageName: "@solana/keychain-privy",
    factoryExport: "createPrivySigner",
    custodyModel: "managed-wallet",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["appId"], ["appSecret"], ["walletId"]],
    secretFields: ["appSecret"],
    httpsFields: [],
    recommendedRoles: ["user-wallet", "operational"],
  },
  {
    id: "turnkey",
    displayName: "Turnkey",
    packageName: "@solana/keychain-turnkey",
    factoryExport: "createTurnkeySigner",
    custodyModel: "managed-wallet",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["apiPublicKey"], ["apiPrivateKey"], ["organizationId"], ["privateKeyId"], ["publicKey"]],
    secretFields: ["apiPrivateKey"],
    httpsFields: [],
    recommendedRoles: ["user-wallet", "operational", "fee-payer", "treasury"],
  },
  {
    id: "fireblocks",
    displayName: "Fireblocks",
    packageName: "@solana/keychain-fireblocks",
    factoryExport: "createFireblocksSigner",
    custodyModel: "mpc-custody",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["apiKey"], ["privateKeyPem"], ["vaultAccountId"], ["assetId"]],
    secretFields: ["apiKey", "privateKeyPem"],
    httpsFields: [],
    recommendedRoles: ["treasury", "operational"],
  },
  {
    id: "cdp",
    displayName: "Coinbase Developer Platform",
    packageName: "@solana/keychain-cdp",
    factoryExport: "createCdpSigner",
    custodyModel: "managed-wallet",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["apiKeyId"], ["apiKeySecret"], ["walletSecret"], ["address"]],
    secretFields: ["apiKeySecret", "walletSecret"],
    httpsFields: [],
    recommendedRoles: ["user-wallet", "operational"],
  },
  {
    id: "crossmint",
    displayName: "Crossmint",
    packageName: "@solana/keychain-crossmint",
    factoryExport: "createCrossmintSigner",
    custodyModel: "managed-wallet",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["apiKey"], ["walletLocator"]],
    secretFields: ["apiKey"],
    httpsFields: [],
    recommendedRoles: ["user-wallet", "operational"],
  },
  {
    id: "dfns",
    displayName: "Dfns",
    packageName: "@solana/keychain-dfns",
    factoryExport: "createDfnsSigner",
    custodyModel: "mpc-custody",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["authToken"], ["credId"], ["privateKeyPem"], ["appId"], ["walletId"]],
    secretFields: ["authToken", "privateKeyPem"],
    httpsFields: [],
    recommendedRoles: ["treasury", "user-wallet", "operational"],
  },
  {
    id: "openfort",
    displayName: "Openfort",
    packageName: "@solana/keychain-openfort",
    factoryExport: "createOpenfortSigner",
    custodyModel: "managed-wallet",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["apiKey"], ["walletId"]],
    secretFields: ["apiKey"],
    httpsFields: [],
    recommendedRoles: ["user-wallet", "operational"],
  },
  {
    id: "para",
    displayName: "Para",
    packageName: "@solana/keychain-para",
    factoryExport: "createParaSigner",
    custodyModel: "mpc-custody",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["apiKey"], ["walletId"]],
    secretFields: ["apiKey"],
    httpsFields: [],
    recommendedRoles: ["treasury", "user-wallet", "operational"],
  },
  {
    id: "utila",
    displayName: "Utila",
    packageName: "@solana/keychain-utila",
    factoryExport: "createUtilaSigner",
    custodyModel: "mpc-custody",
    productionUse: true,
    remote: true,
    requiredFieldGroups: [["apiKey"], ["walletId"]],
    secretFields: ["apiKey"],
    httpsFields: [],
    recommendedRoles: ["treasury", "operational"],
  },
];

const BACKEND_ALIASES: Record<string, SolanaKeychainBackendId> = {
  "aws-kms": "aws_kms",
  awskms: "aws_kms",
  "gcp-kms": "gcp_kms",
  gcpkms: "gcp_kms",
  hashicorp: "vault",
  "hashicorp-vault": "vault",
  coinbase: "cdp",
  "coinbase-cdp": "cdp",
};

const BACKEND_ENV_FIELDS: Record<SolanaKeychainBackendId, Record<string, string[]>> = {
  memory: {
    privateKeyPath: ["SOLANA_KEYCHAIN_PRIVATE_KEY_PATH", "SOLANA_KEYPAIR_PATH"],
    privateKey: ["SOLANA_KEYCHAIN_PRIVATE_KEY"],
  },
  vault: {
    vaultAddr: ["SOLANA_KEYCHAIN_VAULT_ADDR", "VAULT_ADDR"],
    vaultToken: ["SOLANA_KEYCHAIN_VAULT_TOKEN", "VAULT_TOKEN"],
    keyName: ["SOLANA_KEYCHAIN_KEY_NAME", "SOLANA_KEYCHAIN_VAULT_KEY_NAME"],
    publicKey: ["SOLANA_KEYCHAIN_PUBLIC_KEY", "SOLANA_SIGNER_PUBLIC_KEY"],
  },
  aws_kms: {
    keyId: ["SOLANA_KEYCHAIN_AWS_KMS_KEY_ID", "AWS_KMS_KEY_ID"],
    publicKey: ["SOLANA_KEYCHAIN_PUBLIC_KEY", "SOLANA_SIGNER_PUBLIC_KEY"],
    region: ["AWS_REGION", "AWS_DEFAULT_REGION"],
  },
  gcp_kms: {
    keyName: ["SOLANA_KEYCHAIN_GCP_KMS_KEY_NAME", "GCP_KMS_KEY_NAME"],
    publicKey: ["SOLANA_KEYCHAIN_PUBLIC_KEY", "SOLANA_SIGNER_PUBLIC_KEY"],
  },
  privy: {
    appId: ["SOLANA_KEYCHAIN_PRIVY_APP_ID", "PRIVY_APP_ID"],
    appSecret: ["SOLANA_KEYCHAIN_PRIVY_APP_SECRET", "PRIVY_APP_SECRET"],
    walletId: ["SOLANA_KEYCHAIN_PRIVY_WALLET_ID", "PRIVY_WALLET_ID"],
  },
  turnkey: {
    apiPublicKey: ["SOLANA_KEYCHAIN_TURNKEY_API_PUBLIC_KEY", "TURNKEY_API_PUBLIC_KEY"],
    apiPrivateKey: ["SOLANA_KEYCHAIN_TURNKEY_API_PRIVATE_KEY", "TURNKEY_API_PRIVATE_KEY"],
    organizationId: ["SOLANA_KEYCHAIN_TURNKEY_ORGANIZATION_ID", "TURNKEY_ORGANIZATION_ID"],
    privateKeyId: ["SOLANA_KEYCHAIN_TURNKEY_PRIVATE_KEY_ID", "TURNKEY_PRIVATE_KEY_ID"],
    publicKey: ["SOLANA_KEYCHAIN_PUBLIC_KEY", "SOLANA_SIGNER_PUBLIC_KEY"],
  },
  fireblocks: {
    apiKey: ["SOLANA_KEYCHAIN_FIREBLOCKS_API_KEY", "FIREBLOCKS_API_KEY"],
    privateKeyPem: ["SOLANA_KEYCHAIN_FIREBLOCKS_PRIVATE_KEY_PEM", "FIREBLOCKS_PRIVATE_KEY_PEM"],
    vaultAccountId: ["SOLANA_KEYCHAIN_FIREBLOCKS_VAULT_ACCOUNT_ID", "FIREBLOCKS_VAULT_ACCOUNT_ID"],
    assetId: ["SOLANA_KEYCHAIN_FIREBLOCKS_ASSET_ID", "FIREBLOCKS_ASSET_ID"],
  },
  cdp: {
    apiKeyId: ["SOLANA_KEYCHAIN_CDP_API_KEY_ID", "CDP_API_KEY_ID"],
    apiKeySecret: ["SOLANA_KEYCHAIN_CDP_API_KEY_SECRET", "CDP_API_KEY_SECRET"],
    walletSecret: ["SOLANA_KEYCHAIN_CDP_WALLET_SECRET", "CDP_WALLET_SECRET"],
    address: ["SOLANA_KEYCHAIN_ADDRESS", "SOLANA_SIGNER_PUBLIC_KEY"],
  },
  crossmint: {
    apiKey: ["SOLANA_KEYCHAIN_CROSSMINT_API_KEY", "CROSSMINT_API_KEY"],
    walletLocator: ["SOLANA_KEYCHAIN_CROSSMINT_WALLET_LOCATOR", "CROSSMINT_WALLET_LOCATOR"],
  },
  dfns: {
    authToken: ["SOLANA_KEYCHAIN_DFNS_AUTH_TOKEN", "DFNS_AUTH_TOKEN"],
    credId: ["SOLANA_KEYCHAIN_DFNS_CRED_ID", "DFNS_CRED_ID"],
    privateKeyPem: ["SOLANA_KEYCHAIN_DFNS_PRIVATE_KEY_PEM", "DFNS_PRIVATE_KEY_PEM"],
    appId: ["SOLANA_KEYCHAIN_DFNS_APP_ID", "DFNS_APP_ID"],
    walletId: ["SOLANA_KEYCHAIN_DFNS_WALLET_ID", "DFNS_WALLET_ID"],
  },
  openfort: {
    apiKey: ["SOLANA_KEYCHAIN_OPENFORT_API_KEY", "OPENFORT_API_KEY"],
    walletId: ["SOLANA_KEYCHAIN_OPENFORT_WALLET_ID", "OPENFORT_WALLET_ID"],
  },
  para: {
    apiKey: ["SOLANA_KEYCHAIN_PARA_API_KEY", "PARA_API_KEY"],
    walletId: ["SOLANA_KEYCHAIN_PARA_WALLET_ID", "PARA_WALLET_ID"],
  },
  utila: {
    apiKey: ["SOLANA_KEYCHAIN_UTILA_API_KEY", "UTILA_API_KEY"],
    walletId: ["SOLANA_KEYCHAIN_UTILA_WALLET_ID", "UTILA_WALLET_ID"],
  },
};

const NON_PRODUCTION_ENVIRONMENTS = new Set<SolanaKeychainEnvironment>(["development", "test", "ci"]);
const MAINNET_CLUSTERS = new Set<SolanaKeychainCluster>(["mainnet", "mainnet-beta"]);
const TREASURY_CUSTODY_MODELS = new Set<SolanaKeychainBackendMetadata["custodyModel"]>([
  "mpc-custody",
  "cloud-kms",
  "self-hosted",
]);

export function parseKeychainBackend(value: string | undefined): SolanaKeychainBackendId {
  const normalized = (value || "memory").trim().toLowerCase().replace(/_/g, "-");
  const aliased = BACKEND_ALIASES[normalized];
  if (aliased) return aliased;
  const canonical = normalized.replace(/-/g, "_") as SolanaKeychainBackendId;
  if (KEYCHAIN_BACKENDS.some((backend) => backend.id === canonical)) return canonical;
  throw new Error(`Unsupported Solana Keychain backend "${value}".`);
}

export function getKeychainBackendMetadata(backend: SolanaKeychainBackendId): SolanaKeychainBackendMetadata {
  const metadata = KEYCHAIN_BACKENDS.find((item) => item.id === backend);
  if (!metadata) throw new Error(`Unsupported Solana Keychain backend "${backend}".`);
  return metadata;
}

export function buildSolanaKeychainConfigFromEnv(input: {
  env?: Record<string, string | undefined>;
  backend?: string;
  overrides?: Record<string, unknown>;
} = {}): SolanaKeychainConfig {
  const env = input.env || process.env;
  const backend = parseKeychainBackend(input.backend || env.SOLANA_KEYCHAIN_BACKEND);
  const config: SolanaKeychainConfig = { backend };
  for (const [field, envNames] of Object.entries(BACKEND_ENV_FIELDS[backend])) {
    const value = firstEnvValue(env, envNames);
    if (value) config[field] = value;
  }
  for (const [field, value] of Object.entries(input.overrides || {})) {
    if (value !== undefined && value !== "") config[field] = value;
  }
  return config;
}

export function buildSolanaKeychainReport(input: BuildSolanaKeychainReportInput = {}): SolanaKeychainReport {
  const env = input.env || process.env;
  const environment = input.environment || parseEnvironment(env.SOLANA_KEYCHAIN_ENVIRONMENT || env.NODE_ENV);
  const cluster = input.cluster || parseCluster(env.SOLANA_KEYCHAIN_CLUSTER || env.SOLANA_CLUSTER);
  const role = input.role || parseRole(env.SOLANA_KEYCHAIN_ROLE || "operational");
  const config = normalizeKeychainConfig(input.config, input.backend, env);
  const metadata = getKeychainBackendMetadata(config.backend);
  const blockers: string[] = [];
  const warnings: string[] = [];
  const missingFields = findMissingFieldGroups(metadata, config);
  const address = extractSignerAddress(config);
  const validAddress = address ? isLikelySolanaAddress(address) : null;

  if (missingFields.length > 0) {
    blockers.push(`${metadata.displayName} signer config is missing ${missingFields.join(", ")}.`);
  }
  if (address && !validAddress) {
    blockers.push("signer address is not a valid Solana base58 address shape.");
  }
  for (const issue of httpsIssues(metadata, config)) {
    blockers.push(issue);
  }
  if (config.backend === "memory" && (!NON_PRODUCTION_ENVIRONMENTS.has(environment) || MAINNET_CLUSTERS.has(cluster))) {
    blockers.push("memory signing is limited to development, test, or CI on non-mainnet clusters.");
  }
  if (environment === "production" && !metadata.productionUse) {
    blockers.push(`${metadata.displayName} is not a production signing backend.`);
  }
  if (role === "treasury" && !TREASURY_CUSTODY_MODELS.has(metadata.custodyModel)) {
    warnings.push("treasury signing should use MPC custody, cloud KMS/HSM, or Vault with approval controls.");
  }
  if (role === "user-wallet" && metadata.custodyModel !== "managed-wallet" && metadata.custodyModel !== "mpc-custody") {
    warnings.push("user-wallet signing usually belongs on a managed wallet or MPC backend.");
  }
  if (MAINNET_CLUSTERS.has(cluster) && environment !== "production") {
    warnings.push("mainnet signing config should normally run with environment=production and separate hot/cold signer roles.");
  }
  if (config.backend === "memory") {
    warnings.push("memory signing keeps key material in process; use it only for local development, tests, or CI fixtures.");
  }

  const requiredEnv = requiredEnvForBackend(config.backend);
  const preferredBackends = preferredBackendsForRole(role);
  return {
    name: "nemoclawd-solana-keychain",
    version: 1,
    mode: "signing-config-dry-run",
    status: blockers.length > 0 ? "blocked" : "ready",
    generatedAt: (input.now || new Date()).toISOString(),
    signing: {
      backend: config.backend,
      displayName: metadata.displayName,
      role,
      environment,
      cluster,
      custodyModel: metadata.custodyModel,
      remote: metadata.remote,
      packageName: metadata.packageName,
      factoryExport: metadata.factoryExport,
      address,
      validAddress,
    },
    config: {
      redacted: redactKeychainConfig(config),
      requiredFields: metadata.requiredFieldGroups.map((group) => group.join(" or ")),
      missingFields,
      secretFieldsPresent: secretFieldsPresent(metadata, config),
    },
    guardrails: {
      signerCreationEnabled: false,
      transactionSubmissionEnabled: false,
      privateKeyMaterialAllowed: config.backend === "memory" && NON_PRODUCTION_ENVIRONMENTS.has(environment),
      rawSecretLoggingAllowed: false,
      explicitAllowSigningRequired: true,
      availabilityCheckRequired: metadata.remote,
      separateHotColdSignersRecommended: role === "treasury" || MAINNET_CLUSTERS.has(cluster),
    },
    recommendations: {
      installCommand: `npm install ${metadata.packageName}`,
      preferredBackendsForRole: preferredBackends,
      requiredEnv,
    },
    blockers,
    warnings,
    nextCommands: [
      SOLANA_KEYCHAIN_COMMAND,
      `npm install ${metadata.packageName}`,
      "store backend credentials in the deployment secret manager",
      "call signer.isAvailable() before signing through remote backends",
    ],
  };
}

export function redactKeychainConfig(config: Record<string, unknown>): Record<string, unknown> {
  const backend = parseKeychainBackend(stringValue(config.backend));
  const metadata = getKeychainBackendMetadata(backend);
  const redacted: Record<string, unknown> = {};
  for (const [field, value] of Object.entries(config)) {
    if (value === undefined || value === "") continue;
    redacted[field] = shouldRedactField(metadata, field) ? "<redacted>" : value;
  }
  return redacted;
}

export function sanitizeKeychainError(error: unknown, config?: Record<string, unknown>): string {
  let message = error instanceof Error ? error.message : String(error);
  for (const value of Object.values(config || {})) {
    if (typeof value === "string" && value.length >= 4) {
      message = message.split(value).join("<redacted>");
    }
  }
  return message.replace(
    /\b(?:hvs\.[A-Za-z0-9._-]+|sk_[A-Za-z0-9._-]+|-----BEGIN [^-]+ PRIVATE KEY-----[\s\S]*?-----END [^-]+ PRIVATE KEY-----)\b/g,
    "<redacted>",
  );
}

export async function createNemoSolanaSigner(input: CreateNemoSolanaSignerInput): Promise<unknown> {
  const report = buildSolanaKeychainReport(input);
  const config = normalizeKeychainConfig(input.config, input.backend, input.env || process.env);
  if (!input.allowSigning) {
    throw new Error("Solana Keychain signer creation requires allowSigning=true.");
  }
  if (report.status === "blocked") {
    throw new Error(`Solana Keychain signer is blocked: ${report.blockers.join("; ")}`);
  }
  try {
    const factory = input.factory || (await loadKeychainBackendFactory(config.backend));
    const signer = await factory(keychainFactoryConfig(config));
    if (input.verifyAvailability && isAvailabilityCheckable(signer) && !(await signer.isAvailable())) {
      throw new Error("Solana Keychain signer backend is unavailable.");
    }
    return signer;
  } catch (error: unknown) {
    throw new Error(sanitizeKeychainError(error, config));
  }
}

export async function loadKeychainBackendFactory(backend: SolanaKeychainBackendId): Promise<KeychainFactory> {
  const metadata = getKeychainBackendMetadata(backend);
  let module: Record<string, unknown>;
  try {
    module = (await import(metadata.packageName)) as Record<string, unknown>;
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Install ${metadata.packageName} to use the ${metadata.displayName} signer. ${message}`);
  }
  const factory = module[metadata.factoryExport];
  if (typeof factory !== "function") {
    throw new Error(`${metadata.packageName} does not export ${metadata.factoryExport}.`);
  }
  return factory as KeychainFactory;
}

export function renderSolanaKeychainMarkdown(report: SolanaKeychainReport): string {
  const lines: string[] = [];
  lines.push("# Nemo Clawd Solana Keychain");
  lines.push("");
  lines.push(`Status: **${report.status}**`);
  lines.push(`Backend: \`${report.signing.backend}\` (${report.signing.displayName})`);
  lines.push(`Role: \`${report.signing.role}\``);
  lines.push(`Environment: \`${report.signing.environment}\``);
  lines.push(`Cluster: \`${report.signing.cluster}\``);
  lines.push(`Address: \`${report.signing.address || "unconfigured"}\``);
  lines.push("");
  lines.push("## Config");
  lines.push(`- Package: \`${report.signing.packageName}\``);
  lines.push(`- Factory: \`${report.signing.factoryExport}\``);
  lines.push(`- Required fields: ${formatInlineList(report.config.requiredFields)}`);
  lines.push(`- Missing fields: ${formatInlineList(report.config.missingFields)}`);
  lines.push(`- Secret fields present: ${formatInlineList(report.config.secretFieldsPresent)}`);
  lines.push("");
  lines.push("## Guardrails");
  lines.push("- Signer creation enabled by this report: `false`");
  lines.push("- Transaction submission enabled: `false`");
  lines.push(`- Private key material allowed: \`${String(report.guardrails.privateKeyMaterialAllowed)}\``);
  lines.push("- Raw secret logging allowed: `false`");
  lines.push("- Explicit allowSigning call required: `true`");
  lines.push(`- Availability check required: \`${String(report.guardrails.availabilityCheckRequired)}\``);
  lines.push("");
  lines.push("## Recommendations");
  lines.push(`- Install selected backend: \`${report.recommendations.installCommand}\``);
  lines.push(`- Preferred backends for role: ${formatInlineList(report.recommendations.preferredBackendsForRole)}`);
  lines.push(`- Required env: ${formatInlineList(report.recommendations.requiredEnv)}`);
  lines.push("");
  lines.push("## Blockers");
  if (report.blockers.length === 0) {
    lines.push("- _None._");
  } else {
    for (const blocker of report.blockers) lines.push(`- ${blocker}`);
  }
  lines.push("");
  lines.push("## Warnings");
  if (report.warnings.length === 0) {
    lines.push("- _None._");
  } else {
    for (const warning of report.warnings) lines.push(`- ${warning}`);
  }
  return `${lines.join("\n")}\n`;
}

function normalizeKeychainConfig(
  config: Record<string, unknown> | undefined,
  backendInput: string | undefined,
  env: Record<string, string | undefined>,
): SolanaKeychainConfig {
  if (!config) return buildSolanaKeychainConfigFromEnv({ env, backend: backendInput });
  const backend = parseKeychainBackend(backendInput || stringValue(config.backend) || env.SOLANA_KEYCHAIN_BACKEND);
  return { ...config, backend };
}

function keychainFactoryConfig(config: SolanaKeychainConfig): Record<string, unknown> {
  const factoryConfig = { ...config };
  delete factoryConfig.backend;
  return factoryConfig;
}

function parseEnvironment(value: string | undefined): SolanaKeychainEnvironment {
  if (value === "production" || value === "staging" || value === "test" || value === "ci") return value;
  return "development";
}

function parseCluster(value: string | undefined): SolanaKeychainCluster {
  if (
    value === "local-validator" ||
    value === "devnet" ||
    value === "testnet" ||
    value === "mainnet" ||
    value === "mainnet-beta" ||
    value === "custom"
  ) {
    return value;
  }
  return "devnet";
}

function parseRole(value: string | undefined): SolanaSignerRole {
  if (value === "fee-payer" || value === "treasury" || value === "user-wallet") return value;
  return "operational";
}

function firstEnvValue(env: Record<string, string | undefined>, names: readonly string[]): string | undefined {
  for (const name of names) {
    const value = env[name]?.trim();
    if (value) return value;
  }
  return undefined;
}

function findMissingFieldGroups(metadata: SolanaKeychainBackendMetadata, config: Record<string, unknown>): string[] {
  const missing: string[] = [];
  for (const group of metadata.requiredFieldGroups) {
    if (group.every((field) => !hasConfigValue(config[field]))) {
      missing.push(group.join(" or "));
    }
  }
  return missing;
}

function httpsIssues(metadata: SolanaKeychainBackendMetadata, config: Record<string, unknown>): string[] {
  const issues: string[] = [];
  const fields = new Set([
    ...metadata.httpsFields,
    ...Object.keys(config).filter((field) => /(?:Url|Uri|Endpoint|Addr)$/i.test(field)),
  ]);
  for (const field of fields) {
    const value = stringValue(config[field]);
    if (value && !isHttpsUrl(value)) {
      issues.push(`${field} must be an HTTPS URL for remote signing backends.`);
    }
  }
  return issues;
}

function extractSignerAddress(config: Record<string, unknown>): string | null {
  return cleanOptional(stringValue(config.publicKey) || stringValue(config.address));
}

function requiredEnvForBackend(backend: SolanaKeychainBackendId): string[] {
  return Object.values(BACKEND_ENV_FIELDS[backend])
    .map((names) => names[0])
    .filter(Boolean);
}

function preferredBackendsForRole(role: SolanaSignerRole): SolanaKeychainBackendId[] {
  return KEYCHAIN_BACKENDS.filter((backend) => backend.recommendedRoles.includes(role) && backend.productionUse).map(
    (backend) => backend.id,
  );
}

function secretFieldsPresent(metadata: SolanaKeychainBackendMetadata, config: Record<string, unknown>): string[] {
  return Object.keys(config).filter((field) => shouldRedactField(metadata, field) && hasConfigValue(config[field]));
}

function shouldRedactField(metadata: SolanaKeychainBackendMetadata, field: string): boolean {
  if (metadata.secretFields.includes(field)) return true;
  const normalized = field.toLowerCase();
  if (normalized === "publickey" || normalized === "apipublickey" || normalized === "keyid") return false;
  return /(secret|token|password|credential|privatekey|private_key|pem|apikey|api_key|auth)/i.test(field);
}

function isHttpsUrl(value: string): boolean {
  try {
    return new URL(value).protocol === "https:";
  } catch {
    return false;
  }
}

function hasConfigValue(value: unknown): boolean {
  return value !== undefined && value !== null && String(value).trim() !== "";
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function cleanOptional(value: string | undefined | null): string | null {
  const cleaned = value?.trim();
  return cleaned ? cleaned : null;
}

function isAvailabilityCheckable(value: unknown): value is { isAvailable: () => Promise<boolean> } {
  return Boolean(value && typeof value === "object" && typeof (value as { isAvailable?: unknown }).isAvailable === "function");
}

function formatInlineList(values: readonly string[]): string {
  return values.length === 0 ? "_None._" : values.map((value) => `\`${value}\``).join(", ");
}
