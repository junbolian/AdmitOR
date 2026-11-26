# IR: {"sets":{"products":["A","B"],"processes":["manuf","asm","insp"]},"params":["price_A","price_B","hours_manuf_A","hours_asm_A","hours_insp_A","hours_manuf_B","hours_asm_B","hours_insp_B","cap_manuf","cap_asm","cap_insp","cost_manuf","cost_asm","cost_insp","profit_target","min_A_target"],"variables":{"production[products]":"nonnegative_integer","idle[processes]":"nonnegative_real","profit_shortfall":"nonnegative_real","A_shortfall":"nonnegative_real"},"expressions":{"usage[s]":"sum(hours[s,t]*production[t] for t in products)","profit":"sum(price[t]*production[t] for t in products)-sum(cost[s]*usage[s] for s in processes)"},"constraints":["usage[s]+idle[s]=capacity[s] for each process s; nonnegative idle prohibits overtime","profit+profit_shortfall>=profit_target","production[A]+A_shortfall>=min_A_target","after priority 1, fix profit_shortfall to its optimal value","after priority 2, fix A_shortfall to its optimal value"],"objective":{"sense":"lexicographic_minimize","priorities":["profit_shortfall","A_shortfall","sum(cost[s]*idle[s] for s in processes)"],"returned_objective":"priority 3 weighted idle cost at the lexicographic optimum"}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the integer, preemptive goal-programming production model."""
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=("A", "B"), ordered=True)
    model.processes = pyo.Set(
        initialize=("manuf", "asm", "insp"), ordered=True
    )

    model.price = pyo.Param(
        model.products,
        initialize={
            "A": params["price_A"],
            "B": params["price_B"],
        },
    )
    model.hours = pyo.Param(
        model.processes,
        model.products,
        initialize={
            ("manuf", "A"): params["hours_manuf_A"],
            ("asm", "A"): params["hours_asm_A"],
            ("insp", "A"): params["hours_insp_A"],
            ("manuf", "B"): params["hours_manuf_B"],
            ("asm", "B"): params["hours_asm_B"],
            ("insp", "B"): params["hours_insp_B"],
        },
    )
    model.capacity = pyo.Param(
        model.processes,
        initialize={
            "manuf": params["cap_manuf"],
            "asm": params["cap_asm"],
            "insp": params["cap_insp"],
        },
    )
    model.hourly_cost = pyo.Param(
        model.processes,
        initialize={
            "manuf": params["cost_manuf"],
            "asm": params["cost_asm"],
            "insp": params["cost_insp"],
        },
    )
    model.profit_target = pyo.Param(initialize=params["profit_target"])
    model.min_A_target = pyo.Param(initialize=params["min_A_target"])

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeIntegers
    )
    model.idle = pyo.Var(model.processes, domain=pyo.NonNegativeReals)
    model.profit_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.A_shortfall = pyo.Var(domain=pyo.NonNegativeReals)

    def usage_rule(current_model, process):
        return sum(
            current_model.hours[process, product]
            * current_model.production[product]
            for product in current_model.products
        )

    model.usage = pyo.Expression(model.processes, rule=usage_rule)

    model.profit = pyo.Expression(
        expr=sum(
            model.price[product] * model.production[product]
            for product in model.products
        )
        - sum(
            model.hourly_cost[process] * model.usage[process]
            for process in model.processes
        )
    )
    model.weighted_idle = pyo.Expression(
        expr=sum(
            model.hourly_cost[process] * model.idle[process]
            for process in model.processes
        )
    )

    def capacity_balance_rule(current_model, process):
        return (
            current_model.usage[process] + current_model.idle[process]
            == current_model.capacity[process]
        )

    model.capacity_balance = pyo.Constraint(
        model.processes, rule=capacity_balance_rule
    )
    model.profit_goal = pyo.Constraint(
        expr=model.profit + model.profit_shortfall >= model.profit_target
    )
    model.production_goal = pyo.Constraint(
        expr=model.production["A"] + model.A_shortfall >= model.min_A_target
    )

    model.goal_objective = pyo.Objective(
        expr=model.profit_shortfall, sense=pyo.minimize
    )

    def solve_current_priority():
        try:
            Highs().solve(model)
        except RuntimeError as exc:
            # APPsi raises this when it cannot load a feasible solution.
            # Unexpected runtime errors are allowed to propagate.
            if "feasible solution was not found" in str(exc).lower():
                return {"objective": None, "status": "no_feasible_solution"}
            raise

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        return {"objective": obj_val, "status": "optimal"}

    # Priority 1: minimize the unmet profit target.
    result = solve_current_priority()
    if result["objective"] is None:
        return result

    model.preserve_profit_priority = pyo.Constraint(
        expr=model.profit_shortfall == result["objective"]
    )

    # Priority 2: minimize the unmet type A target without degrading priority 1.
    model.goal_objective.set_value(model.A_shortfall)
    result = solve_current_priority()
    if result["objective"] is None:
        return result

    model.preserve_A_priority = pyo.Constraint(
        expr=model.A_shortfall == result["objective"]
    )

    # Priority 3: minimize cost-weighted idle time, preserving both prior goals.
    model.goal_objective.set_value(model.weighted_idle)
    return solve_current_priority()