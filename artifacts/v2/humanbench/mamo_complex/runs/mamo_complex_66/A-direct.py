import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Symmetric travel costs read from params
    cost_map = {
        (1, 2): params["c12"], (1, 3): params["c13"], (1, 4): params["c14"],
        (1, 5): params["c15"], (1, 6): params["c16"],
        (2, 3): params["c23"], (2, 4): params["c24"], (2, 5): params["c25"],
        (2, 6): params["c26"],
        (3, 4): params["c34"], (3, 5): params["c35"], (3, 6): params["c36"],
        (4, 5): params["c45"], (4, 6): params["c46"],
        (5, 6): params["c56"],
    }

    nodes = [1, 2, 3, 4, 5, 6]
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def arc_cost(i, j):
        key = (i, j) if i < j else (j, i)
        return cost_map[key]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    # Objective: minimize total travel cost
    model.total_cost = pyo.Objective(
        expr=sum(arc_cost(i, j) * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Degree constraints: each city entered once and left once
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in nodes if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in nodes if i != j) == 1

    model.out_cons = pyo.Constraint(model.N, rule=out_rule)
    model.in_cons = pyo.Constraint(model.N, rule=in_rule)

    # Subtour elimination (MTZ). Fix city 1 as depot (u[1] = 0),
    # other cities get u in [1, 5].
    model.u = pyo.Var(model.N, domain=pyo.Reals)

    def u_fix(mdl, i):
        if i == 1:
            return mdl.u[i] == 0
        return pyo.Constraint.Skip

    model.u_fix_cons = pyo.Constraint(model.N, rule=u_fix)

    def u_bound_rule(mdl, i):
        if i == 1:
            return pyo.Constraint.Skip
        return pyo.inequality(1, mdl.u[i], 5)

    model.u_bounds = pyo.Constraint(model.N, rule=u_bound_rule)

    def mtz_rule(mdl, i, j):
        if i != 1 and j != 1 and i != j:
            return mdl.u[i] - mdl.u[j] + 6 * mdl.x[i, j] <= 5
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(model.A, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}