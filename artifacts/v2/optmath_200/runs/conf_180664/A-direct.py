import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 5
    cities = list(range(N))
    nodes_nonzero = list(range(1, N))

    # Distance matrix from params
    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[(i, j)] = params["dist_%d_%d" % (i, j)]

    u_min = params["u_min"]
    u_max = params["u_max"]

    model = pyo.ConcreteModel()

    # Binary arc variables
    model.x = pyo.Var([(i, j) for i in cities for j in cities if i != j],
                      domain=pyo.Binary)

    # Position variables for non-zero cities
    model.u = pyo.Var(nodes_nonzero, bounds=(u_min, u_max))

    # Objective: minimize total distance
    def obj_rule(m):
        return sum(dist[(i, j)] * m.x[(i, j)]
                   for i in cities for j in cities if i != j)
    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Degree constraints: leave each city exactly once
    def leave_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1
    model.leave = pyo.Constraint(cities, rule=leave_rule)

    # Degree constraints: enter each city exactly once
    def enter_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1
    model.enter = pyo.Constraint(cities, rule=enter_rule)

    # Subtour elimination (MTZ) for non-zero cities
    def mtz_rule(m, i, j):
        if i != j:
            return m.u[i] - m.u[j] + (N - 1) * m.x[(i, j)] <= N - 2
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(nodes_nonzero, nodes_nonzero, rule=mtz_rule)

    # Solve
    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}