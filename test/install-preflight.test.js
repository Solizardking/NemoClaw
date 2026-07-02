// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const INSTALLER = path.join(__dirname, "..", "install.sh");

function writeExecutable(target, contents) {
  fs.writeFileSync(target, contents, { mode: 0o755 });
}

describe("installer runtime preflight", () => {
  it("fails fast with a clear message on unsupported Node.js and npm", () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "nemoclawd-install-preflight-"));
    const fakeBin = path.join(tmp, "bin");
    fs.mkdirSync(fakeBin);

    writeExecutable(
      path.join(fakeBin, "node"),
      `#!/usr/bin/env bash
if [ "$1" = "--version" ]; then
  echo "v18.19.1"
  exit 0
fi
echo "unexpected node invocation: $*" >&2
exit 99
`,
    );

    writeExecutable(
      path.join(fakeBin, "npm"),
      `#!/usr/bin/env bash
if [ "$1" = "--version" ]; then
  echo "9.8.1"
  exit 0
fi
echo "unexpected npm invocation: $*" >&2
exit 98
`,
    );

    const result = spawnSync("bash", [INSTALLER], {
      cwd: path.join(__dirname, ".."),
      encoding: "utf-8",
      env: {
        ...process.env,
        HOME: tmp,
        PATH: `${fakeBin}:${process.env.PATH}`,
      },
    });

    const output = `${result.stdout}${result.stderr}`;
    assert.notEqual(result.status, 0);
    assert.match(output, /Unsupported runtime detected/);
    assert.match(output, /Node\.js >=20 and npm >=10/);
    assert.match(output, /v18\.19\.1/);
    assert.match(output, /9\.8\.1/);
  });

  it("seed-only mode creates private wallet, agent, model, and dry-run trading box metadata", () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "nemoclawd-install-seed-"));
    const fakeBin = path.join(tmp, "bin");
    const home = path.join(tmp, "home");
    fs.mkdirSync(fakeBin);

    writeExecutable(
      path.join(fakeBin, "node"),
      `#!/usr/bin/env bash
if [ "$1" = "--version" ]; then
  echo "v22.16.0"
  exit 0
fi
exec ${JSON.stringify(process.execPath)} "$@"
`,
    );

    writeExecutable(
      path.join(fakeBin, "npm"),
      `#!/usr/bin/env bash
if [ "$1" = "--version" ]; then
  echo "10.9.0"
  exit 0
fi
echo "unexpected npm invocation: $*" >&2
exit 98
`,
    );

    writeExecutable(
      path.join(fakeBin, "solana-keygen"),
      `#!/usr/bin/env bash
if [ "$1" = "new" ]; then
  out=""
  while [ "$#" -gt 0 ]; do
    if [ "$1" = "--outfile" ]; then
      shift
      out="$1"
    fi
    shift || true
  done
  [ -n "$out" ] || exit 97
  printf '[1,2,3,4]\\n' > "$out"
  exit 0
fi
if [ "$1" = "pubkey" ]; then
  echo "So11111111111111111111111111111111111111112"
  exit 0
fi
echo "unexpected solana-keygen invocation: $*" >&2
exit 96
`,
    );

    const result = spawnSync("bash", [INSTALLER], {
      cwd: path.join(__dirname, ".."),
      encoding: "utf-8",
      env: {
        ...process.env,
        HOME: tmp,
        NEMOCLAWD_HOME: home,
        NEMOCLAWD_INSTALL_SEED_ONLY: "1",
        NEMOCLAWD_NO_ANIMATION: "1",
        PATH: `${fakeBin}:${process.env.PATH}`,
      },
    });

    const output = `${result.stdout}${result.stderr}`;
    assert.equal(result.status, 0, output);

    const solanaConfig = JSON.parse(fs.readFileSync(path.join(home, "solana.json"), "utf-8"));
    assert.equal(solanaConfig.model, "8bit/DeepSolana");
    assert.equal(solanaConfig.provider, "ollama-local");
    assert.equal(solanaConfig.trading.mode, "dry-run");
    assert.equal(solanaConfig.trading.liveTradingEnabled, false);

    const wallets = JSON.parse(fs.readFileSync(path.join(home, "wallets", "wallets.json"), "utf-8"));
    assert.equal(wallets[0].provider, "local-keypair");
    assert.equal(wallets[0].address, "So11111111111111111111111111111111111111112");
    assert.equal(wallets[0].liveTradingEnabled, false);

    const keypairPath = path.join(home, "wallets", "nemoclawd-local-private-keypair.json");
    assert.equal(fs.statSync(keypairPath).mode & 0o777, 0o600);

    const agent = JSON.parse(fs.readFileSync(path.join(home, "agent.json"), "utf-8"));
    assert.equal(agent.theme, "lobster");
    assert.equal(agent.model.id, "8bit/DeepSolana");
    assert.equal(agent.wallet.provider, "local-keypair");

    const tradingBox = JSON.parse(fs.readFileSync(path.join(home, "trading-box.json"), "utf-8"));
    assert.equal(tradingBox.name, "nemoclawd-trading-box");
    assert.equal(tradingBox.mode, "dry-run");
    assert.equal(tradingBox.guardrails.signingEnabledByInstaller, false);
    assert.equal(tradingBox.guardrails.transactionSubmissionEnabledByInstaller, false);
  });
});
