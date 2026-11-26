import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    hubs = list(range(8))
    source = 0
    dest = 7

    arcs = [
        (0,1),(0,2),(0,3),(0,5),(0,6),(0,7),
        (1,0),(1,2),(1,3),(1,4),(1,5),(1,6),
        (2,0),(2,1),(2,3),(2,4),(2,5),(2,6),(2,7),
        (3,0),(3,1),(3,2),(3,4),(3,5),(3,7),
        (4,0),(4,1),(4,2),(4,3),(4,5),(4,6),(4,7),
        (5,0),(5,1),(5,2),(5,3),(5,4),(5,6),(5,7),
        (6,0),(6,1),(6,2),(6,3),(6,4),(6,5),(6,7),
        (7,0),(7,1),(7,3),(7,4),(7,5),(7,6),
    ]

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.HUBS = pyo.Set(initialize=hubs)

    def cap_bounds(m, i, j):
        return (0, params["cap_{}_{}".format(i, j)])

    model.flow = pyo.Var(model.ARCS, bounds=cap_bounds)

    def flow_balance_rule(m, k):
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == k)
        rhs = 0
        if k == source:
            rhs = 1
        elif k == dest:
            rhs = -1
        return inflow - outflow == rhs

    model.balance = pyo.Constraint(model.HUBS, rule=flow_balance_rule)

    # maximize total flow out of source
    model.OBJ = pyo.Objective(
        expr=sum(model.flow[source, j] for (i, j) in arcs if i == source),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.OBJ))
    return {"objective": obj_val, "status": "optimal"}