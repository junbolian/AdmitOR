import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    base_cost_type0 = params["base_cost_type0"]
    base_cost_type1 = params["base_cost_type1"]
    var_cost_type0 = params["var_cost_type0"]
    var_cost_type1 = params["var_cost_type1"]
    startup_cost_type0 = params["startup_cost_type0"]
    startup_cost_type1 = params["startup_cost_type1"]
    max_units_type0 = params["max_units_type0"]
    max_units_type1 = params["max_units_type1"]
    demand = params["demand"]
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    reserve_margin = params["reserve_margin"]
    max_startup_type0_period0 = params["max_startup_type0_period0"]
    max_startup_type1_period0 = params["max_startup_type1_period0"]

    periods = list(range(4))

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=periods, ordered=True)

    model.n0 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)
    model.n1 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)
    model.s0 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)
    model.s1 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)
    model.p0 = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.p1 = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    model.cap0 = pyo.Constraint(model.T, rule=lambda m, t: m.n0[t] <= max_units_type0)
    model.cap1 = pyo.Constraint(model.T, rule=lambda m, t: m.n1[t] <= max_units_type1)

    model.pmin0 = pyo.Constraint(model.T, rule=lambda m, t: m.p0[t] >= min_output_type0 * m.n0[t])
    model.pmax0 = pyo.Constraint(model.T, rule=lambda m, t: m.p0[t] <= max_output_type0 * m.n0[t])
    model.pmin1 = pyo.Constraint(model.T, rule=lambda m, t: m.p1[t] >= min_output_type1 * m.n1[t])
    model.pmax1 = pyo.Constraint(model.T, rule=lambda m, t: m.p1[t] <= max_output_type1 * m.n1[t])

    model.demand = pyo.Constraint(model.T, rule=lambda m, t: m.p0[t] + m.p1[t] >= demand[t])

    model.reserve = pyo.Constraint(
        model.T,
        rule=lambda m, t: max_output_type0 * m.n0[t] + max_output_type1 * m.n1[t]
        >= (1.0 + reserve_margin) * demand[t],
    )

    model.start0_p0 = pyo.Constraint(rule=lambda m: m.s0[0] <= max_startup_type0_period0)
    model.start1_p0 = pyo.Constraint(rule=lambda m: m.s1[0] <= max_startup_type1_period0)

    def start0_later(m, t):
        return m.s0[t] <= m.n0[t - 1]

    def start1_later(m, t):
        return m.s1[t] <= m.n1[t - 1]

    model.start0_later = pyo.Constraint(model.T, rule=lambda m, t: pyo.Constraint.Skip if t == 0 else m.s0[t] <= m.n0[t - 1])
    model.start1_later = pyo.Constraint(model.T, rule=lambda m, t: pyo.Constraint.Skip if t == 0 else m.s1[t] <= m.n1[t - 1])

    model.obj = pyo.Objective(
        expr=sum(
            base_cost_type0 * model.n0[t]
            + base_cost_type1 * model.n1[t]
            + var_cost_type0 * model.p0[t]
            + var_cost_type1 * model.p1[t]
            + startup_cost_type0 * model.s0[t]
            + startup_cost_type1 * model.s1[t]
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}