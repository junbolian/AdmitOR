import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_hosp = len(demand)
    n_cent = len(opening_cost)
    hospitals = range(n_hosp)
    centers = range(n_cent)

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=list(hospitals))
    model.J = pyo.Set(initialize=list(centers))

    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)
    model.y = pyo.Var(model.J, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(opening_cost[j] * mdl.y[j] for j in mdl.J) + \
               sum(demand[i] * transport_cost[i][j] * mdl.x[i, j]
                   for i in mdl.I for j in mdl.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def single_source_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) == 1

    model.single_source = pyo.Constraint(model.I, rule=single_source_rule)

    def capacity_rule(mdl, j):
        return sum(demand[i] * mdl.x[i, j] for i in mdl.I) <= capacity[j] * mdl.y[j]

    model.capacity_link = pyo.Constraint(model.J, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}