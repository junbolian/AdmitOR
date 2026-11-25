import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]
    leg_utilization = params["leg_utilization"]

    num_packages = len(revenue)
    num_legs = len(capacity)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_packages - 1)
    model.L = pyo.RangeSet(0, num_legs - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def demand_rule(mdl, p):
        return mdl.x[p] <= demand[p]
    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def capacity_rule(mdl, l):
        return sum(leg_utilization[l][p] * mdl.x[p] for p in range(num_packages)) <= capacity[l]
    model.capacity_con = pyo.Constraint(model.L, rule=capacity_rule)

    model.obj = pyo.Objective(
        expr=sum(revenue[p] * model.x[p] for p in range(num_packages)),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}