import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = [params["cost_strategy_%d" % (i + 1)] for i in range(8)]

    coverage = [
        [1, 2, 3, 4, 7],
        [1, 3, 5, 6, 7, 8],
        [2, 3, 4, 5, 7],
        [5, 6],
        [2, 3, 5, 7, 8],
        [3, 6, 7, 8],
        [7],
        [4, 8],
        [2, 3, 6, 8],
        [2, 4, 7],
        [5, 6],
        [1, 2, 4, 7],
        [2, 3, 4, 6, 8],
        [1, 2, 3, 7],
        [5, 6],
        [1, 2, 3, 5, 6, 7, 8],
        [7],
        [1, 4, 6],
        [2, 5, 7],
        [3, 6],
        [1, 4, 5, 6],
        [2, 5, 6, 8],
        [1, 8],
        [4, 5, 6, 8],
        [1],
        [1, 2, 4, 8],
        [7],
        [2, 4],
        [1, 2, 4, 6],
        [7, 8],
        [3, 4],
        [5, 8],
        [4, 6],
        [3, 5, 7],
        [3, 5, 6],
        [1, 3, 4, 5],
        [2],
        [1, 2, 6],
        [1, 2, 3, 4, 7, 8],
    ]

    # Convert 1-based strategy indices to 0-based
    coverage0 = [[s - 1 for s in seg] for seg in coverage]

    num_strategies = len(costs)
    num_segments = len(coverage0)

    model = pyo.ConcreteModel()
    model.strategies = pyo.Set(initialize=list(range(num_strategies)))
    model.segments = pyo.Set(initialize=list(range(num_segments)))

    model.x = pyo.Var(model.strategies, domain=pyo.Binary)

    def obj_rule(_):
        return sum(costs[i] * model.x[i] for i in range(num_strategies))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(mod, seg):
        return sum(mod.x[i] for i in coverage0[seg]) >= 1

    model.cover = pyo.Constraint(model.segments, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}