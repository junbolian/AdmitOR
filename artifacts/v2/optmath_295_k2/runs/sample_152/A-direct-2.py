import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = int(params["num_cities"])
    cities = range(n)

    # Cost dict from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_{0}_{1}".format(i, j)]

    model = pyo.ConcreteModel()

    # Arc selection variables
    model.x = pyo.Var([(i, j) for i in cities for j in cities if i != j],
                      domain=pyo.Binary)

    # Position (order) variables
    model.u = pyo.Var(cities, domain=pyo.Reals,
                      bounds=(params["position_lower"], params["position_upper"]))

    # Objective: minimize total travel cost
    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)]
                   for i in cities for j in cities if i != j)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city departed exactly once
    def depart_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1
    model.depart = pyo.Constraint(cities, rule=depart_rule)

    # Each city entered exactly once
    def arrive_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1
    model.arrive = pyo.Constraint(cities, rule=arrive_rule)

    # Fix root position
    model.root_pos = pyo.Constraint(expr=model.u[0] == params["position_lower"])

    # Subtour elimination (MTZ)
    def mtz_rule(m, i, j):
        if i != j and i != 0 and j != 0:
            return m.u[i] - m.u[j] + n * m.x[(i, j)] <= n - 1
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint([(i, j) for i in cities for j in cities if i != j],
                               rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}