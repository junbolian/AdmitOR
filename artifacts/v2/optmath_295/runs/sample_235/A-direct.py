import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_emp = len(params["employee_availability"])
    n_proj = len(params["project_requirement"])

    model = pyo.ConcreteModel()

    model.emp = pyo.RangeSet(0, n_emp - 1)
    model.proj = pyo.RangeSet(0, n_proj - 1)

    model.hours = pyo.Var(model.emp, model.proj, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            params["assignment_cost"][i][j] * mdl.hours[i, j]
            for i in range(n_emp)
            for j in range(n_proj)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.emp_supply = pyo.Constraint(
        model.emp,
        rule=lambda mdl, i: sum(mdl.hours[i, j] for j in range(n_proj))
        == params["employee_availability"][i],
    )

    model.proj_demand = pyo.Constraint(
        model.proj,
        rule=lambda mdl, j: sum(mdl.hours[i, j] for i in range(n_emp))
        == params["project_requirement"][j],
    )

    model.pair_cap = pyo.Constraint(
        model.emp,
        model.proj,
        rule=lambda mdl, i, j: mdl.hours[i, j]
        <= params["per_assignment_capacity"][i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}