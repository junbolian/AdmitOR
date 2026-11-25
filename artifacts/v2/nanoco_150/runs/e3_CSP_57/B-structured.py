# IR: {"sets":{"I":"{0,1,2}","B":"{0,...,sum(q[i] for i in I)-1}"},"params":{"W":"params['master_width']","q":"params['order_quantities'] indexed by I","w":"params['finished_widths'] indexed by I"},"variables":{"used[b]":"binary for b in B","cuts[i,b]":"nonnegative integer, upper bound q[i], for i in I and b in B"},"constraints":["For each i in I: sum(cuts[i,b] for b in B) = q[i]","For each b in B: sum(w[i]*cuts[i,b] for i in I) <= W*used[b]"],"objective":"minimize sum(used[b] for b in B)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    master_width = params["master_width"]
    order_quantities = params["order_quantities"]
    finished_widths = params["finished_widths"]

    model = pyo.ConcreteModel()
    model.specifications = pyo.Set(initialize=range(3), ordered=True)
    model.master_rolls = pyo.Set(
        initialize=range(sum(order_quantities)), ordered=True
    )

    model.used = pyo.Var(model.master_rolls, domain=pyo.Binary)
    model.cuts = pyo.Var(
        model.specifications,
        model.master_rolls,
        domain=pyo.NonNegativeIntegers,
        bounds=lambda mdl, specification, roll: (
            0,
            order_quantities[specification],
        ),
    )

    def demand_rule(mdl, specification):
        return (
            pyo.quicksum(
                mdl.cuts[specification, roll] for roll in mdl.master_rolls
            )
            == order_quantities[specification]
        )

    model.exact_demand = pyo.Constraint(
        model.specifications, rule=demand_rule
    )

    def capacity_rule(mdl, roll):
        return (
            pyo.quicksum(
                finished_widths[specification] * mdl.cuts[specification, roll]
                for specification in mdl.specifications
            )
            <= master_width * mdl.used[roll]
        )

    model.width_capacity = pyo.Constraint(
        model.master_rolls, rule=capacity_rule
    )

    model.total_master_rolls = pyo.Objective(
        expr=pyo.quicksum(model.used[roll] for roll in model.master_rolls),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_master_rolls))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}