import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    net_demands = params["net_demands"]
    city_capacity = params["city_capacity"]
    link_capacity = params["link_capacity"]

    n = 7
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    arc_index = {a: k for k, a in enumerate(arcs)}

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.cities = pyo.RangeSet(0, n - 1)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def arc_bound_rule(md, i, j):
        return (0, link_capacity[arc_index[(i, j)]])

    model.flow_bounds = pyo.Constraint(model.arcs, rule=arc_bound_rule)

    def balance_rule(md, i):
        inflow = sum(md.flow[j, i] for j in range(n) if j != i)
        outflow = sum(md.flow[i, j] for j in range(n) if j != i)
        return inflow - outflow == net_demands[i]

    model.balance = pyo.Constraint(model.cities, rule=balance_rule)

    def receive_rule(md, i):
        return sum(md.flow[j, i] for j in range(n) if j != i) <= city_capacity[i]

    model.receive_cap = pyo.Constraint(model.cities, rule=receive_rule)

    def obj_rule(md):
        return sum(costs[arc_index[(i, j)]] * md.flow[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}