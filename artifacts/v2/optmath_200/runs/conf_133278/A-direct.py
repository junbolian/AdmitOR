import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)
    origins = list(range(n_orig))
    dests = list(range(n_dest))

    model = pyo.ConcreteModel()

    model.origin_set = pyo.Set(initialize=origins, ordered=True)
    model.dest_set = pyo.Set(initialize=dests, ordered=True)
    model.arcs = pyo.Set(initialize=[(o, d) for o in origins for d in dests],
                         dimen=2, ordered=True)

    model.x = pyo.Var(model.arcs, bounds=lambda m, o, d: (0.0, capacity[o][d]))

    def tot_cost(m):
        return sum(cost[o][d] * m.x[o, d] for o in origins for d in dests)

    model.total_cost = pyo.Objective(rule=tot_cost, sense=pyo.minimize)

    def supply_rule(m, o):
        return sum(m.x[o, d] for d in dests) == supply[o]
    model.supply_con = pyo.Constraint(model.origin_set, rule=supply_rule)

    def demand_rule(m, d):
        return sum(m.x[o, d] for o in origins) == demand[d]
    model.demand_con = pyo.Constraint(model.dest_set, rule=demand_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}