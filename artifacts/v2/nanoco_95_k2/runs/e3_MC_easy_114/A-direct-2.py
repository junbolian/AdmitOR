import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    source = int(params["source"])
    sink_node = int(params["sink"])
    arcs = params["arcs"]
    arc_unit_costs = params["arc_unit_costs"]

    nodes = list(range(num_nodes))
    arc_list = [(int(a[0]), int(a[1])) for a in arcs]

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=arc_list, dimen=2)

    model.x = pyo.Var(model.V, within=pyo.Binary)

    def cut_cost_rule(m):
        return sum(arc_unit_costs[k] * (m.x[i] - m.x[j])
                   for k, (i, j) in enumerate(arc_list))
    model.cut_cost = pyo.Expression(rule=cut_cost_rule)

    model.obj = pyo.Objective(expr=model.cut_cost, sense=pyo.minimize)

    model.src_fix = pyo.Constraint(expr=model.x[source] == 1)
    model.snk_fix = pyo.Constraint(expr=model.x[sink_node] == 0)

    # Feasibility re-fix source/sink at solution (redundant guard for solver)
    model.src_lo = pyo.Constraint(expr=model.x[source] >= 1)
    model.snk_hi = pyo.Constraint(expr=model.x[sink_node] <= 0)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}