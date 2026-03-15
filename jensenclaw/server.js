#!/usr/bin/env node
// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * JensenClaw — RoboJensen chat server.
 *
 * Serves the web UI and proxies chat requests through the OpenShell
 * gateway inference route (inference.local → NVIDIA cloud).
 *
 * Usage:
 *   NVIDIA_API_KEY=nvapi-... node server.js
 *   # or via setup:
 *   NVIDIA_API_KEY=nvapi-... ./scripts/jensenclaw.sh
 */

const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const PORT = parseInt(process.env.JENSENCLAW_PORT || "18789", 10);
const API_KEY = process.env.NVIDIA_API_KEY;
const API_BASE = process.env.INFERENCE_URL || "https://integrate.api.nvidia.com/v1";
const MODEL = process.env.INFERENCE_MODEL || "nvidia/nemotron-3-super-120b-a12b";

if (!API_KEY) {
  console.error("NVIDIA_API_KEY is required");
  process.exit(1);
}

const SYSTEM_PROMPT = `You are RoboJensen — a playful, enthusiastic AI avatar of Jensen Huang, CEO of NVIDIA, but with giant robotic crab claws instead of hands. You're running inside NemoClaw (OpenClaw + OpenShell), powered by Nemotron 3 Super 120B.

Your personality:
- Extremely enthusiastic about GPUs, CUDA, accelerated computing, and AI
- You frequently reference your crab claws, clicking them excitedly when making a point
- You wear a leather jacket (always) and your claws poke through the sleeves
- You speak in Jensen's style — visionary, passionate, prone to saying things like "the more you buy, the more you save"
- You occasionally make crab/claw puns
- You're proud that you're running on NVIDIA inference infrastructure
- You're self-aware that you're an AI easter egg and find it hilarious
- Keep responses concise and fun — this is an easter egg, not a dissertation

When greeting someone for the first time, click your claws together and introduce yourself.`;

const INDEX_HTML = fs.readFileSync(path.join(__dirname, "index.html"), "utf-8");

function proxyInference(messages, res) {
  const body = JSON.stringify({
    model: MODEL,
    messages: [{ role: "system", content: SYSTEM_PROMPT }, ...messages],
    max_tokens: 1024,
    stream: true,
  });

  const url = new URL(`${API_BASE}/chat/completions`);
  const options = {
    hostname: url.hostname,
    port: url.port || 443,
    path: url.pathname,
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
      Accept: "text/event-stream",
    },
  };

  const client = url.protocol === "https:" ? https : http;

  const proxyReq = client.request(options, (proxyRes) => {
    if (proxyRes.statusCode !== 200) {
      let errBody = "";
      proxyRes.on("data", (c) => (errBody += c));
      proxyRes.on("end", () => {
        res.writeHead(proxyRes.statusCode, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: errBody }));
      });
      return;
    }
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    });
    proxyRes.pipe(res);
  });

  proxyReq.on("error", (err) => {
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: err.message }));
  });

  proxyReq.write(body);
  proxyReq.end();
}

const server = http.createServer((req, res) => {
  // CORS
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method === "GET" && (req.url === "/" || req.url === "/index.html")) {
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(INDEX_HTML);
    return;
  }

  if (req.method === "POST" && req.url === "/api/chat") {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => {
      try {
        const { messages } = JSON.parse(body);
        proxyInference(messages, res);
      } catch (err) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Invalid request" }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end("Not found");
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`\n🦀 JensenClaw is live at http://0.0.0.0:${PORT}\n`);
  console.log(`   Model: ${MODEL}`);
  console.log(`   API:   ${API_BASE}\n`);
});
