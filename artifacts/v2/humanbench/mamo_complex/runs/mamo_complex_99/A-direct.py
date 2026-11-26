import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4, 5]
    src = 0
    sink = 5

    # All directed arcs present in the network (per the listed capacities)
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 5),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    ]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    # Max-flow: maximize net outflow from source, subject to conservation
    # at all intermediate nodes and capacity bounds.
    def flow_bounds_rule(m, i, j):
        return (0.0, params["capacity_{0}_{1}".format(i, j)])

    model.flow = pyo.Var(model.arcs, bounds=flow_bounds_rule)

    def outflow_rule(m, k):
        return sum(m.flow[k, j] for (i, j) in arcs if i == k)

    def inflow_rule(m, k):
        return sum(m.flow[i, k] for (i, j) in arcs if j == k)

    def conservation_rule(m, k):
        if k == src or k == sink:
            return pyo.Constraint.Skip
        return outflow_rule(m, k) - inflow_rule(m, k) == 0

    model.conservation = pyo.Constraint(nodes, rule=conservation_rule)

    model.objective = pyo.Objective(
        expr=outflow_rule(model, src) - inflow_rule(model, src),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}