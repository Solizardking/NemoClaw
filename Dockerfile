# NemoClaw sandbox image — OpenClaw + NemoClaw plugin inside OpenShell

FROM node:22-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv \
        curl git ca-certificates \
        iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Create sandbox user (matches OpenShell convention)
RUN groupadd -r sandbox && useradd -r -g sandbox -d /sandbox -s /bin/bash sandbox \
    && mkdir -p /sandbox/.openclaw /sandbox/.nemoclaw \
    && chown -R sandbox:sandbox /sandbox

# Install OpenClaw CLI
RUN npm install -g openclaw@2026.3.11

# Install PyYAML for blueprint runner
RUN pip3 install --break-system-packages pyyaml

# Copy our plugin and blueprint into the sandbox
COPY nemoclaw/dist/ /opt/nemoclaw/dist/
COPY nemoclaw/openclaw.plugin.json /opt/nemoclaw/
COPY nemoclaw/package.json /opt/nemoclaw/
COPY nemoclaw-blueprint/ /opt/nemoclaw-blueprint/

# Install runtime dependencies only (no devDependencies, no build step)
WORKDIR /opt/nemoclaw
RUN npm install --omit=dev

# Set up blueprint for local resolution
RUN mkdir -p /sandbox/.nemoclaw/blueprints/0.1.0 \
    && cp -r /opt/nemoclaw-blueprint/* /sandbox/.nemoclaw/blueprints/0.1.0/

# Copy startup script
COPY scripts/nemoclaw-start.sh /usr/local/bin/nemoclaw-start
RUN chmod +x /usr/local/bin/nemoclaw-start

WORKDIR /sandbox
USER sandbox

# Pre-create OpenClaw directories and bake in auth + model config
# so the sandbox is ready the moment you connect (no entrypoint needed)
RUN mkdir -p /sandbox/.openclaw/agents/main/agent \
    && chmod 700 /sandbox/.openclaw

# Auth profile: use NVIDIA provider, read API key from env at runtime
# Model config: route through inference.local (OpenShell gateway proxy)
RUN python3 -c "\
import json, os; \
agent_dir = os.path.expanduser('~/.openclaw/agents/main/agent'); \
os.makedirs(agent_dir, exist_ok=True); \
json.dump({'nvidia:manual': {'type': 'api_key', 'provider': 'nvidia', 'keyRef': {'source': 'env', 'id': 'NVIDIA_API_KEY'}, 'profileId': 'nvidia:manual'}}, open(os.path.join(agent_dir, 'auth-profiles.json'), 'w')); \
os.chmod(os.path.join(agent_dir, 'auth-profiles.json'), 0o600); \
json.dump({'default': 'nvidia/nemotron-3-super-120b-a12b', 'providers': {'nvidia': {'baseUrl': 'https://inference.local/v1', 'models': {'nemotron-3-super-120b-a12b': {'id': 'nvidia/nemotron-3-super-120b-a12b', 'label': 'Nemotron 3 Super 120B'}}}}}, open(os.path.join(agent_dir, 'models.json'), 'w'), indent=2)"

# Install NemoClaw plugin into OpenClaw
RUN openclaw doctor --fix > /dev/null 2>&1 || true \
    && openclaw plugins install /opt/nemoclaw > /dev/null 2>&1 || true

ENTRYPOINT ["/bin/bash"]
CMD []
