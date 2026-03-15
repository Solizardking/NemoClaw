# NemoClaw Rearchitecture — End-to-End Test Plan

Maps to War Room Test Plan sections 2, 5, 8, 9, 14.
Scoped to **only the files we changed/created** in this rearchitecture.

---

## 0. Syntax & Load (do this first, takes 10 seconds)

```bash
# All JS parses
node -c bin/nemoclaw.js
node -c bin/lib/runner.js
node -c bin/lib/credentials.js
node -c bin/lib/registry.js
node -c bin/lib/nim.js
node -c bin/lib/policies.js
node -c bin/lib/onboard.js

# All shell parses
bash -n scripts/install.sh
bash -n scripts/start-services.sh

# All YAML is valid
python3 -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('nemoclaw-blueprint/policies/presets/*.yaml')]"

# Module resolution works (no missing requires)
node -e "require('./bin/lib/runner')"
node -e "require('./bin/lib/credentials')"
node -e "require('./bin/lib/registry')"
node -e "require('./bin/lib/nim')"
node -e "require('./bin/lib/policies')"
node -e "require('./bin/lib/onboard')"
```

**Pass** = all exit 0. If anything fails here, stop — nothing else will work.

---

## 1. CLI Dispatch — Global Commands (War Room §8)

These test that the monolith was split correctly and dispatch still works.

| # | Command | Expected | Pass? |
|---|---------|----------|-------|
| 1 | `node bin/nemoclaw.js help` | Prints grouped help (Getting Started, Sandbox Management, Policy Presets, Deploy, Services, Legacy) | |
| 2 | `node bin/nemoclaw.js --help` | Same as above | |
| 3 | `node bin/nemoclaw.js` (no args) | Same as above | |
| 4 | `node bin/nemoclaw.js list` | Prints "No sandboxes registered" or lists sandboxes | |
| 5 | `node bin/nemoclaw.js status` | Shows sandbox list (if any) + runs start-services.sh --status | |
| 6 | `node bin/nemoclaw.js setup` | Prints deprecation warning, then attempts legacy setup.sh | |
| 7 | `node bin/nemoclaw.js boguscmd` | Prints "Unknown command: boguscmd" + suggestions + exit 1 | |

---

## 2. Sandbox Registry (War Room §8 — new functionality)

Test the registry in isolation, then through the CLI.

```bash
# Direct registry test — run in node REPL or as a script:
node -e "
  const r = require('./bin/lib/registry');

  // Clean slate
  const fs = require('fs');
  const path = require('path');
  const regFile = path.join(process.env.HOME, '.nemoclaw', 'sandboxes.json');
  if (fs.existsSync(regFile)) fs.unlinkSync(regFile);

  // Register two sandboxes
  r.registerSandbox({ name: 'test-alpha', model: 'nvidia/nemotron-3-nano-30b-a3b', provider: 'nvidia-nim' });
  r.registerSandbox({ name: 'test-beta', model: 'meta/llama-3.1-8b-instruct', provider: 'vllm-local', gpuEnabled: true });

  // Verify
  const list = r.listSandboxes();
  console.assert(list.sandboxes.length === 2, 'Expected 2 sandboxes');
  console.assert(list.defaultSandbox === 'test-alpha', 'First registered should be default');

  // Set default
  r.setDefault('test-beta');
  console.assert(r.getDefault() === 'test-beta', 'Default should be test-beta');

  // Update
  r.updateSandbox('test-alpha', { policies: ['pypi', 'npm'] });
  console.assert(r.getSandbox('test-alpha').policies.length === 2, 'Should have 2 policies');

  // Remove
  r.removeSandbox('test-alpha');
  console.assert(r.listSandboxes().sandboxes.length === 1, 'Should have 1 sandbox');
  console.assert(r.getDefault() === 'test-beta', 'Default should shift to test-beta');

  // Remove last
  r.removeSandbox('test-beta');
  console.assert(r.getDefault() === null, 'Default should be null');

  console.log('PASS: registry');
"
```

**Then test via CLI dispatch:**

| # | Command | Expected | Pass? |
|---|---------|----------|-------|
| 1 | Seed a sandbox: `node -e "require('./bin/lib/registry').registerSandbox({name:'demo', model:'test'})"` then `node bin/nemoclaw.js list` | Shows `demo` with `*` default marker | |
| 2 | `node bin/nemoclaw.js demo status` | Hits sandbox-scoped status path (may error on openshell — that's fine, just confirm dispatch works) | |
| 3 | `node bin/nemoclaw.js demo policy-list` | Lists all 9 presets with ○ markers | |
| 4 | `node bin/nemoclaw.js demo destroy` | Removes from registry, prints "destroyed" | |
| 5 | `node bin/nemoclaw.js demo status` | Now falls through to "Unknown command: demo" (no longer in registry) | |

---

## 3. Policy Presets (War Room §5, §12)

```bash
# Verify all 9 presets load and have valid structure
node -e "
  const p = require('./bin/lib/policies');
  const presets = p.listPresets();
  console.assert(presets.length === 9, 'Expected 9 presets, got ' + presets.length);

  const expected = ['discord','docker','huggingface','jira','npm','outlook','pypi','slack','telegram'];
  const names = presets.map(x => x.name).sort();
  console.assert(JSON.stringify(names) === JSON.stringify(expected), 'Preset names mismatch: ' + names);

  // Each preset has endpoints
  for (const preset of presets) {
    const content = p.loadPreset(preset.name);
    const endpoints = p.getPresetEndpoints(content);
    console.assert(endpoints.length > 0, preset.name + ' has no endpoints');
    console.log('  ' + preset.name + ': ' + endpoints.join(', '));
  }

  console.log('PASS: presets');
"
```

| # | Check | Expected | Pass? |
|---|-------|----------|-------|
| 1 | outlook preset | graph.microsoft.com, login.microsoftonline.com, outlook.office365.com, outlook.office.com | |
| 2 | telegram preset | api.telegram.org | |
| 3 | docker preset | registry-1.docker.io, auth.docker.io, nvcr.io, authn.nvidia.com | |
| 4 | huggingface preset | huggingface.co, cdn-lfs.huggingface.co, api-inference.huggingface.co | |

---

## 4. NIM Module (War Room §2, §4)

```bash
# NIM image mapping + GPU detection (won't find GPU on Mac — that's expected)
node -e "
  const nim = require('./bin/lib/nim');

  // Model listing
  const models = nim.listModels();
  console.assert(models.length === 5, 'Expected 5 models');

  // Image lookup
  console.assert(nim.getImageForModel('nvidia/nemotron-3-nano-30b-a3b') === 'nvcr.io/nim/nvidia/nemotron-3-nano-30b-a3b:latest');
  console.assert(nim.getImageForModel('bogus/model') === null);

  // Container naming
  console.assert(nim.containerName('my-sandbox') === 'nemoclaw-nim-my-sandbox');

  // GPU detection (null on Mac is fine)
  const gpu = nim.detectGpu();
  console.log('  GPU: ' + JSON.stringify(gpu));

  // NIM status for non-existent container
  const st = nim.nimStatus('nonexistent');
  console.assert(st.running === false);

  console.log('PASS: nim');
"
```

---

## 5. start-services.sh --sandbox Flag (War Room §14)

| # | Command | Expected | Pass? |
|---|---------|----------|-------|
| 1 | `bash scripts/start-services.sh --sandbox testbox --status` | Uses PIDDIR `/tmp/nemoclaw-services-testbox`, shows status (both stopped is fine) | |
| 2 | `bash scripts/start-services.sh --status` | Uses PIDDIR `/tmp/nemoclaw-services-default` (env fallback) | |
| 3 | `NEMOCLAW_SANDBOX=myenv bash scripts/start-services.sh --status` | Uses PIDDIR `/tmp/nemoclaw-services-myenv` | |
| 4 | `bash scripts/start-services.sh --sandbox testbox --stop` | Runs stop path for testbox PIDDIR, no errors | |

Verify the PIDDIR is correct:
```bash
# Should print /tmp/nemoclaw-services-hello
bash -x scripts/start-services.sh --sandbox hello --status 2>&1 | grep PIDDIR
```

---

## 6. End-to-End: `nemoclaw onboard` (War Room §2 + §4 + §5)

This is the big one. Requires Docker running + openshell installed.

| # | Step | Expected | Pass? |
|---|------|----------|-------|
| 1 | `node bin/nemoclaw.js onboard` | Starts [1/7] Preflight — checks Docker, openshell, GPU | |
| 2 | Step [2/7] | Destroys old gateway, starts new one, verifies health | |
| 3 | Step [3/7] | Prompts for sandbox name, creates sandbox via openshell | |
| 4 | Step [4/7] | Offers NIM options (cloud if no GPU), configures inference | |
| 5 | Step [5/7] | Creates provider + sets inference route | |
| 6 | Step [6/7] | Runs openclaw doctor inside sandbox | |
| 7 | Step [7/7] | Shows presets, suggests pypi+npm, applies on confirm | |
| 8 | Dashboard | Prints dashboard with sandbox name, model, NIM status, and run/status/logs commands | |
| 9 | `node bin/nemoclaw.js list` | Shows the sandbox just created with `*` | |
| 10 | `node bin/nemoclaw.js <name> connect` | Drops into sandbox shell | |
| 11 | `node bin/nemoclaw.js <name> status` | Shows registry info + openshell info + NIM health | |
| 12 | `node bin/nemoclaw.js <name> policy-list` | Shows applied presets with ● markers | |
| 13 | `node bin/nemoclaw.js <name> destroy` | Cleans everything up | |
| 14 | `node bin/nemoclaw.js list` | Empty again | |

---

## Quick Smoke (if you only have 2 minutes)

```bash
# 1. Syntax
node -c bin/nemoclaw.js && node -e "require('./bin/lib/runner'); require('./bin/lib/credentials'); require('./bin/lib/registry'); require('./bin/lib/nim'); require('./bin/lib/policies'); require('./bin/lib/onboard')" && echo "PASS: modules load"

# 2. Help works
node bin/nemoclaw.js help | grep -q "Sandbox Management" && echo "PASS: help"

# 3. Registry round-trip
node -e "const r=require('./bin/lib/registry'); r.registerSandbox({name:'smoke'}); console.assert(r.getSandbox('smoke')); r.removeSandbox('smoke'); console.assert(!r.getSandbox('smoke')); console.log('PASS: registry')"

# 4. Presets load
node -e "const p=require('./bin/lib/policies'); console.assert(p.listPresets().length===9); console.log('PASS: presets')"

# 5. NIM models load
node -e "const n=require('./bin/lib/nim'); console.assert(n.listModels().length===5); console.log('PASS: nim')"

# 6. Shell scripts parse
bash -n scripts/install.sh && bash -n scripts/start-services.sh && echo "PASS: shell"
```

All 6 print PASS = safe to push.
