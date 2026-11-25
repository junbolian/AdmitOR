import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3]
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    dist = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                dist[(i, j)] = params["dist_%d_%d" % (i, j)]

    bigM = params["bigM"]
    num_selected = params["num_selected"]

    model = pyo.ConcreteModel()

    model.Nodes = pyo.Set(initialize=nodes)
    model.Pairs = pyo.Set(initialize=pairs, dimen=2)

    model.Select = pyo.Var(model.Nodes, domain=pyo.Binary)
    model.PairSelect = pyo.Var(model.Pairs, domain=pyo.Binary)
    model.MinDistance = pyo.Var(domain=pyo.NonNegativeReals)

    def total_facilities_rule(mdl):
        return sum(mdl.Select[i] for i in mdl.Nodes) == num_selected

    model.TotalFacilities = pyo.Constraint(rule=total_facilities_rule)

    def pair_ub_i_rule(mdl, i, j):
        return mdl.PairSelect[i, j] <= mdl.Select[i]

    def pair_ub_j_rule(mdl, i, j):
        return mdl.PairSelect[i, j] <= mdl.Select[j]

    def pair_lb_rule(mdl, i, j):
        return mdl.PairSelect[i, j] >= mdl.Select[i] + mdl.Select[j] - 1

    model.PairUBI = pyo.Constraint(model.Pairs, rule=pair_ub_i_rule)
    model.PairUBJ = pyo.Constraint(model.Pairs, rule=pair_ub_j_rule)
    model.PairLB = pyo.Constraint(model.Pairs, rule=pair_lb_rule)

    def distance_rule(mdl, i, j):
        return mdl.MinDistance <= dist[(i, j)] + bigM * (1 - mdl.PairSelect[i, j])

    model.DistanceConstraint = pyo.Constraint(model.Pairs, rule=distance_rule)

    def objective_rule(mdl):
        return mdl.MinDistance

    model.Objective = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.Objective))
    return {"objective": obj_val, "status": "optimal"}