import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow_matrix = params["flow_matrix"]
    distance_matrix = params["distance_matrix"]
    num_facilities = params["num_facilities"]
    num_locations = params["num_locations"]

    model = pyo.ConcreteModel()

    model.FAC = pyo.RangeSet(0, num_facilities - 1)
    model.LOC = pyo.RangeSet(0, num_locations - 1)

    model.x = pyo.Var(model.FAC, model.LOC, domain=pyo.Binary)

    def rack_assignment_rule(mdl, i):
        return sum(mdl.x[i, k] for k in mdl.LOC) == 1

    def slot_assignment_rule(mdl, k):
        return sum(mdl.x[i, k] for i in mdl.FAC) == 1

    model.rack_constraint = pyo.Constraint(model.FAC, rule=rack_assignment_rule)
    model.slot_constraint = pyo.Constraint(model.LOC, rule=slot_assignment_rule)

    def objective_rule(mdl):
        return sum(
            flow_matrix[i][j] * distance_matrix[k][l]
            * (mdl.x[i, k] * mdl.x[j, l] + mdl.x[i, l] * mdl.x[j, k])
            for i in mdl.FAC
            for j in mdl.FAC
            for k in mdl.LOC
            for l in mdl.LOC
            if i < j and k < l
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}