import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)
    origins = range(n_orig)
    dests = range(n_dest)

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=list(origins))
    model.dests = pyo.Set(initialize=list(dests))
    model.routes = pyo.Set(initialize=[(i, j) for i in origins for j in dests],
                           dimen=2)

    model.x = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in origins for j in dests)
    model.total_cost = pyo.Expression(rule=cost_rule)

    # Supply must be fully utilized
    model.supply_cons = pyo.Constraint(
        model.origins,
        rule=lambda m, i: sum(m.x[i, j] for j in dests) == supply[i]
    )

    # Demand must be exactly met
    model.demand_cons = pyo.Constraint(
        model.dests,
        rule=lambda m, j: sum(m.x[i, j] for i in origins) == demand[j]
    )

    # Route capacity limits
    model.cap_cons = pyo.Constraint(
        model.routes,
        rule=lambda m, i, j: m.x[i, j] <= capacity[i][j]
    )

    model.obj = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}