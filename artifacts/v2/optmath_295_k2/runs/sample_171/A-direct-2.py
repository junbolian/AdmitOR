import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    origins = list(range(len(supply)))
    destinations = list(range(len(demand)))

    model = pyo.ConcreteModel()
    model.origins = pyo.Set(initialize=origins)
    model.destinations = pyo.Set(initialize=destinations)
    model.arcs = pyo.Set(initialize=[(i, j) for i in origins for j in destinations])

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in m.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in destinations) == supply[i]

    model.supply_constraint = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in origins) == demand[j]

    model.demand_constraint = pyo.Constraint(model.destinations, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.capacity_constraint = pyo.Constraint(model.arcs, rule=cap_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or solver failed"}