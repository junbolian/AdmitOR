import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    arcs = params["arcs"]
    arc_unit_costs = params["arc_unit_costs"]

    nodes = list(range(num_nodes))
    arc_list = [tuple(a) for a in arcs]

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(initialize=arc_list, dimen=2)

    # y[v] = 1 if v in source set S, 0 if in sink set T
    model.y = pyo.Var(model.V, domain=pyo.Binary)

    # Fix source in S and sink in T
    model.y[source].fix(1)
    model.y[sink].fix(0)

    def cut_cost_rule(m):
        return sum(
            arc_unit_costs[k] * (m.y[i] - m.y[j])
            for k, (i, j) in enumerate(arc_list)
        )

    model.cut_cost = pyo.Objective(rule=cut_cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cut_cost))
    return {"objective": obj_val, "status": "optimal"}