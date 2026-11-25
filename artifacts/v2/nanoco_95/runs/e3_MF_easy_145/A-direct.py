import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]

    # Fixed network structure: 14 channels (tail, head), channels 1..14 in order
    channels = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    ]
    arc_ids = list(range(len(channels)))
    intermediate_nodes = [1, 2, 3, 4, 5, 6, 7]
    source = 0
    sink = 8

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arc_ids)
    model.INTER = pyo.Set(initialize=intermediate_nodes)

    model.flow = pyo.Var(
        model.ARC, bounds=lambda mdl, a: (0.0, float(capacities[a]))
    )

    # Single objective: maximize net delivered volume at the sink
    def obj_rule(mdl):
        return sum(mdl.flow[a] for a in mdl.ARC if channels[a][1] == sink)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Flow conservation at intermediate nodes
    def conservation_rule(mdl, n):
        inflow = sum(mdl.flow[a] for a in mdl.ARC if channels[a][1] == n)
        outflow = sum(mdl.flow[a] for a in mdl.ARC if channels[a][0] == n)
        return inflow == outflow

    model.conservation = pyo.Constraint(model.INTER, rule=conservation_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}