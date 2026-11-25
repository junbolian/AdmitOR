import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    N = len(cost)
    cities = list(range(N))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.C = pyo.Set(initialize=cities, dimen=1)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    # Position variables: city 0 fixed at 0, others in 1..N-1
    model.u = pyo.Var(model.C, domain=pyo.NonNegativeReals)
    model.u[0].fix(0)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in m.A)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city: exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in m.C if j != i) == 1
    model.out_con = pyo.Constraint(model.C, rule=out_rule)

    # Each city: exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in m.C if i != j) == 1
    model.in_con = pyo.Constraint(model.C, rule=in_rule)

    # MTZ subtour elimination for cities 1..N-1
    other_cities = [i for i in cities if i != 0]

    def mtz_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (N - 1) * m.x[i, j] <= N - 2
    model.mtz_con = pyo.Constraint(model.A, rule=mtz_rule)

    # Position bounds for non-start cities
    def u_lb_rule(m, i):
        return m.u[i] >= 1
    model.u_lb = pyo.Constraint(other_cities, rule=u_lb_rule)

    def u_ub_rule(m, i):
        return m.u[i] <= N - 1
    model.u_ub = pyo.Constraint(other_cities, rule=u_ub_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}