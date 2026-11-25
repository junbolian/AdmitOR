import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    net_demands = params["net_demands"]
    city_capacity = params["city_capacity"]
    link_capacity = params["link_capacity"]

    n = 7
    cities = list(range(n))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=cities)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def cost_rule(md):
        return sum(costs[arcs.index((i, j))] * md.flow[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def balance_rule(md, k):
        inflow = sum(md.flow[i, k] for i in cities if i != k)
        outflow = sum(md.flow[k, j] for j in cities if j != k)
        return inflow - outflow == net_demands[k]

    model.balance = pyo.Constraint(model.I, rule=balance_rule)

    def receive_cap_rule(md, k):
        return sum(md.flow[i, k] for i in cities if i != k) <= city_capacity[k]

    model.receive_cap = pyo.Constraint(model.I, rule=receive_cap_rule)

    def link_cap_rule(md, i, j):
        return md.flow[i, j] <= link_capacity[arcs.index((i, j))]

    model.link_cap = pyo.Constraint(model.A, rule=link_cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}