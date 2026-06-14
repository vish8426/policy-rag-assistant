"""Run the evaluation:
    python -m eval              # single run at config.TOP_K
    python -m eval --ablation   # compare k=4 vs k=6
"""
import json
import sys

from .evaluate import run_ablation, run_eval

if __name__ == "__main__":
    if "--ablation" in sys.argv:
        results = run_ablation(k_values=(4, 6))
        print(json.dumps(results, indent=2))
        print("\nWrote eval/results/{eval_results.json, eval_summary.md, ablation.json, ablation.md}")
    else:
        summary, _ = run_eval()
        print(json.dumps(summary, indent=2))
        print("\nWrote eval/results/{eval_results.json, eval_summary.md}")
