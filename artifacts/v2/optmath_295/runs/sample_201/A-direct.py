import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

N_AIRCRAFT = 6
N_ROUTES = 7


def solve(params):
    availability = params["availability"]
    route_demand = params["route_demand"]
    route6_demand = params["route6_demand"]
    a0_capacity = params["a0_capacity"]
    a1_capacity = params["a1_capacity"]
    operational_cost = params["operational_cost"]

    model = pyo.ConcreteModel()
    model.A = pyo.RangeSet(0, N_AIRCRAFT - 1)
    model.R = pyo.RangeSet(0, N_ROUTES - 1)

    def cap(a, r):
        if a == 0:
            return a0_capacity[r]
        if a == 1:
            return a1_capacity[r]
        return a0_capacity[r]

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def avail_rule(mdl, a):
        return sum(mdl.x[a, r] for r in mdl.R) <= availability[a]

    model.avail_con = pyo.Constraint(model.A, rule=avail_rule)

    def demand_rule(mdl, r):
        if r == N_ROUTES - 1:
            rhs = route6_demand
        else:
            rhs = route_demand[r]
        return sum(cap(a, r) * mdl.x[a, r] for a in mdl.A) >= rhs

    model.demand_con = pyo.Constraint(model.R, rule=demand_rule)

    def obj_rule(mdl):
        return sum(operational_cost[a][r] * mdl.x[a, r]
                   for a in mdl.A for r in mdl.R)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}