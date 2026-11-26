import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    widths = list(params["order_widths"])
    lengths = list(params["order_lengths"])
    std = list(params["standard_widths"])
    n = len(widths)
    m = len(std)

    model = pyo.ConcreteModel()

    # x[j]: number of standard rolls of width std[j] used
    model.x = pyo.Var(range(m), domain=pyo.NonNegativeReals)

    # demand satisfied: sum_j x[j] * std[j] >= sum_i widths[i]*lengths[i]
    # but must allow multiple orders fitted per strip: model by counting
    # Length produced from std j is x[j] (since roll length unlimited,
    # for each standard roll of width w_j we get x[j] meters of that width).
    # Cutting pattern: each meter of std width j is sliced into pieces covering
    # orders. Aggregate area balance: total produced area >= total demand area.
    # Per-order length must be met, which is a width-constrained packing.
    # Use continuous cutting pattern variables.

    # Patterns: enumerate all combinations of orders whose widths sum <= std width
    patterns = []  # (std_idx, tuple of counts per order)
    for sj in range(m):
        W = std[sj]

        def rec(i, remaining, cur):
            if i == n:
                if any(c > 0 for c in cur):
                    patterns.append((sj, tuple(cur)))
                return
            maxc = int(remaining // widths[i] + 1e-9)
            for c in range(maxc + 1):
                cur.append(c)
                rec(i + 1, remaining - c * widths[i], cur)
                cur.pop()

        rec(0, W, [])

    pidx = list(range(len(patterns)))
    model.p = pidx

    # y[k]: length (meters) of pattern k used
    model.y = pyo.Var(model.p, domain=pyo.NonNegativeReals)

    # Order length requirements
    model.demand = pyo.Constraint(range(n))
    for i in range(n):
        model.demand[i] = sum(
            patterns[k][1][i] * model.y[k] for k in pidx
        ) >= lengths[i]

    # Objective: minimize wasted area = sum over std rolls used area - demand area
    # area of std sj used = W_sj * (sum of y[k] for k with pattern std=sj)
    # minus demand area (constant) => minimize sum_k W_{sj(k)} * y[k]
    def obj_rule(mdl):
        return sum(std[patterns[k][0]] * mdl.y[k] for k in pidx)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}