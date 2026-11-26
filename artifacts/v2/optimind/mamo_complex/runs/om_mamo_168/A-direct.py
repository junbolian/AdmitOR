import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = ["E", "F", "G", "H", "I"]

    cost = {
        ("E", "F"): params["cost_E_to_F"],
        ("E", "G"): params["cost_E_to_G"],
        ("E", "H"): params["cost_E_to_H"],
        ("E", "I"): params["cost_E_to_I"],
        ("F", "E"): params["cost_F_to_E"],
        ("F", "G"): params["cost_F_to_G"],
        ("F", "H"): params["cost_F_to_H"],
        ("F", "I"): params["cost_F_to_I"],
        ("G", "E"): params["cost_G_to_E"],
        ("G", "F"): params["cost_G_to_F"],
        ("G", "H"): params["cost_G_to_H"],
        ("G", "I"): params["cost_G_to_I"],
        ("H", "E"): params["cost_H_to_E"],
        ("H", "F"): params["cost_H_to_F"],
        ("H", "G"): params["cost_H_to_G"],
        ("H", "I"): params["cost_H_to_I"],
        ("I", "E"): params["cost_I_to_E"],
        ("I", "F"): params["cost_I_to_F"],
        ("I", "G"): params["cost_I_to_G"],
        ("I", "H"): params["cost_I_to_H"],
    }

    model = pyo.ConcreteModel()
    model.LOCS = pyo.Set(initialize=locations)
    model.ARCS = pyo.Set(initialize=[(i, j) for i in locations for j in locations if i != j])

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[i, j] for (i, j) in m.ARCS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in m.LOCS if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[i, j] for i in m.LOCS if i != j) == 1

    model.out_cons = pyo.Constraint(model.LOCS, rule=out_rule)
    model.in_cons = pyo.Constraint(model.LOCS, rule=in_rule)

    # MTZ subtour elimination: order vars u_i in [1, n-1].
    # u_i - u_j + n*x_ij <= n-1 for all i != j.
    # Fix order of the first node only (symmetry breaking).
    n = len(locations)
    root = locations[0]
    model.u = pyo.Var(model.LOCS, bounds=(1, n - 1))
    model.u[root].fix(1)

    def mtz_rule(m, i, j):
        if i == j:
            return pyo.Constraint.Skip
        if i == root:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1

    model.mtz = pyo.Constraint(model.LOCS, model.LOCS, rule=mtz_rule)

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}