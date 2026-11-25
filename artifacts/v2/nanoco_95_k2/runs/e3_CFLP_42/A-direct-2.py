import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_hospitals = len(demand)
    n_centers = len(opening_cost)

    hospitals = range(n_hospitals)
    centers = range(n_centers)

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=list(hospitals))
    model.J = pyo.Set(initialize=list(centers))

    model.x = pyo.Var(model.J, within=pyo.Binary)
    model.z = pyo.Var(model.I, model.J, within=pyo.Binary)

    def obj_rule(mdl):
        return sum(opening_cost[j] * mdl.x[j] for j in mdl.J) + sum(
            transport_cost[i][j] * demand[i] * mdl.z[i, j]
            for i in mdl.I
            for j in mdl.J
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(mdl, i):
        return sum(mdl.z[i, j] for j in mdl.J) == 1

    model.assign_constraint = pyo.Constraint(model.I, rule=assign_rule)

    def cap_rule(mdl, j):
        return sum(demand[i] * mdl.z[i, j] for i in mdl.I) <= capacity[j] * mdl.x[j]

    model.capacity_constraint = pyo.Constraint(model.J, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}