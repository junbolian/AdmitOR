import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_supply = params["initial_supply"]
    required_supply = params["required_supply"]
    transfer_cost = params["transfer_cost"]

    n = len(initial_supply)
    facilities = list(range(n))

    model = pyo.ConcreteModel()

    model.ship = pyo.Var(facilities, facilities, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            transfer_cost[i][j] * mdl.ship[i, j]
            for i in facilities
            for j in facilities
            if i != j
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.net = pyo.Constraint(
        facilities,
        rule=lambda mdl, i: sum(mdl.ship[i, j] for j in facilities if j != i)
        - sum(mdl.ship[j, i] for j in facilities if j != i)
        == required_supply[i] - initial_supply[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}