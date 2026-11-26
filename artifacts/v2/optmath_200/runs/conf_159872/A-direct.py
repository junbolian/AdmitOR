import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)
    n_prod = len(supply[0])

    origins = list(range(n_orig))
    dests = list(range(n_dest))
    prods = list(range(n_prod))

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=origins)
    model.dests = pyo.Set(initialize=dests)
    model.prods = pyo.Set(initialize=prods)

    # Decision variables: x[(o, d, p)]
    model.x = pyo.Var(model.origins, model.dests, model.prods, domain=pyo.NonNegativeReals)

    # Objective: minimize total transportation cost
    model.total_cost = pyo.Objective(
        expr=sum(cost[o][d][p] * model.x[o, d, p]
                 for o in origins for d in dests for p in prods),
        sense=pyo.minimize,
    )

    # Supply constraints: total shipped from each origin for each product equals supply
    model.supply_con = pyo.Constraint(
        model.origins, model.prods,
        rule=lambda mdl, o, p: sum(mdl.x[o, d, p] for d in dests) == supply[o][p],
    )

    # Demand constraints: total received at each destination for each product equals demand
    model.demand_con = pyo.Constraint(
        model.dests, model.prods,
        rule=lambda mdl, d, p: sum(mdl.x[o, d, p] for o in origins) == demand[d][p],
    )

    # Capacity constraints: total units (both products) between origin and destination
    model.capacity_con = pyo.Constraint(
        model.origins, model.dests,
        rule=lambda mdl, o, d: sum(mdl.x[o, d, p] for p in prods) <= capacity[o][d],
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}