import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();

test('repository adopts only the required build123d MCP workflow', () => {
  const workflow = fs.readFileSync(path.join(root, 'mechanical/docs/BUILD123D_MCP_WORKFLOW_RU.md'), 'utf8');
  const agents = fs.readFileSync(path.join(root, 'AGENTS.md'), 'utf8');
  for (const skill of ['modeling', 'drawing', 'repair']) assert.match(workflow, new RegExp(`skill="${skill}"`));
  assert.match(workflow, /build123d-mcp@latest/);
  assert.match(workflow, /#petg-6/);
  assert.match(workflow, /#petg-10/);
  assert.match(workflow, /#petg-5/);
  assert.match(agents, /BUILD123D_MCP_WORKFLOW_RU\.md/);
  assert.doesNotMatch(agents, /codex plugin add cad@text-to-cad/);
});
