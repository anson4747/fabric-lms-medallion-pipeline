# CI/CD

## Branching and workspaces

| Stage | Git | Fabric workspace |
|---|---|---|
| Feature work | `feature/*` branch | Personal feature workspace connected to the branch |
| Integration | `main`, protected by a branch policy (pull request required) | Dev workspace (`fabric_DEV`) synced to `main` |
| Release | n/a | Prod workspace, populated by a Fabric deployment pipeline |

## Continuous integration

1. Branch from `main` in Azure DevOps and connect a feature workspace to the branch (Fabric Git integration supports branching out to a new workspace).
2. Develop and run the notebooks and pipelines in the feature workspace, then **Commit** from the Source control pane. Fabric serialises each item: notebooks as `notebook-content.py`, pipelines as `pipeline-content.json`, the semantic model as TMDL and the report as PBIR.
3. Open a pull request into `main`. The branch policy blocks direct pushes.
4. After merge, the Dev workspace shows incoming changes and is updated from Git.

## Continuous deployment

1. A Fabric **deployment pipeline** has two stages, Development and Production.
2. Deploying compares item definitions and promotes changed items from Dev to Prod.
3. **Deployment rules** on the Prod stage change data sources and default Lakehouses so Prod notebooks read and write Prod Lakehouses.
4. The orchestrator exposes `workspace_name`, `storage_account` and `storage_container` as pipeline parameters, so the same pipeline definition runs against either environment's storage and OneLake paths.

## Checks in this GitHub repo

`.github/workflows/ci.yml` runs on every push and pull request:

| Job | What it checks |
|---|---|
| Validate Fabric items | every item has a `.platform` file, all JSON parses, all notebooks are valid Python, pipelines only reference items that exist, and no pipeline passes a hard-coded workspace name |
| Lint and unit test | `ruff`, the pytest suite for the transformation logic, and a full local run of the pipeline on the sample data |

The workspace check in the first job would have caught the hard-coded workspace bug described in [engineering-review.md](engineering-review.md) before it reached the workspace.

## Git integration notes

* Lakehouse data is never in Git. Only the item definition (`.platform`, `lakehouse.metadata.json`, shortcuts) is versioned. Data is recreated by running the pipeline.
* Connections are referenced by ID in `pipeline-content.json`. These are not credentials, but they are environment specific and must be rebound or handled by deployment rules.
* The report references the semantic model by relative path (`../LMS_model.SemanticModel`), so both must be in the same Git folder.
