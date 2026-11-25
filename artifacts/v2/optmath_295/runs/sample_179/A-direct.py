import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producers = list(range(6))
    contracts = list(range(6))

    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_coefficient = params["cost_coefficient"]

    # cost_coefficient may be indexed [i][j] or [j][i]; detect layout.
    def cost_at(i, j):
        c = cost_coefficient
        if isinstance(c, dict):
            if (i, j) in c:
                return c[(i, j)]
            if (j, i) in c:
                return c[(j, i)]
        try:
            v = c[i][j]
            if not isinstance(v, (list, dict, tuple)):
                return v
        except (TypeError, IndexError, KeyError):
            pass
        return c[j][i]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)

    def x_bounds(m, i, j):
        return (0, producer_capacity[i])

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals, bounds=x_bounds)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= producer_capacity[i]
    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= contract_demand[j]
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def contributors_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= min_contributors[j]
    model.contributors_con = pyo.Constraint(model.C, rule=contributors_rule)

    def link_lb_rule(m, i, j):
        return m.x[i, j] >= producer_min_delivery[i] * m.y[i, j]
    model.link_lb_con = pyo.Constraint(model.P, model.C, rule=link_lb_rule)

    def link_ub_rule(m, i, j):
        return m.x[i, j] <= producer_capacity[i] * m.y[i, j]
    model.link_ub_con = pyo.Constraint(model.P, model.C, rule=link_ub_rule)

    def obj_rule(m):
        return sum(cost_at(i, j) * m.x[i, j] for i in m.P for j in m.C)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}