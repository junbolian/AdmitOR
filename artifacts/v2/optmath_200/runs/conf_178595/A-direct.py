import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]

    num_facilities = len(fixed_cost)
    num_customers = len(demand)

    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, num_facilities - 1)
    model.customers = pyo.RangeSet(0, num_customers - 1)

    model.open = pyo.Var(model.facilities, domain=pyo.Binary)
    model.ship = pyo.Var(
        model.facilities, model.customers, domain=pyo.NonNegativeReals
    )

    def obj_rule(m):
        return sum(
            fixed_cost[j] * m.open[j] for j in m.facilities
        ) + sum(
            shipping_cost[i][j] * m.ship[j, i]
            for j in m.facilities
            for i in m.customers
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, i):
        return sum(m.ship[j, i] for j in m.facilities) == demand[i]

    model.demand_con = pyo.Constraint(model.customers, rule=demand_rule)

    def capacity_rule(m, j):
        return sum(m.ship[j, i] for i in m.customers) <= capacity[j] * m.open[j]

    model.capacity_con = pyo.Constraint(model.facilities, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}