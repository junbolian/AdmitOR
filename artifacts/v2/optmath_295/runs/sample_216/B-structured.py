# {
#   "sets": {"I": "0..6", "J": "0..7"},
#   "params": {"supplies": "params['supplies'][i]", "demands": "params['demands'][j]", "costs": "params['costs'][i][j]"},
#   "variables": {"shipment[i,j]": "NonNegativeReals, i in I, j in J"},
#   "constraints": [
#     "sum(shipment[i,j] for j in J) == supplies[i], for each i in I",
#     "sum(shipment[i,j] for i in I) == demands[j], for each j in J"
#   ],
#   "objective": "minimize sum(costs[i,j] * shipment[i,j] for i in I, j in J)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    costs = params["costs"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 6)
    model.J = pyo.RangeSet(0, 7)

    model.supplies = pyo.Param(
        model.I,
        initialize={i: supplies[i] for i in model.I},
    )
    model.demands = pyo.Param(
        model.J,
        initialize={j: demands[j] for j in model.J},
    )
    model.costs = pyo.Param(
        model.I,
        model.J,
        initialize={(i, j): costs[i][j] for i in model.I for j in model.J},
    )

    model.shipment = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.J)
            == instance.supplies[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.I)
            == instance.demands[j]
        )

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[i, j] * model.shipment[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}