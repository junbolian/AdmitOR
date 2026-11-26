# IR: {"sets":{"I":[1,2,3,4,5],"T":[1,2,3,4,5,6],"A":"(i,t) in I x T with t>=3 if i=1 and t>=2 if i=4","L":[[3,4],[3,5],[4,5]]},"params":{"D":"params['D'][i], nonnegative integer demand","S":"params['S'][i], nonnegative selling price","C":"params['C'][i], nonnegative base unit cost","a":"params['a'][i], positive hours per unit","H":"params['normal_hours'][t], nonnegative normal capacity","O":"params['max_overtime_hours'][t], nonnegative overtime capacity","CP":"params['overtime_cost_premium'][i], nonnegative overtime unit premium","p3":"params['penalty_p3'], nonnegative monthly completion-delay penalty","p4":"params['penalty_p4'], nonnegative monthly completion-delay penalty"},"variables":{"x[i,t]":"nonnegative integer normal units for (i,t) in A","y[i,t]":"nonnegative integer overtime units for (i,t) in A","late[i,t]":"binary unfinished-order indicator for (i,t) in L"},"constraints":["For each i: sum_{t:(i,t) in A}(x[i,t]+y[i,t])=D[i].","For each t: sum_{i:(i,t) in A}a[i]*x[i,t]<=H[t].","For each t: sum_{i:(i,t) in A}a[i]*y[i,t]<=O[t].","For each (i,t) in L: sum_{s<=t:(i,s) in A}(x[i,s]+y[i,s])>=D[i]*(1-late[i,t]).","For each (i,t) in L: sum_{s<=t:(i,s) in A}(x[i,s]+y[i,s])<=D[i]-late[i,t]."],"objective":"maximize sum_i S[i]*D[i]-sum_{(i,t) in A}(C[i]*(x[i,t]+y[i,t])+CP[i]*y[i,t])-p3*(late[3,4]+late[3,5])-p4*late[4,5]","input_validation":"Return missing_parameters if a required top-level key is absent; do not invent omitted product data."}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Build and solve the production-planning MILP.

    Required product mappings, keyed by integers 1 through 5:
        D, S, C, a, overtime_cost_premium

    Required month mappings, keyed by integers 1 through 6:
        normal_hours, max_overtime_hours

    Required scalars:
        penalty_p3, penalty_p4

    The supplied problem omits numerical values for D, S, C, and a.
    An objective cannot be computed from the five listed parameters alone.
    Missing required inputs therefore produce a failure result rather than
    a KeyError or an objective based on fabricated data.

    Assumptions:
        Production quantities are integer units.
        Production can be delivered immediately.
        Delay penalties apply per unfinished product order per month.
        Products 3 and 4 may finish late, but all orders finish by June.
    """
    required_keys = (
        "D",
        "S",
        "C",
        "a",
        "normal_hours",
        "max_overtime_hours",
        "overtime_cost_premium",
        "penalty_p3",
        "penalty_p4",
    )
    if any(key not in params for key in required_keys):
        return {"objective": None, "status": "missing_parameters"}

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=range(1, 6), ordered=True)
    model.months = pyo.Set(initialize=range(1, 7), ordered=True)
    model.production_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (product, month)
            for product in range(1, 6)
            for month in range(1, 7)
            if (product != 1 or month >= 3)
            and (product != 4 or month >= 2)
        ],
        ordered=True,
    )
    model.delay_pairs = pyo.Set(
        dimen=2,
        initialize=[(3, 4), (3, 5), (4, 5)],
        ordered=True,
    )

    model.order_quantity = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["D"][product],
        within=pyo.NonNegativeIntegers,
    )
    model.selling_price = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["S"][product],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["C"][product],
        within=pyo.NonNegativeReals,
    )
    model.hours_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["a"][product],
        within=pyo.PositiveReals,
    )
    model.normal_capacity = pyo.Param(
        model.months,
        initialize=lambda mdl, month: params["normal_hours"][month],
        within=pyo.NonNegativeReals,
    )
    model.overtime_capacity = pyo.Param(
        model.months,
        initialize=lambda mdl, month: params["max_overtime_hours"][month],
        within=pyo.NonNegativeReals,
    )
    model.overtime_premium = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["overtime_cost_premium"][product],
        within=pyo.NonNegativeReals,
    )
    model.delay_penalty_p3 = pyo.Param(
        initialize=params["penalty_p3"],
        within=pyo.NonNegativeReals,
    )
    model.delay_penalty_p4 = pyo.Param(
        initialize=params["penalty_p4"],
        within=pyo.NonNegativeReals,
    )

    model.normal_units = pyo.Var(
        model.production_pairs, domain=pyo.NonNegativeIntegers
    )
    model.overtime_units = pyo.Var(
        model.production_pairs, domain=pyo.NonNegativeIntegers
    )
    model.late = pyo.Var(model.delay_pairs, domain=pyo.Binary)

    def contract_rule(mdl, product):
        return sum(
            mdl.normal_units[product, month]
            + mdl.overtime_units[product, month]
            for month in mdl.months
            if (product, month) in mdl.production_pairs
        ) == mdl.order_quantity[product]

    model.contract_completion = pyo.Constraint(
        model.products, rule=contract_rule
    )

    def normal_hours_rule(mdl, month):
        return sum(
            mdl.hours_per_unit[product] * mdl.normal_units[product, month]
            for product in mdl.products
            if (product, month) in mdl.production_pairs
        ) <= mdl.normal_capacity[month]

    model.normal_hours_limit = pyo.Constraint(
        model.months, rule=normal_hours_rule
    )

    def overtime_hours_rule(mdl, month):
        return sum(
            mdl.hours_per_unit[product] * mdl.overtime_units[product, month]
            for product in mdl.products
            if (product, month) in mdl.production_pairs
        ) <= mdl.overtime_capacity[month]

    model.overtime_hours_limit = pyo.Constraint(
        model.months, rule=overtime_hours_rule
    )

    def completed_by(mdl, product, month):
        return sum(
            mdl.normal_units[product, earlier_month]
            + mdl.overtime_units[product, earlier_month]
            for earlier_month in mdl.months
            if earlier_month <= month
            and (product, earlier_month) in mdl.production_pairs
        )

    def delay_lower_rule(mdl, product, month):
        return completed_by(mdl, product, month) >= (
            mdl.order_quantity[product] * (1 - mdl.late[product, month])
        )

    model.delay_completion_lower = pyo.Constraint(
        model.delay_pairs, rule=delay_lower_rule
    )

    def delay_upper_rule(mdl, product, month):
        return completed_by(mdl, product, month) <= (
            mdl.order_quantity[product] - mdl.late[product, month]
        )

    model.delay_completion_upper = pyo.Constraint(
        model.delay_pairs, rule=delay_upper_rule
    )

    model.profit = pyo.Objective(
        expr=(
            sum(
                model.selling_price[product] * model.order_quantity[product]
                for product in model.products
            )
            - sum(
                model.unit_cost[product]
                * (
                    model.normal_units[product, month]
                    + model.overtime_units[product, month]
                )
                + model.overtime_premium[product]
                * model.overtime_units[product, month]
                for product, month in model.production_pairs
            )
            - model.delay_penalty_p3
            * (model.late[3, 4] + model.late[3, 5])
            - model.delay_penalty_p4 * model.late[4, 5]
        ),
        sense=pyo.maximize,
    )

    solver_failure = None
    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        solver_failure = "solver_failed"

    # Objective retrieval alone determines success.
    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": solver_failure or "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}