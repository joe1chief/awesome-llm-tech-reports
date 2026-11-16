"""Offline contract checks for the shared Pages workflow."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_pages_artifact_is_attempt_scoped_and_consistent():
    workflow = (ROOT / '.github/workflows/deploy.yml').read_text()
    upload = re.search(r'          name: (github-pages-.+)', workflow).group(1)
    deploy = re.search(r'          artifact_name: (.+)', workflow).group(1)
    wait = re.search(r'          artifact-name: (.+)', workflow).group(1)
    assert upload == deploy == wait
    assert '${{ github.run_id }}' in upload
    assert '${{ github.run_attempt }}' in upload
    names = {
        upload.replace('${{ github.run_id }}', run).replace('${{ github.run_attempt }}', attempt)
        for run, attempt in [('46', '1'), ('46', '2'), ('47', '1')]
    }
    assert len(names) == 3


def test_refresh_reuses_deploy_without_artifact_permission_expansion():
    refresh = (ROOT / '.github/workflows/refresh-reports.yml').read_text()
    deploy = (ROOT / '.github/workflows/deploy.yml').read_text()
    assert 'uses: ./.github/workflows/deploy.yml' in refresh
    assert 'workflow_call:' in deploy and 'workflow_dispatch:' in deploy
    assert 'actions: read' not in refresh + deploy
    assert 'actions: write' not in refresh + deploy
    assert 'ref: ${{ needs.refresh.outputs.published_ref }}' in refresh


def test_visibility_gate_precedes_the_only_deployment():
    deploy = (ROOT / '.github/workflows/deploy.yml').read_text()
    assert deploy.count('uses: actions/deploy-pages@') == 1
    upload = deploy.index('uses: actions/upload-pages-artifact@')
    wait = deploy.index('uses: ./.github/actions/wait-pages-artifact')
    assert upload < wait < deploy.index('uses: actions/deploy-pages@')
    assert 'artifact-id: ${{ steps.upload.outputs.artifact_id }}' in deploy
    assert 'timeout-minutes: 2' in deploy
    assert 'continue-on-error:' not in deploy
    action = (ROOT / '.github/actions/wait-pages-artifact/action.yml').read_text()
    assert 'using: node24' in action


def test_pull_request_exercises_real_upload_and_visibility_without_deploy():
    refresh = (ROOT / '.github/workflows/refresh-reports.yml').read_text()
    smoke = refresh.split('  pages-artifact-check:', 1)[1].split('  refresh:', 1)[0]
    assert "if: github.event_name == 'pull_request'" in smoke
    assert 'actions/upload-pages-artifact@v4' in smoke
    assert './.github/actions/wait-pages-artifact' in smoke
    assert 'actions/deploy-pages' not in smoke
    assert 'artifact-id: ${{ steps.upload.outputs.artifact_id }}' in smoke
