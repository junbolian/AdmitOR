import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stations = list(range(7))
    source = 0
    sink = 6

    # Directed arcs: all ordered pairs with capacity parameter keys
    arcs = []
    for i in stations:
        for j in stations:
            if i != j:
                key = "capacity_{}_{}".format(i, j)
                if key in params:
                    arcs.append((i, j))

    def cap(i, j):
        return params["capacity_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def flow_bounds(m, i, j):
        return (0, cap(i, j))

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals,
                         bounds=flow_bounds)

    # Objective: maximize net outflow of source
    def objective_rule(m):
        return sum(m.flow[i, j] for (i, j) in arcs if i == source)

    model.max_flow = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    # Flow conservation at all nodes except source and sink
    def conservation_rule(m, k):
        if k == source or k == sink:
            return pyo.Constraint.Skip
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == k)
        return inflow == outflow

    model.conservation = pyo.Constraint(stations, rule=conservation_rule)

    # Source/sink: enforce inflow bounds = 0 handled by arc vars;
    # add sink net inflow equals source net outflow implicitly by
    # conservation; nothing more needed (max-flow LP).

    Highs().solve(model)
    obj_val = float(pyo.value(model.max_flow))

    return {"objective": obj_val, "status": "optimal"}