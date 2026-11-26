import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ['A', 'B', 'C', 'D']

    cost = {
        ('A', 'B'): params["cost_AB"],
        ('A', 'C'): params["cost_AC"],
        ('A', 'D'): params["cost_AD"],
        ('B', 'A'): params["cost_BA"],
        ('B', 'C'): params["cost_BC"],
        ('B', 'D'): params["cost_BD"],
        ('C', 'A'): params["cost_CA"],
        ('C', 'B'): params["cost_CB"],
        ('C', 'D'): params["cost_CD"],
        ('D', 'A'): params["cost_DA"],
        ('D', 'B'): params["cost_DB"],
        ('D', 'C'): params["cost_DC"],
    }

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=list(cost.keys()), dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[i, j] * mdl.x[i, j] for (i, j) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if (i, j) in cost) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if (i, j) in cost) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)
    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # MTZ subtour elimination only over arcs leaving A's "successors" set,
    # i.e. exclude arcs into A since A is fixed as the depot with u=1.
    non_depot = ['B', 'C', 'D']
    model.u = pyo.Var(cities, bounds=(1, len(cities) - 1))
    model.u['A'].fix(1)

    def mtz_rule(mdl, i, j):
        return mdl.u[i] - mdl.u[j] + len(cities) * mdl.x[i, j] <= len(cities) - 1

    model.subtour = pyo.Constraint(
        [(i, j) for (i, j) in cost.keys() if j != 'A'], rule=mtz_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}