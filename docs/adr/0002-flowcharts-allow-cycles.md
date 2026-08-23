# `Flowchart` permits cycles

A `Flowchart` is not required to be acyclic. Process descriptions commonly include retry/rework loops ("if rejected, go back to step 2"), and rejecting these as invalid would reject realistic, common input. The validation invariant is reachability from `StartNode` (every node reachable from start, `EndNode` reachable from start), not "no cycles." A future reader implementing graph algorithms (topological sort, single-pass rendering) against `Flowchart` should not assume acyclicity — it was deliberately not enforced, despite "flowchart" suggesting a DAG.
