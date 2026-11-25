# IR: {"sets":{"V":"range(params['num_variables'])","R":"range(params['num_variables'])","E":"[tuple(pair) for pair in params['interference_pairs']]"},"params":{"num_variables":"number of variables and candidate registers","interference_pairs":"pairs of interfering variables"},"decision_variables":{"assigned[v,r]":"Binary, v in V and r in R","register_used[r]":"Binary, r in R"},"constraints":["For each v in V: sum(assigned[v,r] for r in R) == 1","For each (u,v) in E and r in R: assigned[u,r] + assigned[v,r] <= 1","For each v in V and r in R: assigned[v,r] <= register_used[r]"],"objective":"Minimize sum(register_used[r] for r in R)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_variables = params["num_variables"]
    interference_pairs = [
        tuple(pair) for pair in params["interference_pairs"]
    ]

    model = pyo.ConcreteModel()

    model.variables_set = pyo.Set(
        initialize=range(num_variables),
        ordered=True,
    )
    model.registers_set = pyo.Set(
        initialize=range(num_variables),
        ordered=True,
    )
    model.interference_set = pyo.Set(
        dimen=2,
        initialize=interference_pairs,
        within=model.variables_set * model.variables_set,
    )

    model.assigned = pyo.Var(
        model.variables_set,
        model.registers_set,
        domain=pyo.Binary,
    )
    model.register_used = pyo.Var(
        model.registers_set,
        domain=pyo.Binary,
    )

    def assignment_rule(mdl, variable):
        return sum(
            mdl.assigned[variable, register]
            for register in mdl.registers_set
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.variables_set,
        rule=assignment_rule,
    )

    def interference_rule(mdl, first, second, register):
        return (
            mdl.assigned[first, register]
            + mdl.assigned[second, register]
            <= 1
        )

    model.interference_constraints = pyo.Constraint(
        model.interference_set,
        model.registers_set,
        rule=interference_rule,
    )

    def usage_rule(mdl, variable, register):
        return (
            mdl.assigned[variable, register]
            <= mdl.register_used[register]
        )

    model.usage_constraints = pyo.Constraint(
        model.variables_set,
        model.registers_set,
        rule=usage_rule,
    )

    model.register_count_objective = pyo.Objective(
        expr=sum(
            model.register_used[register]
            for register in model.registers_set
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.register_count_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}