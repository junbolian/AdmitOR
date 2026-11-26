import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = ["A", "B", "C", "D", "E", "F"]

    cost_data = {
        ("A", "B"): params["cost_AB"],
        ("A", "C"): params["cost_AC"],
        ("A", "D"): params["cost_AD"],
        ("A", "E"): params["cost_AE"],
        ("A", "F"): params["cost_AF"],
        ("B", "C"): params["cost_BC"],
        ("B", "D"): params["cost_BD"],
        ("B", "E"): params["cost_BE"],
        ("B", "F"): params["cost_BF"],
        ("C", "D"): params["cost_CD"],
        ("C", "E"): params["cost_CE"],
        ("C", "F"): params["cost_CF"],
        ("D", "E"): params["cost_DE"],
        ("D", "F"): params["cost_DF"],
        ("E", "F"): params["cost_EF"],
    }

    def sym_cost(i, j):
        return cost_data[(i, j)] if (i, j) in cost_data else cost_data[(j, i)]

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.dim_nodes = pyo.Set(initialize=nodes)
    model.dim_arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.dim_arcs, domain=pyo.Binary)

    model.total_cost = pyo.Objective(
        expr=sum(sym_cost(i, j) * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in nodes if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in nodes if i != j) == 1

    model.out_con = pyo.Constraint(model.dim_nodes, rule=out_rule)
    model.in_con = pyo.Constraint(model.dim_nodes, rule=in_rule)

    model.order = pyo.Var(model.dim_nodes, bounds=(1, len(nodes)))

    def mtz_rule(mdl, i, j):
        if i != j and i != nodes[0] and j != nodes[0]:
            return mdl.order[i] - mdl.order[j] + len(nodes) * mdl.x[i, j] <= len(nodes) - 1
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(model.dim_arcs, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}