# GitHub Workflows

This directory contains example GitHub Actions workflows for reference purposes.

## Active Workflows

The **actual active workflows** for this repository are located in the root-level `.github/workflows/` directory:

- **PR Review Workflow**: [`.github/workflows/pr_review_ai.yml`](../../../.github/workflows/pr_review_ai.yml) - Triggers ARK PR review on pull requests
- **Branch Validation Workflow**: [`.github/workflows/validate_branch_name_jira.yml`](../../../.github/workflows/validate_branch_name_jira.yml) - Validates branch naming convention

## Example Files

The files in this directory are copies provided as examples for implementing similar workflows in your own repositories:

- `pr_review_ai.yml.example` - Example PR review workflow configuration

## Usage

To use these workflows in your repository:

1. Copy the example workflow to your repository's `.github/workflows/` directory
2. Remove the `.example` extension
3. Update the configuration values:
   - Repository secrets (GitHub token, Jira credentials)
   - ARK service endpoint
   - Model configurations
4. Customize agent prompts and team configuration as needed

## Configuration

See the main [PR Review documentation](../../../../docs/content/user-guide/samples/pr-review-team/index.mdx) for complete setup instructions including:

- Service deployment
- Secret management
- Agent customization
- Branch naming requirements

## Repository-Wide Standards

This ARK repository enforces:

- **Branch Naming**: All branches must follow `PROJECT-XXX-description` or `PROJECT-000-description` pattern
- **Pre-push Validation**: Husky hook validates branch names locally (see [`.husky/pre-push`](../../../.husky/pre-push))
- **CI Validation**: GitHub Actions adds warning labels to non-compliant PRs
- **Commit Format**: Conventional commit format required (see [`CONTRIBUTING.md`](../../../CONTRIBUTING.md))

These standards serve as both active enforcement for this repository and examples for implementing similar practices in other projects.

