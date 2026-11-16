const core = require('@actions/core');
const { DefaultArtifactClient } = require('@actions/artifact');
const { waitForArtifact, ReadinessError } = require('./wait.cjs');

waitForArtifact(
  new DefaultArtifactClient(),
  core.getInput('artifact-name', { required: true }),
  core.getInput('artifact-id', { required: true }),
  { log: core.info }
).catch(error => {
  // Do not log SDK errors that could include runtime credentials or request URLs.
  core.setFailed(error instanceof ReadinessError
    ? error.message
    : 'Artifact service query failed; deployment was not started.');
});
