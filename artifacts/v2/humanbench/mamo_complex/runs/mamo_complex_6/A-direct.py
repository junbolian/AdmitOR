import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = len(opening_costs)
    n_outlets = len(demands)
    centers = list(range(n_centers))
    outlets = list(range(n_outlets))

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=centers)
    model.outlets = pyo.Set(initialize=outlets)
    model.links = pyo.Set(initialize=[(i, j) for i in centers for j in outlets])

    model.use = pyo.Var(model.centers, within=pyo.Binary)
    model.flow = pyo.Var(model.links, within=pyo.NonNegativeReals)

    def demand_rule(mdl, j):
        return sum(mdl.flow[i, j] for i in mdl.centers) == demands[j]
    model.demand_con = pyo.Constraint(model.outlets, rule=demand_rule)

    def cap_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in mdl.outlets) <= capacities[i] * mdl.use[i]
    model.cap_con = pyo.Constraint(model.centers, rule=cap_rule)

    def obj_rule(mdl):
        return sum(opening_costs[i] * mdl.use[i] for i in mdl.centers) + \
               sum(transport_costs[i][j] * mdl.flow[i, j] for (i, j) in mdl.links)
    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}