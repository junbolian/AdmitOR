import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 6
    cities = list(range(N))
    pairs = [(i, j) for i in cities for j in cities if i != j]

    def dist(i, j):
        return params["dist_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(pairs, domain=pyo.Binary)
    # MTZ order variables: u[i] in [1, N-1] for i != 0, u[0] = 0
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(0, N - 1))

    model.obj = pyo.Objective(
        expr=sum(dist(i, j) * model.x[i, j] for (i, j) in pairs),
        sense=pyo.minimize,
    )

    # Each city: exactly one outgoing arc
    model.out_rule = pyo.Constraint(
        cities, rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1
    )
    # Each city: exactly one incoming arc
    model.in_rule = pyo.Constraint(
        cities, rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1
    )

    # Fix position of city 0 at 0
    model.pos0 = pyo.Constraint(expr=model.u[0] == 0)

    # MTZ subtour elimination: for arcs leaving nonzero cities,
    # u_j >= u_i + 1 - (N-1)*(1 - x_ij)
    # For arcs leaving city 0: u_j >= 1 - (N-1)*(1 - x_0j)
    def sec_rule(m, i, j):
        if i == 0:
            return m.u[j] >= 1 - (N - 1) * (1 - m.x[i, j])
        return m.u[j] >= m.u[i] + 1 - (N - 1) * (1 - m.x[i, j])

    model.sec = pyo.Constraint(pairs, rule=sec_rule)

    # Positions of nonzero cities are at least 1
    model.lb = pyo.Constraint(cities, rule=lambda m, i: pyo.Constraint.Skip if i == 0 else m.u[i] >= 1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}