class ReadinessError extends Error {}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// Only retry a missing artifact, never a deployment or an ambiguous/API failure.
async function waitForArtifact(client, name, id, { attempts = 12, interval = 5000, pause = sleep, log = () => {} } = {}) {
  if (!name || !/^\d+$/.test(id)) throw new ReadinessError('Expected an artifact name and numeric upload ID');
  for (let attempt = 1; attempt <= attempts; attempt++) {
    const { artifacts } = await client.listArtifacts();
    const matches = artifacts.filter(artifact => artifact.name === name);
    if (matches.length > 1) throw new ReadinessError('Multiple matching Pages artifacts');
    if (matches.length === 1) {
      if (String(matches[0].id) !== id) throw new ReadinessError('Pages artifact ID differs from upload output');
      return matches[0];
    }
    log(`Pages artifact not visible (${attempt}/${attempts})`);
    if (attempt < attempts) await pause(interval);
  }
  throw new ReadinessError('Uploaded Pages artifact did not become visible within the retry budget');
}
module.exports = { waitForArtifact, ReadinessError };
