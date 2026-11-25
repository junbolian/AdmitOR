import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    master_width = params["master_width"]
    order_quantities = params["order_quantities"]
    finished_widths = params["finished_widths"]

    n_orders = len(order_quantities)

    # Generate all feasible slitting patterns:
    # a pattern is a vector (count_0, count_1, ..., count_{n-1}) with
    # sum(count_i * width_i) <= master_width.
    patterns = []
    max_counts = [int(master_width // finished_widths[i]) for i in range(n_orders)]

    def gen_patterns(idx, current, remaining):
        if idx == n_orders:
            patterns.append(tuple(current))
            return
        for k in range(max_counts[idx] + 1):
            used = k * finished_widths[idx]
            if used > remaining:
                break
            current.append(k)
            gen_patterns(idx + 1, current, remaining - used)
            current.pop()

    gen_patterns(0, [], master_width)

    n_patterns = len(patterns)
    pattern_tuples = {p: i for i, p in enumerate(patterns)}

    model = pyo.ConcreteModel()

    model.PATTERNS = pyo.RangeSet(0, n_patterns - 1)
    model.ORDERS = pyo.RangeSet(0, n_orders - 1)

    # x[p] = number of times pattern p is used
    model.x = pyo.Var(model.PATTERNS, domain=pyo.NonNegativeIntegers)

    # Objective: minimize total master rolls used
    model.total_rolls = pyo.Objective(
        expr=sum(model.x[p] for p in model.PATTERNS),
        sense=pyo.minimize,
    )

    def demand_rule(mdl, i):
        return sum(patterns[p][i] * mdl.x[p] for p in mdl.PATTERNS) == order_quantities[i]

    model.demand = pyo.Constraint(model.ORDERS, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_rolls))
    return {"objective": obj_val, "status": "optimal"}