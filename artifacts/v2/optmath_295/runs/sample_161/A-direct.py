import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n_cities"])
    max_position = int(params["max_position"])
    cities = list(range(n))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["c_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=cities, ordered=True)
    model.A = pyo.Set(
        initialize=[(i, j) for i in cities for j in cities if i != j],
        dimen=2,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    model.pos = pyo.Var(model.I, domain=pyo.NonNegativeIntegers, bounds=(0, max_position))
    model.pos[0].fix(0)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[i, j] for (i, j) in m.A)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def depart_rule(m, i):
        return sum(m.x[i, j] for j in m.I if j != i) == 1

    model.depart = pyo.Constraint(model.I, rule=depart_rule)

    def arrive_rule(m, j):
        return sum(m.x[i, j] for i in m.I if i != j) == 1

    model.arrive = pyo.Constraint(model.I, rule=arrive_rule)

    # MTZ subtour elimination over non-depot arcs only.
    # For arc (i,j) with i != 0 and j != 0:
    #   pos[i] - pos[j] + n * x[i,j] <= n - 1
    # For arcs leaving depot (0,j) or returning to depot (i,0), no MTZ needed.
    non_depot_arcs = [(i, j) for (i, j) in model.A if i != 0 and j != 0]
    model.ND = pyo.Set(initialize=non_depot_arcs, dimen=2)

    def subtour_rule(m, i, j):
        return m.pos[i] - m.pos[j] + n * m.x[i, j] <= n - 1

    model.subtour = pyo.Constraint(model.ND, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}