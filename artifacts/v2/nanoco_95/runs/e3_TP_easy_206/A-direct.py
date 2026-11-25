import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_supply = 3
    n_demand = 4
    supply_nodes = list(range(n_supply))
    demand_nodes = list(range(n_supply, n_supply + n_demand))
    arcs = [(i, j) for i in supply_nodes for j in demand_nodes]

    supply = params["supply"]
    demand = params["demand"]
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]

    cap = {a: arc_capacity[k] for k, a in enumerate(arcs)}
    cost = {a: arc_cost[k] for k, a in enumerate(arcs)}
    dem = {demand_nodes[k]: demand[k] for k in range(n_demand)}

    model = pyo.ConcreteModel()

    model.S = pyo.Set(initialize=supply_nodes, ordered=True)
    model.D = pyo.Set(initialize=demand_nodes, ordered=True)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def ship_cap_rule(model, i, j):
        return model.x[i, j] <= cap[(i, j)]

    model.ship_cap = pyo.Constraint(model.A, rule=ship_cap_rule)

    def supply_rule(model, i):
        return sum(model.x[i, j] for j in model.D) == supply[i]

    model.supply_balance = pyo.Constraint(model.S, rule=supply_rule)

    def demand_rule(model, j):
        return sum(model.x[i, j] for i in model.S) == dem[j]

    model.demand_balance = pyo.Constraint(model.D, rule=demand_rule)

    def obj_rule(model):
        return sum(cost[(i, j)] * model.x[i, j] for (i, j) in model.A)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}