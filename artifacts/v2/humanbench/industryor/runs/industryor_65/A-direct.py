import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: production quantities
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)

    # Parameter values from params
    mh_A = params["man_hours_A"]
    mh_B = params["man_hours_B"]
    ah_A = params["asm_hours_A"]
    ah_B = params["asm_hours_B"]
    ih_A = params["insp_hours_A"]
    ih_B = params["insp_hours_B"]
    pA = params["price_A"]
    pB = params["price_B"]
    cap_m = params["cap_manufacturing"]
    cap_a = params["cap_assembly"]
    cap_i = params["cap_inspection"]
    c_m = params["cost_manufacturing"]
    c_a = params["cost_assembly"]
    c_i = params["cost_inspection"]
    profit_goal = params["profit_goal"]
    min_A_goal = params["min_A_goal"]

    # Deviational variables (unrestricted in sign for over/under as needed)
    # p1: profit shortfall (want to minimize undershoot); overachievement also allowed
    model.d1_minus = pyo.Var(domain=pyo.NonNegativeReals)  # underachievement of profit
    model.d1_plus = pyo.Var(domain=pyo.NonNegativeReals)   # overachievement of profit

    # p2: Type A production shortfall
    model.d2_minus = pyo.Var(domain=pyo.NonNegativeReals)  # underachievement of min A
    model.d2_plus = pyo.Var(domain=pyo.NonNegativeReals)   # overachievement of min A

    # p3: idle time per process (slack), minimized with cost-proportional weights
    model.s_m = pyo.Var(domain=pyo.NonNegativeReals)
    model.s_a = pyo.Var(domain=pyo.NonNegativeReals)
    model.s_i = pyo.Var(domain=pyo.NonNegativeReals)

    # Profit expression: revenue - operating costs
    profit_expr = (pA * model.xA + pB * model.xB
                   - c_m * (mh_A * model.xA + mh_B * model.xB)
                   - c_a * (ah_A * model.xA + ah_B * model.xB)
                   - c_i * (ih_A * model.xA + ih_B * model.xB))

    # Goal p1: profit + d1_minus - d1_plus = profit_goal
    model.goal_profit = pyo.Constraint(
        expr=profit_expr + model.d1_minus - model.d1_plus == profit_goal
    )

    # Goal p2: xA + d2_minus - d2_plus = min_A_goal
    model.goal_min_A = pyo.Constraint(
        expr=model.xA + model.d2_minus - model.d2_plus == min_A_goal
    )

    # p3: idle time (slack) constraints; no overtime allowed
    model.cap_man = pyo.Constraint(
        expr=mh_A * model.xA + mh_B * model.xB + model.s_m == cap_m
    )
    model.cap_asm = pyo.Constraint(
        expr=ah_A * model.xA + ah_B * model.xB + model.s_a == cap_a
    )
    model.cap_insp = pyo.Constraint(
        expr=ih_A * model.xA + ih_B * model.xB + model.s_i == cap_i
    )

    # Lexicographic priority weights via large constants.
    # Priorities: p1 >> p2 >> p3 (idle terms weighted by hourly costs).
    BIG1 = 1e6
    BIG2 = 1e3

    model.objective = pyo.Objective(
        expr=(
            BIG1 * model.d1_minus
            + BIG2 * model.d2_minus
            + c_m * model.s_m
            + c_a * model.s_a
            + c_i * model.s_i
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}