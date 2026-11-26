import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    regions = list(range(n))
    arc_list = [(i, j) for i in regions for j in regions if i != j]

    model = pyo.ConcreteModel()

    model.regions = pyo.Set(initialize=regions)
    model.arcs = pyo.Set(initialize=arc_list, dimen=2)

    model.ship = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def _obj_rule(mdl):
        return sum(transport_cost[i][j] * mdl.ship[i, j] for (i, j) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=_obj_rule, sense=pyo.minimize)

    # Final stock at each region must meet demand
    def _balance_rule(mdl, i):
        outgoing = sum(mdl.ship[i, j] for j in mdl.regions if j != i)
        incoming = sum(mdl.ship[j, i] for j in mdl.regions if j != i)
        return supply[i] - outgoing + incoming >= demand[i]

    model.balance = pyo.Constraint(model.regions, rule=_balance_rule)

    # Cannot ship more than available supply from any region
    def _supply_limit_rule(mdl, i):
        return sum(mdl.ship[i, j] for j in mdl.regions if j != i) <= supply[i]

    model.supply_limit = pyo.Constraint(model.regions, rule=_supply_limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}