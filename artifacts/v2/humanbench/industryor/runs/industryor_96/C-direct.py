import gurobipy as gp
from gurobipy import GRB
from itertools import product

def solve(params):
    order_widths = params["order_widths"]    # list of widths for each order
    order_lengths = params["order_lengths"]  # list of required lengths for each order
    standard_widths = params["standard_widths"]  # list of standard roll widths

    n_orders = len(order_widths)
    n_std = len(standard_widths)

    orders = range(n_orders)
    stds = range(n_std)

    # Generate all feasible cutting patterns for each standard width.
    # A pattern is a tuple (a_0, a_1, ..., a_{n_orders-1}) giving how many times
    # each order width is cut from a single standard roll of that width.
    # Feasibility: sum(a_i * order_widths[i]) <= standard_widths[s]
    # We enumerate patterns with bounded counts.

    def generate_patterns(std_width):
        patterns = []
        # max count for each order width
        max_counts = [int(std_width / order_widths[i]) for i in orders]

        ranges = [range(0, max_counts[i] + 1) for i in orders]
        for combo in product(*ranges):
            used = sum(combo[i] * order_widths[i] for i in orders)
            if used <= std_width + 1e-9:
                patterns.append(combo)
        return patterns

    # patterns_by_std[s] = list of patterns for standard width s
    patterns_by_std = [generate_patterns(standard_widths[s]) for s in stds]

    # Waste per unit length for pattern p on standard width s:
    # waste = standard_widths[s] - sum(pattern[i] * order_widths[i])
    # Total waste area for x[s][p] length used = waste * x[s][p]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[s][p] = length (m) of standard roll s cut using pattern p
    x = {}
    for s in stds:
        for p_idx, pat in enumerate(patterns_by_std[s]):
            x[s, p_idx] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{s}_{p_idx}")

    # Objective: minimize total waste area
    # waste area = sum over s, p of (standard_widths[s] - sum_i(pat[i]*order_widths[i])) * x[s,p]
    obj_expr = gp.LinExpr()
    for s in stds:
        for p_idx, pat in enumerate(patterns_by_std[s]):
            waste = standard_widths[s] - sum(pat[i] * order_widths[i] for i in orders)
            obj_expr += waste * x[s, p_idx]

    model.setObjective(obj_expr, GRB.MINIMIZE)

    # Demand constraints: for each order i, total length produced >= order_lengths[i]
    for i in orders:
        demand_expr = gp.LinExpr()
        for s in stds:
            for p_idx, pat in enumerate(patterns_by_std[s]):
                if pat[i] > 0:
                    demand_expr += pat[i] * x[s, p_idx]
        model.addConstr(demand_expr >= order_lengths[i], name=f"demand_{i}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}