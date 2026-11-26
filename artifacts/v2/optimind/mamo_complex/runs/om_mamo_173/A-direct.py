import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_supply = params["initial_supply"]
    required_demand = params["required_demand"]
    transfer_cost = params["transfer_cost"]

    num_fac = 7
    facilities = [i + 1 for i in range(num_fac)]

    # transfer_cost is given row-wise: for row i, the columns are the other
    # facilities in ascending order (diagonal omitted). Build full lookup.
    cost = {}
    for i in facilities:
        others = [j for j in facilities if j != i]
        for idx, j in enumerate(others):
            cost[(i, j)] = float(transfer_cost[i - 1][idx])

    arcs = [(i, j) for i in facilities for j in facilities if i != j]

    model = pyo.ConcreteModel()

    # Upper bound on any single transfer: total supply
    big_m = float(sum(initial_supply[i - 1] for i in facilities))

    model.x = pyo.Var(arcs, domain=pyo.NonNegativeReals, bounds=(0, big_m))

    model.total_cost = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def balance_rule(mdl, i):
        inflow = sum(mdl.x[(k, i)] for k in facilities if k != i)
        outflow = sum(mdl.x[(i, k)] for k in facilities if k != i)
        return initial_supply[i - 1] + inflow - outflow == required_demand[i - 1]

    model.balance = pyo.Constraint(facilities, rule=balance_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible_or_unbounded"}

    return {"objective": obj_val, "status": "optimal"}