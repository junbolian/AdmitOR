import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 10  # nodes 0..9, node 0 is depot
    K = int(params["num_vehicles"])  # number of vehicles
    customers = list(range(1, n))
    nodes = list(range(n))
    vehicles = list(range(K))

    # Build distance matrix from params
    D = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                D[(i, j)] = 0
            elif i < j:
                D[(i, j)] = D[(j, i)] = float(params[f"dist_{i}_{j}"])

    model = pyo.ConcreteModel()

    # Sets
    model.V = pyo.Set(initialize=nodes)
    model.C = pyo.Set(initialize=customers)
    model.K = pyo.Set(initialize=vehicles)
    model.A = pyo.Set(initialize=[(i, j, k) for i in nodes for j in nodes
                                  if i != j for k in vehicles])

    # Variables
    model.x = pyo.Var(model.A, domain=pyo.Binary)
    # MTZ order variables for subtour elimination
    model.u = pyo.Var(model.C, domain=pyo.NonNegativeReals,
                      bounds=(1, len(customers)))

    # Objective: minimize total travel distance
    def obj_rule(m):
        return sum(D[(i, j)] * m.x[i, j, k] for (i, j, k) in m.A)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once
    def visit_rule(m, j):
        return sum(m.x[i, j, k] for i in m.V if i != j
                   for k in m.K) == 1
    model.visit = pyo.Constraint(model.C, rule=visit_rule)

    # Each vehicle leaves the depot at most once
    def depart_rule(m, k):
        return sum(m.x[0, j, k] for j in m.C) <= 1
    model.depart = pyo.Constraint(model.K, rule=depart_rule)

    # Flow conservation for customers per vehicle
    def flow_rule(m, h, k):
        return (sum(m.x[i, h, k] for i in m.V if i != h)
                == sum(m.x[h, j, k] for j in m.V if j != h))
    model.flow = pyo.Constraint(model.C, model.K, rule=flow_rule)

    # Zero flow from depot into depot (not in A anyway)

    # MTZ subtour elimination
    def mtz_rule(m, i, j, k):
        if i == j:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + len(customers) * m.x[i, j, k] <= len(customers) - 1
    model.mtz = pyo.Constraint(model.C, model.C, model.K, rule=mtz_rule)

    # Solve
    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}