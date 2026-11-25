import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.destinations = pyo.RangeSet(0, n_dest - 1)
    model.routes = pyo.Set(initialize=[(i, j) for i in model.origins for j in model.destinations], dimen=2)

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(transport_cost[i][j] * m.flow[i, j] for (i, j) in m.routes)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.flow[i, j] for j in m.destinations) == supply[i]
    model.supply_constraint = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in m.origins) == demand[j]
    model.demand_constraint = pyo.Constraint(model.destinations, rule=demand_rule)

    try:
        solver = Highs()
        solver.solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}