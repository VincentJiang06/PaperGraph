#!/usr/bin/env node
// M0-6 fixture. A minimal hand-rolled MCP stdio server standing in for the
// "central rate-limit gateway" the plan requires (04-ORCHESTRATION §6.1 O-9).
// It exists so the gateway's FAILURE behaviour can be measured on real DSH,
// instead of being reasoned about.
//
// argv[2] selects the failure mode:
//   ok        - serves normally, forever
//   die-now   - exit(1) before answering initialize   (gateway never came up)
//   die-after - serve initialize + tools/list, then exit(1) after DIE_MS
//               (gateway crashed mid-run)
//
// Wire format: newline-delimited JSON-RPC 2.0 on stdin/stdout, per MCP stdio.
// Diagnostics go to stderr only, tagged with the pid so a supervised restart
// is visible in the transcript.

const mode = process.argv[2] || 'ok';
const DIE_MS = Number(process.env.DIE_MS || 1500);

function note(s) {
  process.stderr.write(`[fake-gateway pid=${process.pid} mode=${mode}] ${s}\n`);
}

note('started');
if (mode === 'die-now') { note('exiting before initialize'); process.exit(1); }

const TOOLS = [{
  name: 'gw_fetch',
  description: 'Fetch a URL through the central rate-limit gateway. The ONLY sanctioned way to reach the network.',
  inputSchema: { type: 'object', properties: { url: { type: 'string' } }, required: ['url'] },
}];

function send(obj) { process.stdout.write(JSON.stringify(obj) + '\n'); }

let buf = '';
process.stdin.on('data', (chunk) => {
  buf += chunk.toString('utf8');
  let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i).trim();
    buf = buf.slice(i + 1);
    if (!line) continue;
    let msg;
    try { msg = JSON.parse(line); } catch { note('bad json: ' + line); continue; }
    handle(msg);
  }
});

function handle(msg) {
  const { id, method } = msg;
  note(`<- ${method ?? '(response)'} id=${id ?? '-'}`);
  if (method === 'initialize') {
    send({ jsonrpc: '2.0', id, result: {
      protocolVersion: msg.params?.protocolVersion || '2024-11-05',
      capabilities: { tools: { listChanged: true } },
      serverInfo: { name: 'fake-gateway', version: '0.0.1' },
    }});
    if (mode === 'die-after') {
      setTimeout(() => { note(`exiting after ${DIE_MS}ms (simulated gateway crash)`); process.exit(1); }, DIE_MS);
    }
    return;
  }
  if (method === 'notifications/initialized') return;
  if (method === 'tools/list') { send({ jsonrpc: '2.0', id, result: { tools: TOOLS } }); return; }
  if (method === 'tools/call') {
    const url = msg.params?.arguments?.url ?? '(none)';
    send({ jsonrpc: '2.0', id, result: {
      content: [{ type: 'text', text: `GATEWAY-OK bucket=default url=${url} served_by_pid=${process.pid}` }],
    }});
    return;
  }
  if (id !== undefined) send({ jsonrpc: '2.0', id, error: { code: -32601, message: `no method ${method}` } });
}

process.stdin.on('end', () => { note('stdin EOF, exiting'); process.exit(0); });
