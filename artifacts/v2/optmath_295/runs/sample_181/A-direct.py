import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Cities
    cities = [0, 1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    # Cost data from params
    cost = {(i, j): params["cost_%d_%d" % (i, j)] for (i, j) in arcs}

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.Reals)

    # Objective: minimize total delivery cost
    def obj_rule(model):
        return sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city visited exactly once (indegree == 1)
    def in_flow_rule(model, j):
        return sum(model.x[(i, j)] for i in cities if i != j) == 1
    model.in_flow = pyo.Constraint(cities, rule=in_flow_rule)

    # Each city departed exactly once (outdegree == 1)
    def out_flow_rule(model, i):
        return sum(model.x[(i, j)] for j in cities if j != i) == 1
    model.out_flow = pyo.Constraint(cities, rule=out_flow_rule)

    # Position bounds for cities 1..4
    for c in [1, 2, 3, 4]:
        model.add_component(
            "u_bounds_lb_%d" % c,
            pyo.Constraint(expr=model.u[c] >= 1)
        )
        model.add_component(
            "u_bounds_ub_%d" % c,
            pyo.Constraint(expr=model.u[c] <= 4)
        )

    # Subtour elimination (MTZ) for arcs among nodes 1..4
    subtour_arcs = [(i, j) for (i, j) in arcs if i != 0 and j != 0]

    def mtz_rule(model, i, j):
        return model.u[i] - model.u[j] + 5 * model.x[(i, j)] <= 4
    model.mtz = pyo.Constraint(subtour_arcs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}