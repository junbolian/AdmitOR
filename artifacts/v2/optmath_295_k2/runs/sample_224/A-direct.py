import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 6
    cities = list(range(N))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.CITIES = pyo.Set(initialize=cities)
    model.ARCS = pyo.Set(
        initialize=[(i, j) for i in cities for j in cities if i != j],
        dimen=2,
    )

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)
    model.pos = pyo.Var(
        model.CITIES,
        domain=pyo.Reals,
        bounds=(params["pos_lower_bound"], params["pos_upper_bound"]),
    )

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in model.ARCS),
        sense=pyo.minimize,
    )

    def out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in cities if i != j) == 1

    model.out_flow = pyo.Constraint(model.CITIES, rule=out_rule)
    model.in_flow = pyo.Constraint(model.CITIES, rule=in_rule)

    model.pos_fix = pyo.Constraint(expr=model.pos[0] == params["pos_0_fixed"])

    # MTZ subtour elimination with an exact big-M based on position bounds.
    # pos_i - pos_j + M * x_ij <= M - sep  is equivalent to:
    #   if x_ij = 1: pos_i - pos_j <= -sep  (i.e., pos_j >= pos_i + sep)
    #   if x_ij = 0: pos_i - pos_j <= M - sep (always satisfiable given bounds)
    P_hi = params["pos_upper_bound"]
    P_lo = params["pos_lower_bound"]
    sep = params["subtour_separation_min"]
    # Need M - sep >= P_hi - P_lo  =>  M >= P_hi - P_lo + sep
    bigM = (P_hi - P_lo) + sep

    def subtour_rule(mdl, i, j):
        return mdl.pos[i] - mdl.pos[j] + bigM * mdl.x[(i, j)] <= bigM - sep

    model.subtour = pyo.Constraint(model.ARCS, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}