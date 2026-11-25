import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    investment_cost = params["investment_cost"]
    distance_matrix = params["distance_matrix"]

    n_demand = len(distance_matrix)
    n_sites = len(investment_cost)

    model = pyo.ConcreteModel()

    model.demand = pyo.RangeSet(0, n_demand - 1)
    model.sites = pyo.RangeSet(0, n_sites - 1)

    model.open_site = pyo.Var(model.sites, domain=pyo.Binary)
    model.assign = pyo.Var(model.demand, model.sites, domain=pyo.Binary)

    def investment_rule(m):
        return sum(investment_cost[j] * m.open_site[j] for j in m.sites)

    def travel_rule(m):
        return sum(distance_matrix[i][j] * m.assign[i, j]
                   for i in m.demand for j in m.sites)

    model.investment_cost_expr = pyo.Expression(rule=investment_rule)
    model.travel_cost_expr = pyo.Expression(rule=travel_rule)

    model.obj = pyo.Objective(
        expr=model.investment_cost_expr + model.travel_cost_expr,
        sense=pyo.minimize,
    )

    def assign_once_rule(m, i):
        return sum(m.assign[i, j] for j in m.sites) == 1

    model.assign_once = pyo.Constraint(model.demand, rule=assign_once_rule)

    def link_rule(m, i, j):
        return m.assign[i, j] <= m.open_site[j]

    model.link = pyo.Constraint(model.demand, model.sites, rule=link_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}