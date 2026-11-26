import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cap = params["cap"]
    n = params["n_nodes"]
    source = params["source"]
    sink = params["sink"]

    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j and cap[i][j] > 0]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    def flow_bounds(mdl, i, j):
        return (0.0, float(cap[i][j]))

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals, bounds=flow_bounds)

    def conservation_rule(mdl, k):
        out_flow = sum(mdl.flow[i, j] for (i, j) in arcs if i == k)
        in_flow = sum(mdl.flow[i, j] for (i, j) in arcs if j == k)
        if k == source:
            return out_flow - in_flow >= 0
        elif k == sink:
            return in_flow - out_flow >= 0
        else:
            return out_flow - in_flow == 0

    model.conservation = pyo.Constraint(model.nodes, rule=conservation_rule)

    def objective_rule(mdl):
        return sum(mdl.flow[i, j] for (i, j) in arcs if i == source)

    model.total_flow = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}