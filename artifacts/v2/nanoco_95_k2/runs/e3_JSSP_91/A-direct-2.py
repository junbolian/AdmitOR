import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    p = {
        (0, 1): params["p_0_1"], (0, 0): params["p_0_0"], (0, 2): params["p_0_2"],
        (1, 1): params["p_1_1"], (1, 0): params["p_1_0"], (1, 2): params["p_1_2"],
        (2, 1): params["p_2_1"], (2, 0): params["p_2_0"], (2, 2): params["p_2_2"],
    }

    lots = [0, 1, 2]
    steps = [0, 1, 2]  # step index; tool sequence is [1, 0, 2]

    # structure: each lot has 3 operations; op k of lot l runs on tool TOOL_SEQ[k]
    TOOL_SEQ = [1, 0, 2]

    # Define operations as (lot, step)
    ops = [(l, k) for l in lots for k in steps]

    # Big-M for disjunctive constraints
    total_time = sum(p[(l, k)] for l in lots for k in steps)

    model = pyo.ConcreteModel()

    model.LOTS = pyo.Set(initialize=lots)
    model.STEPS = pyo.Set(initialize=steps)
    model.OPS = pyo.Set(initialize=ops, dimen=2)

    # Variables: start times for each operation
    model.start = pyo.Var(model.OPS, domain=pyo.NonNegativeReals)

    # Makespan variable
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    # Precedence: step k+1 of lot l starts after step k finishes
    def precedence_rule(model, l, k):
        return model.start[l, k + 1] >= model.start[l, k] + p[(l, k)]

    model.precedence = pyo.Constraint(
        [(l, k) for l in lots for k in steps[:-1]], rule=precedence_rule
    )

    # Makespan: Cmax >= finish of last op of each lot
    def cmax_rule(model, l):
        return model.Cmax >= model.start[l, steps[-1]] + p[(l, steps[-1])]

    model.cmax_def = pyo.Constraint(model.LOTS, rule=cmax_rule)

    # Disjunctive constraints for tool usage (mutual exclusion)
    # For each tool, and each pair of operations on the same tool, enforce ordering
    import itertools

    tool_ops = {0: [], 1: [], 2: []}
    for l in lots:
        for k in steps:
            tool_ops[TOOL_SEQ[k]].append((l, k))

    # Binary variables for ordering pairs
    pairs = []
    for t in [0, 1, 2]:
        for op_i, op_j in itertools.combinations(tool_ops[t], 2):
            pairs.append((op_i, op_j))

    model.PAIRS = pyo.Set(initialize=list(range(len(pairs))), dimen=1)

    # binary: 1 if op_i before op_j, 0 otherwise
    model.before = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def disj_rule_i(model, idx):
        op_i, op_j = pairs[idx]
        return model.start[op_i] + p[op_i] <= model.start[op_j] + total_time * (1 - model.before[idx])

    def disj_rule_j(model, idx):
        op_i, op_j = pairs[idx]
        return model.start[op_j] + p[op_j] <= model.start[op_i] + total_time * model.before[idx]

    model.disj_i = pyo.Constraint(model.PAIRS, rule=disj_rule_i)
    model.disj_j = pyo.Constraint(model.PAIRS, rule=disj_rule_j)

    # Objective: minimize makespan
    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}