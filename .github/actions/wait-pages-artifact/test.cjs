const { test } = require('node:test');
const assert = require('node:assert/strict');
const { waitForArtifact } = require('./wait.cjs');
const artifact = { name: 'pages-46-2', id: 123, size: 500 };
const options = { attempts: 3, interval: 1, pause: async () => {} };

test('immediate visibility returns the exact upload', async () => {
  assert.equal(await waitForArtifact({listArtifacts: async () => ({artifacts: [artifact]})}, artifact.name, '123', options), artifact);
});
test('polls only absence and succeeds after eventual visibility', async () => {
  let calls = 0, pauses = 0;
  const result = await waitForArtifact({listArtifacts: async () => ({artifacts: ++calls < 3 ? [] : [artifact]})}, artifact.name, '123', {...options, pause: async () => pauses++});
  assert.equal(result, artifact); assert.equal(calls, 3); assert.equal(pauses, 2);
});
test('missing artifact fails after a bounded number of calls', async () => {
  let calls = 0;
  await assert.rejects(waitForArtifact({listArtifacts: async () => {calls++; return {artifacts: []};}}, artifact.name, '123', options), /retry budget/);
  assert.equal(calls, 3);
});
for (const [label, artifacts, message] of [
  ['duplicate', [artifact, artifact], /Multiple/],
  ['wrong ID', [{...artifact,id:124}], /ID differs/],
]) test(label + ' fails immediately', async () => {
  let calls = 0;
  await assert.rejects(waitForArtifact({listArtifacts: async () => { calls++; return {artifacts};}}, artifact.name, '123', options), message);
  assert.equal(calls,1);
});
test('API errors are not retried', async () => {
  let calls = 0;
  await assert.rejects(waitForArtifact({listArtifacts: async () => {calls++; throw new Error('API unavailable');}},artifact.name,'123',options), /API unavailable/);
  assert.equal(calls,1);
});
test('other attempts are ignored', async () => {
  await assert.rejects(waitForArtifact({listArtifacts: async () => ({artifacts:[{...artifact,name:'pages-46-1'}]})},artifact.name,'123',options), /retry budget/);
});
test('missing upload ID fails without reading the service', async () => {
  await assert.rejects(waitForArtifact({listArtifacts: async () => {throw new Error('must not call');}},artifact.name,'',options), /numeric upload ID/);
});

test('unknown size is accepted like deploy-pages', async () => {
  const item = {name:artifact.name,id:123};
  assert.equal(await waitForArtifact({listArtifacts: async () => ({artifacts:[item]})}, artifact.name,'123',options), item);
});
