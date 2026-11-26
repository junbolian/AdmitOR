import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    source = 0
    dest = 5

    model = pyo.ConcreteModel()

    def capacity(i, j):
        return params["capacity_{}_{}".format(i, j)]

    # Flow variables: number of trains on each directed track
    model.flow = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    # Flow conservation at intermediate nodes, supply at source
    def flow_rule(md, i):
        inflow = sum(md.flow[j, i] for j in cities if j != i)
        outflow = sum(md.flow[i, j] for j in cities if j != i)
        if i == source:
            return outflow - inflow <= 0
        elif i == dest:
            return inflow - outflow <= 0
        else:
            return inflow - outflow == 0

    model.flow_con = pyo.Constraint(cities, rule=flow_rule)

    # Capacity constraints
    def cap_rule(md, i, j):
        return md.flow[i, j] <= capacity(i, j)

    model.capacity_con = pyo.Constraint(arcs, rule=cap_rule)

    # Objective: maximize total trucks/trains arriving at destination
    total_at_dest = sum(model.flow[j, dest] for j in cities if j != dest)
    model.total = pyo.Expression(expr=total_at_dest)
    model.obj = pyo.Objective(expr=model.total, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}