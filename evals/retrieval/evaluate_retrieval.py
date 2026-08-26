import json
import time
from pathlib import Path

from policy_mcp.retrieval.simple_retriever import (
    search_policy,
)
from policy_mcp.retrieval.hyde_retriever import (
    search_policy_hyde,
)
from policy_mcp.retrieval.multi_query_retriever import (
    search_policy_multi_query,
)
from policy_mcp.retrieval.adaptive_retriever import (
    search_policy_adaptive,
)


DATASET_PATH = Path(
    "evals/datasets/retrieval_cases.json"
)


def load_cases() -> list[dict]:
    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def first_relevant_rank(
    retrieved_chunk_ids: list[str],
    expected_chunk_ids: list[str],
) -> int | None:
    """
    Return the 1-based rank of the first relevant chunk.
    """

    expected = set(expected_chunk_ids)

    for index, chunk_id in enumerate(
        retrieved_chunk_ids,
        start=1,
    ):
        if chunk_id in expected:
            return index

    return None


def calculate_metrics(
    retrieved_chunk_ids: list[str],
    expected_chunk_ids: list[str],
) -> dict:

    rank = first_relevant_rank(
        retrieved_chunk_ids,
        expected_chunk_ids,
    )

    hit_at_1 = (
        1
        if rank is not None and rank <= 1
        else 0
    )

    hit_at_3 = (
        1
        if rank is not None and rank <= 3
        else 0
    )

    reciprocal_rank = (
        1 / rank
        if rank is not None
        else 0.0
    )

    return {
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "reciprocal_rank": reciprocal_rank,
        "first_relevant_rank": rank,
    }


def run_simple(case: dict) -> list[dict]:
    return search_policy(
        query=case["query"],
        country=case["country"],
        top_k=3,
    )


def run_hyde(case: dict) -> list[dict]:
    result = search_policy_hyde(
        query=case["query"],
        country=case["country"],
        top_k=3,
    )

    return result["results"]


def run_multi_query(case: dict) -> list[dict]:
    result = search_policy_multi_query(
        query=case["query"],
        country=case["country"],
        top_k_per_query=3,
        final_top_k=3,
    )

    return result["results"]

def run_adaptive(case: dict) -> dict:
    return search_policy_adaptive(
        query=case["query"],
        country=case["country"],
        top_k=3,
    )

STRATEGIES = {
    "simple": run_simple,
    "hyde": run_hyde,
    "multi_query": run_multi_query,
    "adaptive": run_adaptive,
}


def evaluate_strategy(
    strategy_name: str,
    strategy_function,
    cases: list[dict],
) -> dict:

    results = []

    total_hit_at_1 = 0
    total_hit_at_3 = 0
    total_rr = 0.0
    total_latency = 0.0

    for case in cases:

        start = time.perf_counter()

        raw_result = strategy_function(case)

        selected_strategy = strategy_name

        if isinstance(raw_result, dict) and "results" in raw_result:
            selected_strategy = raw_result.get(
                "strategy",
                strategy_name,
            )
            retrieved = raw_result["results"]
        else:
            retrieved = raw_result

        latency = time.perf_counter() - start

        retrieved_chunk_ids = [
            item["chunk_id"]
            for item in retrieved
        ]

        metrics = calculate_metrics(
            retrieved_chunk_ids,
            case["expected_chunk_ids"],
        )

        total_hit_at_1 += metrics["hit_at_1"]
        total_hit_at_3 += metrics["hit_at_3"]
        total_rr += metrics["reciprocal_rank"]
        total_latency += latency

        results.append(
            {
                "case_id": case["id"],
                "query": case["query"],
                "expected_chunk_ids": (
                    case["expected_chunk_ids"]
                ),
                "retrieved_chunk_ids": (
                    retrieved_chunk_ids
                ),
                "selected_strategy": selected_strategy,
                "first_relevant_rank": (
                    metrics["first_relevant_rank"]
                ),
                "hit_at_1": metrics["hit_at_1"],
                "hit_at_3": metrics["hit_at_3"],
                "reciprocal_rank": (
                    metrics["reciprocal_rank"]
                ),
                "latency_seconds": latency,
            }
        )

        if strategy_name == "adaptive":
            print(
                f"{strategy_name:12} "
                f"{case['id']:30} "
                f"selected={selected_strategy:12} "
                f"rank={metrics['first_relevant_rank']} "
                f"latency={latency:.2f}s"
            )
        else:
            print(
                f"{strategy_name:12} "
                f"{case['id']:30} "
                f"rank={metrics['first_relevant_rank']} "
                f"latency={latency:.2f}s"
            )

    count = len(cases)

    return {
        "strategy": strategy_name,
        "summary": {
            "case_count": count,
            "hit_at_1": total_hit_at_1 / count,
            "hit_at_3": total_hit_at_3 / count,
            "mrr": total_rr / count,
            "average_latency_seconds": (
                total_latency / count
            ),
        },
        "cases": results,
    }

def analyze_adaptive_efficiency(
    evaluation_results: list[dict],
) -> dict:

    simple_result = next(
        result
        for result in evaluation_results
        if result["strategy"] == "simple"
    )

    adaptive_result = next(
        result
        for result in evaluation_results
        if result["strategy"] == "adaptive"
    )

    simple_by_case = {
        item["case_id"]: item
        for item in simple_result["cases"]
    }

    adaptive_by_case = {
        item["case_id"]: item
        for item in adaptive_result["cases"]
    }

    total_cases = len(simple_by_case)

    escalated = 0
    useful_escalations = 0
    unnecessary_escalations = 0
    failed_escalations = 0

    details = []

    for case_id, simple_case in simple_by_case.items():

        adaptive_case = adaptive_by_case[case_id]

        selected_strategy = adaptive_case["selected_strategy"]

        simple_hit = simple_case["hit_at_3"] == 1
        adaptive_hit = adaptive_case["hit_at_3"] == 1

        escalation = selected_strategy != "simple"

        classification = "no_escalation"

        if escalation:
            escalated += 1

            if not simple_hit and adaptive_hit:
                useful_escalations += 1
                classification = "useful_escalation"

            elif simple_hit and adaptive_hit:
                unnecessary_escalations += 1
                classification = "unnecessary_escalation"

            elif not simple_hit and not adaptive_hit:
                failed_escalations += 1
                classification = "failed_escalation"

            else:
                classification = "regression"

        details.append(
            {
                "case_id": case_id,
                "selected_strategy": selected_strategy,
                "simple_hit_at_3": simple_case["hit_at_3"],
                "adaptive_hit_at_3": adaptive_case["hit_at_3"],
                "classification": classification,
            }
        )

    return {
        "total_cases": total_cases,
        "escalated_cases": escalated,
        "escalation_rate": (
            escalated / total_cases
            if total_cases
            else 0.0
        ),
        "useful_escalations": useful_escalations,
        "unnecessary_escalations": unnecessary_escalations,
        "failed_escalations": failed_escalations,
        "details": details,
    }

def print_adaptive_efficiency(
    efficiency: dict,
) -> None:

    print("\n")
    print("=" * 80)
    print("ADAPTIVE ROUTER EFFICIENCY")
    print("=" * 80)

    print(
        f"Total cases: "
        f"{efficiency['total_cases']}"
    )

    print(
        f"Escalated cases: "
        f"{efficiency['escalated_cases']}"
    )

    print(
        f"Escalation rate: "
        f"{efficiency['escalation_rate']:.3f}"
    )

    print(
        f"Useful escalations: "
        f"{efficiency['useful_escalations']}"
    )

    print(
        f"Unnecessary escalations: "
        f"{efficiency['unnecessary_escalations']}"
    )

    print(
        f"Failed escalations: "
        f"{efficiency['failed_escalations']}"
    )

    print("\nPer-case routing:")

    for item in efficiency["details"]:
        print(
            f"{item['case_id']:32} "
            f"{item['selected_strategy']:12} "
            f"{item['classification']}"
        )

def print_summary(
    evaluation_results: list[dict],
) -> None:

    print("\n")
    print("=" * 80)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("=" * 80)

    print(
        f"{'Strategy':15}"
        f"{'Hit@1':>10}"
        f"{'Hit@3':>10}"
        f"{'MRR':>10}"
        f"{'Avg Latency':>15}"
    )

    print("-" * 60)

    for result in evaluation_results:
        summary = result["summary"]

        print(
            f"{result['strategy']:15}"
            f"{summary['hit_at_1']:>10.3f}"
            f"{summary['hit_at_3']:>10.3f}"
            f"{summary['mrr']:>10.3f}"
            f"{summary['average_latency_seconds']:>14.2f}s"
        )


def save_results(
    evaluation_results: list[dict],
    adaptive_efficiency: dict,
) -> None:

    output_path = Path(
        "evals/results/retrieval_results.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "strategies": evaluation_results,
        "adaptive_efficiency": adaptive_efficiency,
    }

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
        )

    print(
        f"\nResults saved to: {output_path}"
    )


def main():

    cases = load_cases()

    evaluation_results = []

    for strategy_name, strategy_function in (
        STRATEGIES.items()
    ):

        print("\n" + "=" * 80)
        print(
            f"Evaluating strategy: {strategy_name}"
        )
        print("=" * 80)

        result = evaluate_strategy(
            strategy_name=strategy_name,
            strategy_function=strategy_function,
            cases=cases,
        )

        evaluation_results.append(result)

    print_summary(evaluation_results)

    efficiency = analyze_adaptive_efficiency(
        evaluation_results
    )

    print_adaptive_efficiency(
        efficiency
    )    

    save_results(
        evaluation_results,
        efficiency,
    )


if __name__ == "__main__":
    main()