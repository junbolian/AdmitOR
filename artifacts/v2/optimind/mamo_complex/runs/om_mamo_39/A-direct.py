import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    centers = list(range(1, 6))
    stores = list(range(1, 10))

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=centers, ordered=True)
    model.stores = pyo.Set(initialize=stores, ordered=True)

    # y[i]: open center i
    model.y = pyo.Var(model.centers, domain=pyo.Binary)
    # x[i,j]: flow from center i to store j
    model.x = pyo.Var(model.centers, model.stores, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(opening_cost[i - 1] * mdl.y[i] for i in mdl.centers) + \
               sum(transport_cost[i - 1][j - 1] * mdl.x[i, j]
                   for i in mdl.centers for j in mdl.stores)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand satisfaction
    model.demand_con = pyo.Constraint(
        model.stores,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.centers) == demand[j - 1]
    )

    # Capacity linking
    model.capacity_con = pyo.Constraint(
        model.centers,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in mdl.stores) <= capacity[i - 1] * mdl.y[i]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}