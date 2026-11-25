import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    # Index sets
    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.customers = pyo.RangeSet(1, num_nodes - 1)

    # Binary arc variables: x[i, j] = 1 if truck travels from i to j
    model.x = pyo.Var(model.nodes, model.nodes, domain=pyo.Binary)

    # Objective: minimize total distance
    def obj_rule(mdl):
        return sum(
            distance_matrix[i][j] * mdl.x[i, j]
            for i in mdl.nodes
            for j in mdl.nodes
            if i != j
        )

    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.nodes if j != i) == 1

    model.out_flow = pyo.Constraint(model.nodes, rule=out_rule)

    # Each node has exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.nodes if i != j) == 1

    model.in_flow = pyo.Constraint(model.nodes, rule=in_rule)

    # Subtour elimination via MTZ: order variables for customer nodes
    model.u = pyo.Var(model.customers, domain=pyo.NonNegativeReals, bounds=(1, num_nodes - 1))

    def mtz_rule(mdl, i, j):
        if i != j and i >= 1 and j >= 1:
            return mdl.u[i] - mdl.u[j] + (num_nodes - 1) * mdl.x[i, j] <= num_nodes - 2
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(model.nodes, model.nodes, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}