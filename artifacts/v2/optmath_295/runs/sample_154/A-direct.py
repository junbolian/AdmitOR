import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.ORIG = pyo.RangeSet(0, n_orig - 1)
    model.DEST = pyo.RangeSet(0, n_dest - 1)

    def flow_bounds(mdl, i, j):
        return (0, None)

    model.flow = pyo.Var(model.ORIG, model.DEST, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            cost_matrix[i][j] * mdl.flow[i, j]
            for i in range(n_orig)
            for j in range(n_dest)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in range(n_dest)) == supply[i]

    model.supply_con = pyo.Constraint(model.ORIG, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.flow[i, j] for i in range(n_orig)) == demand[j]

    model.demand_con = pyo.Constraint(model.DEST, rule=demand_rule)

    try:
        Highs().solve(model)
    except Exception:
        return {"objective": None, "status": "solver failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "no solution"}

    return {"objective": obj_val, "status": "optimal"}