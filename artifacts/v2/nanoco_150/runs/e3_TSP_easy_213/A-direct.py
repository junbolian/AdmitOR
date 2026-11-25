import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    travel = params["travel_time_matrix"]
    n = len(travel)
    nodes = list(range(n))
    customers = list(range(1, n))

    model = pyo.ConcreteModel()

    # Decision variables: x[i,j] = 1 if arc i->j used
    model.x = pyo.Var(nodes, nodes, domain=pyo.Binary)

    # MTZ ordering variables for subtour elimination (customers only)
    model.u = pyo.Var(customers, domain=pyo.NonNegativeReals)

    # Objective: minimize total travel time
    def obj_rule(mdl):
        return sum(travel[i][j] * mdl.x[i, j]
                   for i in nodes for j in nodes if i != j)
    model.total_time = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in nodes if j != i) == 1
    model.out_arc = pyo.Constraint(nodes, rule=out_rule)

    # Each node has exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in nodes if i != j) == 1
    model.in_arc = pyo.Constraint(nodes, rule=in_rule)

    # MTZ subtour elimination
    def mtz_rule(mdl, i, j):
        if i != j and j != 0:
            return mdl.u[i] - mdl.u[j] + (n - 1) * mdl.x[i, j] <= n - 2
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(customers, customers, rule=mtz_rule)

    # Bounds on u for customers
    model.u_bound = pyo.Constraint(customers,
                                   rule=lambda mdl, i: (1, mdl.u[i], n - 1))

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_time))
    return {"objective": obj_val, "status": "optimal"}