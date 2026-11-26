# IR: {"sets":{"grades":["I","I_prime","II"],"brands":["red","yellow","blue"]},"params":["supply_I","supply_I_prime","supply_II","cost_I","cost_I_prime","cost_II","price_red","price_yellow","price_blue","red_min_output","red_gradeI_upper_frac","red_gradeI_lower_frac","yellow_gradeII_upper_frac","yellow_gradeI_lower_frac","blue_gradeI_upper_frac","blue_gradeI_lower_frac"],"interpretation":"The duplicated grade-I rows are distinct ingredients I and I_prime. Upper grade-I limits refer to I; lower grade-I limits refer to I_prime. Percentage limits are inclusive LP bounds.","variables":{"x[g,b]":"continuous nonnegative kg of ingredient g allocated to brand b"},"expressions":{"output[b]":"sum_g x[g,b]"},"constraints":["sum_b x[g,b] <= supply[g] for each g","output[red] >= red_min_output","x[I,red] <= red_gradeI_upper_frac * output[red]","x[I_prime,red] >= red_gradeI_lower_frac * output[red]","x[II,yellow] <= yellow_gradeII_upper_frac * output[yellow]","x[I_prime,yellow] >= yellow_gradeI_lower_frac * output[yellow]","x[I,blue] <= blue_gradeI_upper_frac * output[blue]","x[I_prime,blue] >= blue_gradeI_lower_frac * output[blue]"],"objective":"maximize sum_g sum_b (price[b] - cost[g]) * x[g,b]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = {
        "I": params["supply_I"],
        "I_prime": params["supply_I_prime"],
        "II": params["supply_II"],
    }
    cost = {
        "I": params["cost_I"],
        "I_prime": params["cost_I_prime"],
        "II": params["cost_II"],
    }
    price = {
        "red": params["price_red"],
        "yellow": params["price_yellow"],
        "blue": params["price_blue"],
    }

    red_min_output = params["red_min_output"]
    red_gradeI_upper_frac = params["red_gradeI_upper_frac"]
    red_gradeI_lower_frac = params["red_gradeI_lower_frac"]
    yellow_gradeII_upper_frac = params["yellow_gradeII_upper_frac"]
    yellow_gradeI_lower_frac = params["yellow_gradeI_lower_frac"]
    blue_gradeI_upper_frac = params["blue_gradeI_upper_frac"]
    blue_gradeI_lower_frac = params["blue_gradeI_lower_frac"]

    model = pyo.ConcreteModel()
    model.grades = pyo.Set(initialize=("I", "I_prime", "II"), ordered=True)
    model.brands = pyo.Set(initialize=("red", "yellow", "blue"), ordered=True)

    model.x = pyo.Var(
        model.grades,
        model.brands,
        domain=pyo.NonNegativeReals,
    )

    model.output = pyo.Expression(
        model.brands,
        rule=lambda mdl, brand: sum(
            mdl.x[grade, brand] for grade in mdl.grades
        ),
    )

    model.supply_limits = pyo.Constraint(
        model.grades,
        rule=lambda mdl, grade: sum(
            mdl.x[grade, brand] for brand in mdl.brands
        ) <= supply[grade],
    )

    model.red_minimum_production = pyo.Constraint(
        expr=model.output["red"] >= red_min_output
    )
    model.red_first_grade_upper = pyo.Constraint(
        expr=model.x["I", "red"]
        <= red_gradeI_upper_frac * model.output["red"]
    )
    model.red_second_grade_lower = pyo.Constraint(
        expr=model.x["I_prime", "red"]
        >= red_gradeI_lower_frac * model.output["red"]
    )
    model.yellow_third_grade_upper = pyo.Constraint(
        expr=model.x["II", "yellow"]
        <= yellow_gradeII_upper_frac * model.output["yellow"]
    )
    model.yellow_second_grade_lower = pyo.Constraint(
        expr=model.x["I_prime", "yellow"]
        >= yellow_gradeI_lower_frac * model.output["yellow"]
    )
    model.blue_first_grade_upper = pyo.Constraint(
        expr=model.x["I", "blue"]
        <= blue_gradeI_upper_frac * model.output["blue"]
    )
    model.blue_second_grade_lower = pyo.Constraint(
        expr=model.x["I_prime", "blue"]
        >= blue_gradeI_lower_frac * model.output["blue"]
    )

    model.profit = pyo.Objective(
        expr=sum(
            (price[brand] - cost[grade]) * model.x[grade, brand]
            for grade in model.grades
            for brand in model.brands
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}