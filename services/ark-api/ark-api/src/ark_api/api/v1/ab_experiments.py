"""API routes for AB Experiment management."""

import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Path, Body
from typing import Optional
from ark_sdk.client import with_ark_client
from ark_sdk.models.query_v1alpha1 import QueryV1alpha1
from ark_sdk.models.query_v1alpha1_spec import QueryV1alpha1Spec
from ark_sdk.models.agent_v1alpha1 import AgentV1alpha1
from ark_sdk.models.agent_v1alpha1_spec import AgentV1alpha1Spec

from ...models.ab_experiments import (
    ABExperiment,
    ABExperimentStatus,
    ABExperimentModifications,
    CreateABExperimentRequest,
    UpdateABExperimentRequest,
    ApplyWinnerRequest,
)
from ...models.queries import QueryDetailResponse
from .queries import query_to_detail_response
from .exceptions import handle_k8s_errors

router = APIRouter(
    prefix="/namespaces/{namespace}/queries/{query_name}/ab-experiment",
    tags=["ab-experiments"]
)

VERSION = "v1alpha1"
AB_EXPERIMENT_ANNOTATION = "ab-experiment"
AB_EXPERIMENT_HISTORY_PREFIX = "ab-experiment-history-"


def parse_ab_experiment_annotation(annotations: dict) -> Optional[ABExperiment]:
    """Parse ab-experiment annotation from query metadata."""
    if not annotations or AB_EXPERIMENT_ANNOTATION not in annotations:
        return None

    try:
        data = json.loads(annotations[AB_EXPERIMENT_ANNOTATION])
        return ABExperiment(**data)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Failed to parse ab-experiment annotation: {e}")
        return None


def serialize_ab_experiment(experiment: ABExperiment) -> str:
    """Serialize ABExperiment to JSON string."""
    return json.dumps(experiment.model_dump(exclude_none=True), indent=2)


async def get_variant_query_name(base_name: str, experiment_id: str) -> str:
    """Generate variant query name."""
    return f"{base_name}-exp-{experiment_id}"


def parse_duration_to_seconds(duration_str: str) -> Optional[float]:
    """Parse duration string like '15.032819046s' to float seconds."""
    if not duration_str:
        return None
    try:
        return float(duration_str.rstrip('s'))
    except (ValueError, AttributeError):
        return None


def calculate_cost_from_query(query_dict: dict, model_annotations: dict) -> Optional[float]:
    """Calculate cost based on token usage and model pricing annotations."""
    token_usage = query_dict.get("status", {}).get("tokenUsage")
    if not token_usage:
        return None

    input_price_per_m = model_annotations.get("ark.mckinsey.com/pricing.input-per-million")
    output_price_per_m = model_annotations.get("ark.mckinsey.com/pricing.output-per-million")

    if not input_price_per_m or not output_price_per_m:
        return None

    try:
        prompt_tokens = int(token_usage.get("promptTokens", 0))
        completion_tokens = int(token_usage.get("completionTokens", 0))

        input_cost = (prompt_tokens / 1_000_000) * float(input_price_per_m)
        output_cost = (completion_tokens / 1_000_000) * float(output_price_per_m)

        return input_cost + output_cost
    except (ValueError, TypeError):
        return None


def filter_evals_by_query_ref(evals: list, query_name: str) -> list:
    """Filter evaluations by queryRef.name to get only evaluations targeting a specific query."""
    return [
        e for e in evals
        if e.get("spec", {}).get("config", {}).get("queryRef", {}).get("name") == query_name
    ]


@router.post("", response_model=ABExperiment)
@handle_k8s_errors(operation="create", resource_type="ab-experiment")
async def create_ab_experiment(
    namespace: str = Path(..., description="Namespace"),
    query_name: str = Path(..., description="Base query name"),
    request: CreateABExperimentRequest = Body(...)
) -> ABExperiment:
    """
    Create a new AB experiment for a query.
    Creates a variant query and stores experiment metadata in annotation.
    """
    async with with_ark_client(namespace, VERSION) as ark_client:
        base_query = await ark_client.queries.a_get(query_name)
        base_dict = base_query.to_dict()
        base_spec = base_dict["spec"]

        experiment_id = str(uuid.uuid4())[:8]
        variant_query_name = await get_variant_query_name(query_name, experiment_id)
        variant_agent_name = None

        variant_spec = dict(base_spec)

        if request.modifications.input:
            variant_spec["input"] = request.modifications.input

        if request.modifications.targetType == "agent" and request.modifications.targetName:
            baseline_target_name = base_spec.get("targets", [{}])[0].get("name") if base_spec.get("targets") else None

            if request.modifications.targetChanges and (request.modifications.targetChanges.model or request.modifications.targetChanges.instructions):
                target_agent_name = request.modifications.targetName
                variant_agent_name = f"{target_agent_name}-exp-{experiment_id}"

                base_agent = await ark_client.agents.a_get(target_agent_name)
                base_agent_dict = base_agent.to_dict()
                base_agent_spec = base_agent_dict["spec"]

                variant_agent_spec = dict(base_agent_spec)

                if request.modifications.targetChanges.model:
                    variant_agent_spec["modelRef"] = {"name": request.modifications.targetChanges.model}

                if request.modifications.targetChanges.instructions:
                    variant_agent_spec["prompt"] = request.modifications.targetChanges.instructions

                variant_agent_metadata = {
                    "name": variant_agent_name,
                    "namespace": namespace
                }

                variant_agent = AgentV1alpha1(
                    metadata=variant_agent_metadata,
                    spec=AgentV1alpha1Spec(**variant_agent_spec)
                )

                await ark_client.agents.a_create(variant_agent)

                variant_spec["targets"] = [{
                    "type": "agent",
                    "name": variant_agent_name
                }]
            else:
                variant_spec["targets"] = [{
                    "type": "agent",
                    "name": request.modifications.targetName
                }]

        variant_metadata = {
            "name": variant_query_name,
            "namespace": namespace,
            "labels": base_dict["metadata"].get("labels", {})
        }

        variant_query = QueryV1alpha1(
            metadata=variant_metadata,
            spec=QueryV1alpha1Spec(**variant_spec)
        )

        await ark_client.queries.a_create(variant_query)

        experiment = ABExperiment(
            id=experiment_id,
            status=ABExperimentStatus.PENDING,
            createdAt=datetime.utcnow().isoformat() + "Z",
            createdBy=request.createdBy,
            variantQuery=variant_query_name,
            variantAgent=variant_agent_name,
            modifications=request.modifications
        )

        base_metadata = base_dict.get("metadata", {})
        if "annotations" not in base_metadata:
            base_metadata["annotations"] = {}

        base_metadata["annotations"][AB_EXPERIMENT_ANNOTATION] = serialize_ab_experiment(experiment)

        patch = {
            "metadata": {
                "annotations": base_metadata["annotations"]
            }
        }

        await ark_client.queries.a_patch(query_name, patch)

        return experiment


@router.get("/{experiment_id}", response_model=ABExperiment)
@handle_k8s_errors(operation="get", resource_type="ab-experiment")
async def get_ab_experiment(
    namespace: str = Path(..., description="Namespace"),
    query_name: str = Path(..., description="Base query name"),
    experiment_id: str = Path(..., description="Experiment ID")
) -> ABExperiment:
    """Get AB experiment details and aggregate evaluation results."""
    async with with_ark_client(namespace, VERSION) as ark_client:
        base_query = await ark_client.queries.a_get(query_name)
        base_dict = base_query.to_dict()

        annotations = base_dict.get("metadata", {}).get("annotations", {})
        experiment = parse_ab_experiment_annotation(annotations)

        if not experiment or experiment.id != experiment_id:
            raise ValueError(f"Experiment {experiment_id} not found")

        baseline_evals_list = await ark_client.evaluations.a_list(
            label_selector=f"ark.mckinsey.com/query={query_name}"
        )
        all_baseline_evals = [e.to_dict() for e in baseline_evals_list] if baseline_evals_list else []
        baseline_evals = filter_evals_by_query_ref(all_baseline_evals, query_name)

        variant_evals_list = await ark_client.evaluations.a_list(
            label_selector=f"ark.mckinsey.com/query={experiment.variantQuery}"
        )
        all_variant_evals = [e.to_dict() for e in variant_evals_list] if variant_evals_list else []
        variant_evals = filter_evals_by_query_ref(all_variant_evals, experiment.variantQuery)

        baseline_completed = (
            len(baseline_evals) > 0 and
            all(e.get("status", {}).get("phase") == "done" for e in baseline_evals)
        )
        variant_completed = (
            len(variant_evals) > 0 and
            all(e.get("status", {}).get("phase") == "done" for e in variant_evals)
        )

        if baseline_completed and variant_completed:
            from ...models.ab_experiments import ABExperimentResults, ABExperimentVariantResults

            baseline_scores = {}
            baseline_overall = 0.0
            for e in baseline_evals:
                evaluator = e.get("spec", {}).get("evaluator", {}).get("name", "unknown")
                score = float(e.get("status", {}).get("score", 0))
                baseline_scores[evaluator] = score
                baseline_overall += score
            if baseline_evals:
                baseline_overall /= len(baseline_evals)

            variant_scores = {}
            variant_overall = 0.0
            for e in variant_evals:
                evaluator = e.get("spec", {}).get("evaluator", {}).get("name", "unknown")
                score = float(e.get("status", {}).get("score", 0))
                variant_scores[evaluator] = score
                variant_overall += score
            if variant_evals:
                variant_overall /= len(variant_evals)

            improvement = variant_overall - baseline_overall

            if abs(improvement) < 0.01:
                winner = "tie"
            elif improvement > 0:
                winner = "experiment"
            else:
                winner = "baseline"

            baseline_query = await ark_client.queries.a_get(query_name)
            baseline_query_dict = baseline_query.to_dict()
            baseline_latency = parse_duration_to_seconds(
                baseline_query_dict.get("status", {}).get("duration")
            )

            baseline_model_ref = baseline_query_dict.get("spec", {}).get("targets", [{}])[0].get("modelRef", {}).get("name")
            baseline_cost = None
            if baseline_model_ref:
                try:
                    baseline_model = await ark_client.models.a_get(baseline_model_ref)
                    baseline_model_annotations = baseline_model.to_dict().get("metadata", {}).get("annotations", {})
                    baseline_cost = calculate_cost_from_query(baseline_query_dict, baseline_model_annotations)
                except Exception:
                    pass

            variant_query = await ark_client.queries.a_get(experiment.variantQuery)
            variant_query_dict = variant_query.to_dict()
            variant_latency = parse_duration_to_seconds(
                variant_query_dict.get("status", {}).get("duration")
            )

            variant_model_ref = variant_query_dict.get("spec", {}).get("targets", [{}])[0].get("modelRef", {}).get("name")
            variant_cost = None
            if variant_model_ref:
                try:
                    variant_model = await ark_client.models.a_get(variant_model_ref)
                    variant_model_annotations = variant_model.to_dict().get("metadata", {}).get("annotations", {})
                    variant_cost = calculate_cost_from_query(variant_query_dict, variant_model_annotations)
                except Exception:
                    pass

            experiment.results = ABExperimentResults(
                baseline=ABExperimentVariantResults(
                    overallScore=baseline_overall,
                    criteria=baseline_scores,
                    cost=baseline_cost,
                    latency=baseline_latency
                ),
                experiment=ABExperimentVariantResults(
                    overallScore=variant_overall,
                    criteria=variant_scores,
                    cost=variant_cost,
                    latency=variant_latency
                ),
                improvement=improvement,
                winner=winner
            )
            experiment.status = ABExperimentStatus.COMPLETED

            patch = {
                "metadata": {
                    "annotations": {
                        AB_EXPERIMENT_ANNOTATION: serialize_ab_experiment(experiment)
                    }
                }
            }
            await ark_client.queries.a_patch(query_name, patch)

        elif experiment.status == ABExperimentStatus.PENDING:
            experiment.status = ABExperimentStatus.RUNNING

            patch = {
                "metadata": {
                    "annotations": {
                        AB_EXPERIMENT_ANNOTATION: serialize_ab_experiment(experiment)
                    }
                }
            }
            await ark_client.queries.a_patch(query_name, patch)

        return experiment


@router.patch("/{experiment_id}", response_model=ABExperiment)
@handle_k8s_errors(operation="update", resource_type="ab-experiment")
async def update_ab_experiment(
    namespace: str = Path(..., description="Namespace"),
    query_name: str = Path(..., description="Base query name"),
    experiment_id: str = Path(..., description="Experiment ID"),
    request: UpdateABExperimentRequest = Body(...)
) -> ABExperiment:
    """Update AB experiment status and results."""
    async with with_ark_client(namespace, VERSION) as ark_client:
        base_query = await ark_client.queries.a_get(query_name)
        base_dict = base_query.to_dict()

        annotations = base_dict.get("metadata", {}).get("annotations", {})
        experiment = parse_ab_experiment_annotation(annotations)

        if not experiment or experiment.id != experiment_id:
            raise ValueError(f"Experiment {experiment_id} not found")

        if request.status:
            experiment.status = request.status

        if request.results:
            experiment.results = request.results

        patch = {
            "metadata": {
                "annotations": {
                    AB_EXPERIMENT_ANNOTATION: serialize_ab_experiment(experiment)
                }
            }
        }

        await ark_client.queries.a_patch(query_name, patch)

        return experiment


@router.post("/{experiment_id}/apply", response_model=QueryDetailResponse)
@handle_k8s_errors(operation="update", resource_type="ab-experiment")
async def apply_ab_experiment_winner(
    namespace: str = Path(..., description="Namespace"),
    query_name: str = Path(..., description="Base query name"),
    experiment_id: str = Path(..., description="Experiment ID"),
    request: ApplyWinnerRequest = Body(...)
) -> QueryDetailResponse:
    """Apply winning variant to baseline query."""
    async with with_ark_client(namespace, VERSION) as ark_client:
        base_query = await ark_client.queries.a_get(query_name)
        base_dict = base_query.to_dict()

        annotations = base_dict.get("metadata", {}).get("annotations", {})
        experiment = parse_ab_experiment_annotation(annotations)

        if not experiment or experiment.id != experiment_id:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.status = ABExperimentStatus.APPLIED
        experiment.appliedAt = datetime.utcnow().isoformat() + "Z"
        experiment.appliedWinner = request.winner

        history_key = f"{AB_EXPERIMENT_HISTORY_PREFIX}{experiment.id}"
        annotations[history_key] = serialize_ab_experiment(experiment)

        del annotations[AB_EXPERIMENT_ANNOTATION]

        await ark_client.queries.a_patch(query_name, {
            "metadata": {"annotations": annotations}
        })

        return query_to_detail_response(base_dict)


@router.get("/history", response_model=list[ABExperiment])
@handle_k8s_errors(operation="get", resource_type="ab-experiment-history")
async def get_experiment_history(
    namespace: str = Path(..., description="Namespace"),
    query_name: str = Path(..., description="Base query name")
) -> list[ABExperiment]:
    """Get AB experiment history for a query."""
    async with with_ark_client(namespace, VERSION) as ark_client:
        base_query = await ark_client.queries.a_get(query_name)
        base_dict = base_query.to_dict()

        annotations = base_dict.get("metadata", {}).get("annotations", {})
        history = []

        for key, value in annotations.items():
            if key.startswith(AB_EXPERIMENT_HISTORY_PREFIX):
                try:
                    experiment_data = json.loads(value)
                    experiment = ABExperiment(**experiment_data)
                    history.append(experiment)
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    print(f"Failed to parse history annotation {key}: {e}")
                    continue

        history.sort(key=lambda x: x.createdAt, reverse=True)
        return history


@router.delete("/{experiment_id}", status_code=204)
@handle_k8s_errors(operation="delete", resource_type="ab-experiment")
async def delete_ab_experiment(
    namespace: str = Path(..., description="Namespace"),
    query_name: str = Path(..., description="Base query name"),
    experiment_id: str = Path(..., description="Experiment ID")
) -> None:
    """Delete AB experiment and its variant query."""
    async with with_ark_client(namespace, VERSION) as ark_client:
        base_query = await ark_client.queries.a_get(query_name)
        base_dict = base_query.to_dict()

        annotations = base_dict.get("metadata", {}).get("annotations", {})
        experiment = parse_ab_experiment_annotation(annotations)

        if not experiment or experiment.id != experiment_id:
            raise ValueError(f"Experiment {experiment_id} not found")

        try:
            await ark_client.queries.a_delete(experiment.variantQuery)
        except Exception as e:
            print(f"Failed to delete variant query {experiment.variantQuery}: {e}")

        if experiment.variantAgent:
            try:
                await ark_client.agents.a_delete(experiment.variantAgent)
            except Exception as e:
                print(f"Failed to delete variant agent {experiment.variantAgent}: {e}")

        del annotations[AB_EXPERIMENT_ANNOTATION]

        patch = {
            "metadata": {
                "annotations": annotations
            }
        }

        await ark_client.queries.a_patch(query_name, patch)
