import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = [0, 1, 2, 3, 4]

    model.x = pyo.Var(nodes, domain=pyo.Binary, bounds=(0, 1))

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def interaction_coef(i, j):
        return params[f"interaction_score_{i}_{j}"]

    model.z = pyo.Var(arcs, domain=pyo.Binary, bounds=(0, 1))

    def obj_rule(mdl):
        return sum(interaction_coef(i, j) * mdl.z[i, j] for (i, j) in arcs)

    model.total_benefit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.pick_exactly_two = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == 2
    )

    def link_up_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.x[i]

    def link_down_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.x[j]

    def link_strong_rule(mdl, i, j):
        return mdl.z[i, j] >= mdl.x[i] + mdl.x[j] - 1

    model.link_i = pyo.Constraint(arcs, rule=link_up_rule)
    model.link_j = pyo.Constraint(arcs, rule=link_down_rule)
    model.link_both = pyo.Constraint(arcs, rule=link_strong_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_benefit))
    return {"objective": obj_val, "status": "optimal"}