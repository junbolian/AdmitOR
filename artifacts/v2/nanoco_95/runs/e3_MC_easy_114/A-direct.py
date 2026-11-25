import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    source = int(params["source"])
    sink = int(params["sink"])
    arc_cap_list = list(params["arc_capacities"])
    arc_cost_list = list(params["arc_unit_costs"])

    # Topology is structural (frozen arc list given in problem)
    arcs = [[0, 1], [1, 2], [1, 4], [1, 5], [1, 7], [2, 3], [3, 4],
            [4, 5], [4, 8], [4, 9], [5, 6], [5, 7], [6, 7], [7, 8], [8, 9]]

    model = pyo.ConcreteModel()
    model.NODES = pyo.Set(initialize=list(range(num_nodes)))
    model.A = pyo.Set(initialize=list(range(len(arcs))))

    model.z = pyo.Var(model.NODES, domain=pyo.Binary)

    def cross_rule(m, a):
        u, v = arcs[a]
        return m.z[u] - m.z[v]

    model.crossvar = pyo.Var(model.A, domain=pyo.Binary)
    model.cross_expr = pyo.Expression(model.A, rule=cross_rule)

    def obj_rule(m):
        return sum(arc_cost_list[a] * m.crossvar[a] for a in m.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Linearize: crossvar >= z_u - z_v and crossvar >= 0 (since z in {0,1}, z_u - z_v in {-1,0,1})
    def lin1(m, a):
        u, v = arcs[a]
        return m.crossvar[a] >= m.z[u] - m.z[v]

    model.link = pyo.Constraint(model.A, rule=lin1)

    model.src_fix = pyo.Constraint(expr=model.z[source] == 1)
    model.snk_fix = pyo.Constraint(expr=model.z[sink] == 0)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}