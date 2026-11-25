import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_nodes = len(cost_matrix)
    nodes = list(range(num_nodes))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j], dimen=2
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.nodes, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j] for (i, j) in model.arcs),
        sense=pyo.minimize,
    )

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.nodes if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.nodes if i != j) == 1

    model.out_degree = pyo.Constraint(model.nodes, rule=out_rule)
    model.in_degree = pyo.Constraint(model.nodes, rule=in_rule)

    def mt_run(mdl, i, j):
        if i != 0 and j != 0 and i != j:
            return mdl.u[i] - mdl.u[j] + (num_nodes - 1) * mdl.x[i, j] <= num_nodes - 2
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(model.arcs, rule=mt_run)

    model.u[0].setlb(0)
    model.u[0].setub(0)
    for k in nodes:
        if k != 0:
            model.u[k].setlb(1)
            model.u[k].setub(num_nodes - 1)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}