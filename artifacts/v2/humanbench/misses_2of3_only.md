# panel_base_2of3 certificates that miss the label and are not panel_base_3of3 certificates

Every panel_base_2of3 certificate whose value misses the label on a problem without a panel_base_3of3 certificate. IndustryOR and Mamo ComplexLP, scored with `round_aware` of scripts/score_eval.py against the original labels. Sections: identification with the expert status of Xiao et al. (2025), problem text, extracted parameter set with warnings, the three programs, values on the stated and resampled instances (both samplers), and the data-verification replies of the three families.

| Sample id | Benchmark | Certified value | Label | Expert status | B or C flags |
|---|---|---:|---:|---|---|
| `industryor_14` | IndustryOR | 23520.0 | 20240 | removed | no |
| `industryor_19` | IndustryOR | 25.0 | 12 | removed | no |
| `industryor_29` | IndustryOR | 904590.0 | 4685100 | removed | no |
| `industryor_32` | IndustryOR | 9100.0 | 8800 | removed | no |
| `industryor_33` | IndustryOR | -700.0 | 1360 | removed | no |
| `industryor_34` | IndustryOR | 2555.997963020646 | 770 | removed | yes |
| `industryor_41` | IndustryOR | 2630369.9999999995 | 1581550 | removed | no |
| `industryor_47` | IndustryOR | 4913500.0 | 5069500 | removed | no |
| `industryor_48` | IndustryOR | 156000.0 | 105.52 | removed | no |
| `industryor_57` | IndustryOR | 28.0 | 770 | removed | yes |
| `industryor_62` | IndustryOR | 0.0 | 11250 | removed | no |
| `industryor_65` | IndustryOR | 194.66666666666669 | 6105 | removed | no |
| `industryor_79` | IndustryOR | 479830000.0 | 435431000 | kept, same label; expert label 435431000 | no |
| `industryor_97` | IndustryOR | 4100.0 | 9500 | removed | no |
| `industryor_98` | IndustryOR | 510000.0 | 1360000 | removed | no |
| `industryor_100` | IndustryOR | 280.0 | 5500 | removed | no |
| `mamo_complex_45` | Mamo ComplexLP | 2430.0 | 2400 | removed | no |
| `mamo_complex_64` | Mamo ComplexLP | 212.0 | 199 | kept, same label; expert label 199.0 | no |
| `mamo_complex_71` | Mamo ComplexLP | 121.0 | 60 | removed | no |
| `mamo_complex_80` | Mamo ComplexLP | 4425.0 | 5213 | removed | yes |
| `mamo_complex_94` | Mamo ComplexLP | 22.333333333333332 | 23 | removed | no |
| `mamo_complex_100` | Mamo ComplexLP | 176.0 | 160 | kept, same label; expert label 160.0 | no |
| `mamo_complex_125` | Mamo ComplexLP | 14256.0 | 8090 | removed | no |
| `mamo_complex_163` | Mamo ComplexLP | 51.0 | 69 | kept, same label; expert label 69.0 | yes |
| `mamo_complex_205` | Mamo ComplexLP | 1.0 | 0.6 | removed | no |

## 1. industryor_14 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_14` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 14) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 23520.0 |
| Label (original benchmark) | 20240 |
| Rules that certify it | panel_base_2of3 23520.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol) |

### 2. Problem text

```
A farm has 100 hectares of land and 15,000 yuan available for production development. The farm has a labor force of 3,500 person-days in autumn and winter, and 4,000 person-days in spring and summer. If the labor force is not fully utilized, they can work outside. The wage for hired labor is 2.1 yuan/person-day in spring and summer, and 1.8 yuan/person-day in autumn and winter. The farm grows three crops: soybeans, corn, and wheat, and raises cows and chickens. There is no need for additional investment when planting crops, but for animal farming, it costs 400 yuan per cow and 3 yuan per chicken. When raising cows, 1.5 hectares of land are needed to grow grass for each cow, and it requires 100 person-days of labor in autumn and winter, and 50 person-days in spring and summer. The net income per cow per year is 400 yuan. When raising chickens, no land is needed, but it requires 0.6 person-days of labor in autumn and winter, and 0.3 person-days in spring and summer. The net income per chicken per year is 2 yuan. The farm has a chicken coop that can accommodate up to 3,000 chickens, and a cowshed that can accommodate up to 32 cows. The labor requirements and net income per hectare per year for the three crops are shown in Table 1-9.

Table 1-9
\begin{tabular}{l|c|c|c}
\hline \multicolumn{1}{c}{ Crop } & Soybeans & Corn & Wheat \\
\hline Person-days required in autumn and winter & 20 & 35 & 10 \\
Person-days required in spring and summer & 50 & 75 & 40 \\
Net income per hectare per year (yuan/hm^2) & 175 & 300 & 120 \\
\hline
\end{tabular}

Determine the farm's operating plan to maximize net income per year.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"land_capacity": {"base":100,"perturb":{"mode":"rel","r":0.3}}
"capital_budget": {"base":15000,"perturb":{"mode":"rel","r":0.5}}
"labor_aw_capacity": {"base":3500,"perturb":{"mode":"rel","r":0.3}}
"labor_ss_capacity": {"base":4000,"perturb":{"mode":"rel","r":0.3}}
"wage_hire_ss": {"base":2.1,"perturb":{"mode":"rel","r":0.5}}
"wage_hire_aw": {"base":1.8,"perturb":{"mode":"rel","r":0.5}}
"cow_investment": {"base":400,"perturb":{"mode":"rel","r":0.5}}
"chicken_investment": {"base":3,"perturb":{"mode":"rel","r":0.5}}
"land_per_cow": {"base":1.5,"perturb":{"mode":"rel","r":0.3}}
"labor_cow_aw": {"base":100,"perturb":{"mode":"rel","r":0.3}}
"labor_cow_ss": {"base":50,"perturb":{"mode":"rel","r":0.3}}
"income_cow": {"base":400,"perturb":{"mode":"rel","r":0.5}}
"labor_chicken_aw": {"base":0.6,"perturb":{"mode":"rel","r":0.3}}
"labor_chicken_ss": {"base":0.3,"perturb":{"mode":"rel","r":0.3}}
"income_chicken": {"base":2,"perturb":{"mode":"rel","r":0.5}}
"chicken_coop_capacity": {"base":3000,"perturb":{"mode":"rel","r":0.3}}
"cowshed_capacity": {"base":32,"perturb":{"mode":"rel","r":0.3}}
"labor_soybean_aw": {"base":20,"perturb":{"mode":"rel","r":0.3}}
"labor_soybean_ss": {"base":50,"perturb":{"mode":"rel","r":0.3}}
"income_soybean": {"base":175,"perturb":{"mode":"rel","r":0.5}}
"labor_corn_aw": {"base":35,"perturb":{"mode":"rel","r":0.3}}
"labor_corn_ss": {"base":75,"perturb":{"mode":"rel","r":0.3}}
"income_corn": {"base":300,"perturb":{"mode":"rel","r":0.5}}
"labor_wheat_aw": {"base":10,"perturb":{"mode":"rel","r":0.3}}
"labor_wheat_ss": {"base":40,"perturb":{"mode":"rel","r":0.3}}
"income_wheat": {"base":120,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables
    model.x_soybean = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_corn = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_wheat = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_cow = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_chicken = pyo.Var(domain=pyo.NonNegativeReals)
    model.hire_ss = pyo.Var(domain=pyo.NonNegativeReals)
    model.hire_aw = pyo.Var(domain=pyo.NonNegativeReals)

    # Objective: maximize net income
    model.profit = pyo.Expression(
        expr=params["income_soybean"] * model.x_soybean
        + params["income_corn"] * model.x_corn
        + params["income_wheat"] * model.x_wheat
        + params["income_cow"] * model.x_cow
        + params["income_chicken"] * model.x_chicken
        - params["wage_hire_ss"] * model.hire_ss
        - params["wage_hire_aw"] * model.hire_aw
    )
    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    # Land capacity
    model.land_con = pyo.Constraint(
        expr=model.x_soybean
        + model.x_corn
        + model.x_wheat
        + params["land_per_cow"] * model.x_cow
        <= params["land_capacity"]
    )

    # Capital budget
    model.capital_con = pyo.Constraint(
        expr=params["cow_investment"] * model.x_cow
        + params["chicken_investment"] * model.x_chicken
        <= params["capital_budget"]
    )

    # Autumn-winter labor
    model.labor_aw_con = pyo.Constraint(
        expr=params["labor_soybean_aw"] * model.x_soybean
        + params["labor_corn_aw"] * model.x_corn
        + params["labor_wheat_aw"] * model.x_wheat
        + params["labor_cow_aw"] * model.x_cow
        + params["labor_chicken_aw"] * model.x_chicken
        <= params["labor_aw_capacity"] + model.hire_aw
    )

    # Spring-summer labor
    model.labor_ss_con = pyo.Constraint(
        expr=params["labor_soybean_ss"] * model.x_soybean
        + params["labor_corn_ss"] * model.x_corn
        + params["labor_wheat_ss"] * model.x_wheat
        + params["labor_cow_ss"] * model.x_cow
        + params["labor_chicken_ss"] * model.x_chicken
        <= params["labor_ss_capacity"] + model.hire_ss
    )

    # Livestock capacities
    model.cowshed_con = pyo.Constraint(expr=model.x_cow <= params["cowshed_capacity"])
    model.coop_con = pyo.Constraint(expr=model.x_chicken <= params["chicken_coop_capacity"])

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or unsolved: " + type(exc).__name__}

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"crops":["soybean","corn","wheat"],"animals":["cow","chicken"],"seasons":["aw","ss"],"activities":"crops union animals"},"params":{"land_capacity":"params[land_capacity]","capital_budget":"params[capital_budget]","labor_capacity[aw,ss]":"params[labor_aw_capacity], params[labor_ss_capacity]","wage[aw,ss]":"params[wage_hire_aw], params[wage_hire_ss]","investment[cow,chicken]":"params[cow_investment], params[chicken_investment]","land_per_cow":"params[land_per_cow]","animal_capacity[cow,chicken]":"params[cowshed_capacity], params[chicken_coop_capacity]","labor[activity,season]":"params[labor_<activity>_<season>]","income[activity]":"params[income_<activity>]"},"variables":{"crop_area[crops]":"NonNegativeReals","animal_count[animals]":"NonNegativeIntegers","outside_work[seasons]":"NonNegativeReals","hired_labor[seasons]":"NonNegativeReals"},"constraints":["sum(crop_area) + land_per_cow*animal_count[cow] <= land_capacity","sum(investment[a]*animal_count[a] for a in animals) <= capital_budget","animal_count[a] <= animal_capacity[a] for each animal a","sum(labor[c,s]*crop_area[c] for c in crops) + sum(labor[a,s]*animal_count[a] for a in animals) + outside_work[s] == labor_capacity[s] + hired_labor[s] for each season s"],"objective":"maximize sum(income[c]*crop_area[c] for c in crops) + sum(income[a]*animal_count[a] for a in animals) + sum(wage[s]*(outside_work[s]-hired_labor[s]) for s in seasons)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.crops = pyo.Set(
        initialize=["soybean", "corn", "wheat"], ordered=True
    )
    model.animals = pyo.Set(
        initialize=["cow", "chicken"], ordered=True
    )
    model.seasons = pyo.Set(initialize=["aw", "ss"], ordered=True)
    model.activities = pyo.Set(
        initialize=["soybean", "corn", "wheat", "cow", "chicken"],
        ordered=True,
    )

    model.land_capacity = pyo.Param(
        initialize=params["land_capacity"]
    )
    model.capital_budget = pyo.Param(
        initialize=params["capital_budget"]
    )
    model.land_per_cow = pyo.Param(
        initialize=params["land_per_cow"]
    )

    model.labor_capacity = pyo.Param(
        model.seasons,
        initialize={
            "aw": params["labor_aw_capacity"],
            "ss": params["labor_ss_capacity"],
        },
    )
    model.wage = pyo.Param(
        model.seasons,
        initialize={
            "aw": params["wage_hire_aw"],
            "ss": params["wage_hire_ss"],
        },
    )
    model.investment = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cow_investment"],
            "chicken": params["chicken_investment"],
        },
    )
    model.animal_capacity = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cowshed_capacity"],
            "chicken": params["chicken_coop_capacity"],
        },
    )
    model.labor = pyo.Param(
        model.activities,
        model.seasons,
        initialize={
            ("soybean", "aw"): params["labor_soybean_aw"],
            ("soybean", "ss"): params["labor_soybean_ss"],
            ("corn", "aw"): params["labor_corn_aw"],
            ("corn", "ss"): params["labor_corn_ss"],
            ("wheat", "aw"): params["labor_wheat_aw"],
            ("wheat", "ss"): params["labor_wheat_ss"],
            ("cow", "aw"): params["labor_cow_aw"],
            ("cow", "ss"): params["labor_cow_ss"],
            ("chicken", "aw"): params["labor_chicken_aw"],
            ("chicken", "ss"): params["labor_chicken_ss"],
        },
    )
    model.income = pyo.Param(
        model.activities,
        initialize={
            "soybean": params["income_soybean"],
            "corn": params["income_corn"],
            "wheat": params["income_wheat"],
            "cow": params["income_cow"],
            "chicken": params["income_chicken"],
        },
    )

    model.crop_area = pyo.Var(
        model.crops, domain=pyo.NonNegativeReals
    )
    model.animal_count = pyo.Var(
        model.animals, domain=pyo.NonNegativeIntegers
    )
    model.outside_work = pyo.Var(
        model.seasons, domain=pyo.NonNegativeReals
    )
    model.hired_labor = pyo.Var(
        model.seasons, domain=pyo.NonNegativeReals
    )

    model.land_limit = pyo.Constraint(
        expr=(
            sum(model.crop_area[crop] for crop in model.crops)
            + model.land_per_cow * model.animal_count["cow"]
            <= model.land_capacity
        )
    )
    model.capital_limit = pyo.Constraint(
        expr=(
            sum(
                model.investment[animal] * model.animal_count[animal]
                for animal in model.animals
            )
            <= model.capital_budget
        )
    )

    def animal_capacity_rule(farm, animal):
        return (
            farm.animal_count[animal]
            <= farm.animal_capacity[animal]
        )

    model.housing_limits = pyo.Constraint(
        model.animals, rule=animal_capacity_rule
    )

    def seasonal_labor_rule(farm, season):
        return (
            sum(
                farm.labor[crop, season] * farm.crop_area[crop]
                for crop in farm.crops
            )
            + sum(
                farm.labor[animal, season] * farm.animal_count[animal]
                for animal in farm.animals
            )
            + farm.outside_work[season]
            == farm.labor_capacity[season] + farm.hired_labor[season]
        )

    model.seasonal_labor_balance = pyo.Constraint(
        model.seasons, rule=seasonal_labor_rule
    )

    model.net_income = pyo.Objective(
        expr=(
            sum(
                model.income[crop] * model.crop_area[crop]
                for crop in model.crops
            )
            + sum(
                model.income[animal] * model.animal_count[animal]
                for animal in model.animals
            )
            + sum(
                model.wage[season]
                * (
                    model.outside_work[season]
                    - model.hired_labor[season]
                )
                for season in model.seasons
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this error when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.net_income))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    land_capacity = params["land_capacity"]
    capital_budget = params["capital_budget"]
    labor_aw_capacity = params["labor_aw_capacity"]
    labor_ss_capacity = params["labor_ss_capacity"]
    wage_hire_ss = params["wage_hire_ss"]
    wage_hire_aw = params["wage_hire_aw"]
    cow_investment = params["cow_investment"]
    chicken_investment = params["chicken_investment"]
    land_per_cow = params["land_per_cow"]
    labor_cow_aw = params["labor_cow_aw"]
    labor_cow_ss = params["labor_cow_ss"]
    income_cow = params["income_cow"]
    labor_chicken_aw = params["labor_chicken_aw"]
    labor_chicken_ss = params["labor_chicken_ss"]
    income_chicken = params["income_chicken"]
    chicken_coop_capacity = params["chicken_coop_capacity"]
    cowshed_capacity = params["cowshed_capacity"]
    labor_soybean_aw = params["labor_soybean_aw"]
    labor_soybean_ss = params["labor_soybean_ss"]
    income_soybean = params["income_soybean"]
    labor_corn_aw = params["labor_corn_aw"]
    labor_corn_ss = params["labor_corn_ss"]
    income_corn = params["income_corn"]
    labor_wheat_aw = params["labor_wheat_aw"]
    labor_wheat_ss = params["labor_wheat_ss"]
    income_wheat = params["income_wheat"]

    model = gp.Model("farm_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # Crop areas (hectares)
    x_soy = model.addVar(lb=0.0, name="x_soy")    # soybeans
    x_corn = model.addVar(lb=0.0, name="x_corn")   # corn
    x_wheat = model.addVar(lb=0.0, name="x_wheat")  # wheat

    # Number of animals
    x_cow = model.addVar(lb=0.0, name="x_cow")       # cows
    x_chk = model.addVar(lb=0.0, name="x_chk")       # chickens

    # Idle labor that works outside (can earn wages)
    # (outside work earns wages, which adds to income)
    idle_aw = model.addVar(lb=0.0, name="idle_aw")  # unused AW labor (person-days)
    idle_ss = model.addVar(lb=0.0, name="idle_ss")  # unused SS labor (person-days)

    # Land constraint: crop land + cow-grass land <= total land
    model.addConstr(
        x_soy + x_corn + x_wheat + land_per_cow * x_cow <= land_capacity,
        name="land"
    )

    # Capital budget constraint
    model.addConstr(
        cow_investment * x_cow + chicken_investment * x_chk <= capital_budget,
        name="capital"
    )

    # Autumn-winter labor constraint
    # farm labor used + idle labor = total labor capacity
    model.addConstr(
        labor_soybean_aw * x_soy
        + labor_corn_aw * x_corn
        + labor_wheat_aw * x_wheat
        + labor_cow_aw * x_cow
        + labor_chicken_aw * x_chk
        + idle_aw == labor_aw_capacity,
        name="labor_aw"
    )

    # Spring-summer labor constraint
    model.addConstr(
        labor_soybean_ss * x_soy
        + labor_corn_ss * x_corn
        + labor_wheat_ss * x_wheat
        + labor_cow_ss * x_cow
        + labor_chicken_ss * x_chk
        + idle_ss == labor_ss_capacity,
        name="labor_ss"
    )

    # Capacity constraints
    model.addConstr(x_chk <= chicken_coop_capacity, name="coop_cap")
    model.addConstr(x_cow <= cowshed_capacity, name="shed_cap")

    # Objective: maximize net income
    # = income from crops + income from animals + wages from idle labor working outside
    model.setObjective(
        income_soybean * x_soy
        + income_corn * x_corn
        + income_wheat * x_wheat
        + income_cow * x_cow
        + income_chicken * x_chk
        + wage_hire_aw * idle_aw
        + wage_hire_ss * idle_ss,
        GRB.MAXIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 23520.0 (optimal) | 23520.0 (optimal) | 20260.869565217392 (optimal) |
| 1 | 16220.678976244195 (optimal) | 17958.16801003138 (optimal) | 18015.61945865208 (optimal) |
| 2 | 27058.314307985253 (optimal) | 28834.074047810027 (optimal) | 27779.543259796556 (optimal) |
| 3 | 27902.563216161787 (optimal) | 28008.250253965092 (optimal) | 27916.31285816854 (optimal) |
| 4 | 16657.44582015809 (optimal) | 18924.12463877059 (optimal) | 18924.739579078177 (optimal) |
| 5 | 22440.522565304625 (optimal) | 22428.265634315558 (optimal) | 21711.71752262275 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 23520.0 (optimal) | 23520.0 (optimal) | 20260.869565217392 (optimal) |
| 1 | 16220.678976244195 (optimal) | 17958.16801003138 (optimal) | 18015.61945865208 (optimal) |
| 2 | 27058.314307985253 (optimal) | 28834.074047810027 (optimal) | 27779.543259796556 (optimal) |
| 3 | 27902.563216161787 (optimal) | 28008.250253965092 (optimal) | 27916.31285816854 (optimal) |
| 4 | 16657.44582015809 (optimal) | 18924.12463877059 (optimal) | 18924.739579078177 (optimal) |
| 5 | 22440.522565304625 (optimal) | 22428.265634315558 (optimal) | 21711.71752262275 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{"mismatch": [], "not_stated": []}
```
````

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 2. industryor_19 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_19` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 19) |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 25.0 |
| Label (original benchmark) | 12 |
| Rules that certify it | gate 25.0, panel_base_2of3 25.0, ind_gate 25.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
There are three different products that need to be processed on three machine tools. Each product must be processed first on machine 1, then sequentially on machine 2 and 3. The order of processing the three products should remain the same on each machine. Assume \( t_{ij} \) represents the time it takes to process the \( i \)th product on the \( j \)th machine.\n\n**Given:**\n\n- \( t_{11} = 5 \) minutes, \( t_{12} = 4 \) minutes, \( t_{13} = 3 \) minutes\n- \( t_{21} = 6 \) minutes, \( t_{22} = 5 \) minutes, \( t_{23} = 4 \) minutes\n- \( t_{31} = 7 \) minutes, \( t_{32} = 6 \) minutes, \( t_{33} = 5 \) minutes
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"t_11": {"base":5,"perturb":{"mode":"abs","lo":2.0,"hi":10.0,"integer":true}}
"t_12": {"base":4,"perturb":{"mode":"abs","lo":1.0,"hi":9.0,"integer":true}}
"t_13": {"base":3,"perturb":{"mode":"abs","lo":1.0,"hi":8.0,"integer":true}}
"t_21": {"base":6,"perturb":{"mode":"abs","lo":2.0,"hi":11.0,"integer":true}}
"t_22": {"base":5,"perturb":{"mode":"abs","lo":1.0,"hi":10.0,"integer":true}}
"t_23": {"base":4,"perturb":{"mode":"abs","lo":1.0,"hi":9.0,"integer":true}}
"t_31": {"base":7,"perturb":{"mode":"abs","lo":3.0,"hi":12.0,"integer":true}}
"t_32": {"base":6,"perturb":{"mode":"abs","lo":2.0,"hi":11.0,"integer":true}}
"t_33": {"base":5,"perturb":{"mode":"abs","lo":1.0,"hi":10.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    t = {
        (1, 1): params["t_11"], (1, 2): params["t_12"], (1, 3): params["t_13"],
        (2, 1): params["t_21"], (2, 2): params["t_22"], (2, 3): params["t_23"],
        (3, 1): params["t_31"], (3, 2): params["t_32"], (3, 3): params["t_33"],
    }

    products = [1, 2, 3]
    machines = [1, 2, 3]

    model = pyo.ConcreteModel()

    # Start time of each product on each machine (flow shop, same order)
    model.start = pyo.Var(products, machines, within=pyo.NonNegativeReals)

    # Makespan (completion time of last product on last machine)
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    # Each product must respect processing order across machines
    def machine_order_rule(mdl, i, j):
        if j == 1:
            return pyo.Constraint.Skip
        return mdl.start[i, j] >= mdl.start[i, j - 1] + t[(i, j - 1)]
    model.machine_order = pyo.Constraint(products, machines, rule=machine_order_rule)

    # Same product order on every machine: no overlap between consecutive products
    def product_order_rule(mdl, i, j):
        if i == 1:
            return pyo.Constraint.Skip
        return mdl.start[i, j] >= mdl.start[i - 1, j] + t[(i - 1, j)]
    model.product_order = pyo.Constraint(products, machines, rule=product_order_rule)

    # Makespan definition
    def makespan_rule(mdl, i):
        return mdl.makespan >= mdl.start[i, 3] + t[(i, 3)]
    model.makespan_def = pyo.Constraint(products, rule=makespan_rule)

    # Objective: minimize makespan
    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"products":[1,2,3],"positions":[1,2,3],"machines":[1,2,3]},"params":{"t_11":"nonnegative processing time","t_12":"nonnegative processing time","t_13":"nonnegative processing time","t_21":"nonnegative processing time","t_22":"nonnegative processing time","t_23":"nonnegative processing time","t_31":"nonnegative processing time","t_32":"nonnegative processing time","t_33":"nonnegative processing time"},"variables":{"assignment[i,r]":"binary; product i occupies position r on every machine","completion[r,j]":"nonnegative continuous; completion of position r on machine j"},"expressions":{"duration[r,j]":"sum_i t_ij * assignment[i,r]"},"constraints":["Each product occupies exactly one position: sum_r assignment[i,r] = 1.","Each position contains exactly one product: sum_i assignment[i,r] = 1.","Machine sequence: completion[r,j] >= (completion[r-1,j] if r>1 else 0) + duration[r,j].","Machine routing: completion[r,j] >= completion[r,j-1] + duration[r,j] for j>1."],"objective":{"sense":"minimize","expression":"completion[3,3]","meaning":"makespan"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(1, 3)
    model.positions = pyo.RangeSet(1, 3)
    model.machines = pyo.RangeSet(1, 3)

    processing_times = {
        (1, 1): params["t_11"],
        (1, 2): params["t_12"],
        (1, 3): params["t_13"],
        (2, 1): params["t_21"],
        (2, 2): params["t_22"],
        (2, 3): params["t_23"],
        (3, 1): params["t_31"],
        (3, 2): params["t_32"],
        (3, 3): params["t_33"],
    }

    model.processing_time = pyo.Param(
        model.products,
        model.machines,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.products, model.positions, domain=pyo.Binary
    )
    model.completion = pyo.Var(
        model.positions, model.machines, domain=pyo.NonNegativeReals
    )

    def duration_rule(mdl, position, machine):
        return sum(
            mdl.processing_time[product, machine]
            * mdl.assignment[product, position]
            for product in mdl.products
        )

    model.duration = pyo.Expression(
        model.positions, model.machines, rule=duration_rule
    )

    def product_position_rule(mdl, product):
        return sum(
            mdl.assignment[product, position]
            for position in mdl.positions
        ) == 1

    model.product_position = pyo.Constraint(
        model.products, rule=product_position_rule
    )

    def position_product_rule(mdl, position):
        return sum(
            mdl.assignment[product, position]
            for product in mdl.products
        ) == 1

    model.position_product = pyo.Constraint(
        model.positions, rule=position_product_rule
    )

    def machine_sequence_rule(mdl, position, machine):
        previous_completion = (
            mdl.completion[position - 1, machine]
            if position > 1
            else 0
        )
        return (
            mdl.completion[position, machine]
            >= previous_completion + mdl.duration[position, machine]
        )

    model.machine_sequence = pyo.Constraint(
        model.positions, model.machines, rule=machine_sequence_rule
    )

    def machine_routing_rule(mdl, position, machine):
        if machine == 1:
            return pyo.Constraint.Skip
        return (
            mdl.completion[position, machine]
            >= mdl.completion[position, machine - 1]
            + mdl.duration[position, machine]
        )

    model.machine_routing = pyo.Constraint(
        model.positions, model.machines, rule=machine_routing_rule
    )

    model.makespan = pyo.Objective(
        expr=model.completion[3, 3],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.makespan))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    t = {
        (1, 1): params["t_11"],
        (1, 2): params["t_12"],
        (1, 3): params["t_13"],
        (2, 1): params["t_21"],
        (2, 2): params["t_22"],
        (2, 3): params["t_23"],
        (3, 1): params["t_31"],
        (3, 2): params["t_32"],
        (3, 3): params["t_33"],
    }

    products = [1, 2, 3]
    machines = [1, 2, 3]

    best_makespan = float("inf")
    best_perm = None

    # Enumerate all 6 permutations of product order (same order on all machines)
    for perm in permutations(products):
        # Compute completion times for this sequence
        # C[i][j] = completion time of product perm[i] on machine j
        C = {}
        for idx, prod in enumerate(perm):
            for jdx, mach in enumerate(machines):
                if idx == 0 and jdx == 0:
                    C[(idx, jdx)] = t[(prod, mach)]
                elif idx == 0:
                    # First product, subsequent machines: must wait for same product on previous machine
                    C[(idx, jdx)] = C[(idx, jdx - 1)] + t[(prod, mach)]
                elif jdx == 0:
                    # First machine, subsequent products: must wait for previous product to finish machine 1
                    C[(idx, jdx)] = C[(idx - 1, jdx)] + t[(prod, mach)]
                else:
                    # Must wait for: same product on previous machine AND previous product on same machine
                    C[(idx, jdx)] = max(C[(idx - 1, jdx)], C[(idx, jdx - 1)]) + t[(prod, mach)]

        makespan = C[(len(perm) - 1, len(machines) - 1)]
        if makespan < best_makespan:
            best_makespan = makespan
            best_perm = perm

    # Now build a Gurobi model that represents the optimal permutation found
    # (the problem is a pure flow shop scheduling problem; we encode the optimal sequence)
    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)

    perm = best_perm
    n_prod = len(products)
    n_mach = len(machines)

    # Decision variables: C_vars[i][j] = completion time of product perm[i] on machine j
    C_vars = {}
    for idx in range(n_prod):
        for jdx in range(n_mach):
            C_vars[(idx, jdx)] = model.addVar(lb=0.0, name=f"C_{idx}_{jdx}")

    makespan_var = model.addVar(lb=0.0, name="makespan")
    model.setObjective(makespan_var, GRB.MINIMIZE)

    # Processing time constraints and precedence
    for idx, prod in enumerate(perm):
        for jdx, mach in enumerate(machines):
            proc = t[(prod, mach)]
            if idx == 0 and jdx == 0:
                model.addConstr(C_vars[(idx, jdx)] >= proc)
            elif idx == 0:
                model.addConstr(C_vars[(idx, jdx)] >= C_vars[(idx, jdx - 1)] + proc)
            elif jdx == 0:
                model.addConstr(C_vars[(idx, jdx)] >= C_vars[(idx - 1, jdx)] + proc)
            else:
                model.addConstr(C_vars[(idx, jdx)] >= C_vars[(idx - 1, jdx)] + proc)
                model.addConstr(C_vars[(idx, jdx)] >= C_vars[(idx, jdx - 1)] + proc)

    # Makespan = completion time of last product on last machine
    model.addConstr(makespan_var >= C_vars[(n_prod - 1, n_mach - 1)])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 29.0 (optimal) | 25.0 (optimal) | 25.0 (optimal) |
| 1 | 30.0 (optimal) | 26.0 (optimal) | 26.0 (optimal) |
| 2 | 22.0 (optimal) | 22.0 (optimal) | 22.0 (optimal) |
| 3 | 35.0 (optimal) | 34.0 (optimal) | 34.0 (optimal) |
| 4 | 35.0 (optimal) | 35.0 (optimal) | 35.0 (optimal) |
| 5 | 30.0 (optimal) | 29.0 (optimal) | 29.0 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 29.0 (optimal) | 25.0 (optimal) | 25.0 (optimal) |
| 1 | 30.0 (optimal) | 26.0 (optimal) | 26.0 (optimal) |
| 2 | 22.0 (optimal) | 22.0 (optimal) | 22.0 (optimal) |
| 3 | 35.0 (optimal) | 34.0 (optimal) | 34.0 (optimal) |
| 4 | 35.0 (optimal) | 35.0 (optimal) | 35.0 (optimal) |
| 5 | 30.0 (optimal) | 29.0 (optimal) | 29.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 3. industryor_29 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_29` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 29) |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 904590.0 |
| Label (original benchmark) | 4685100 |
| Rules that certify it | gate 904590.0, panel_base_2of3 904590.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
An Italian transportation company needs to transport some empty containers from its 6 warehouses (located in Verona, Perugia, Rome, Pescara, Taranto, and La Spezia) to major national ports (Genoa, Venice, Ancona, Naples, Bari). The inventory of containers in each warehouse is as follows:

|  | Empty Containers |
| :---: | :---: |
| Verona | 10 |
| Perugia | 12 |
| Rome | 20 |
| Pescara | 24 |
| Taranto | 18 |
| La Spezia | 40 |

The demand at the ports is as follows:

|  | Container Demand |
| :---: | :---: |
| Genoa | 20 |
| Venice | 15 |
| Ancona | 25 |
| Naples | 33 |
| Bari | 21 |

The transportation will be done by a fleet of trucks. The transportation cost for each container is directly proportional to the distance traveled by the truck, at a rate of 30 euros per kilometer. Each truck can transport a maximum of 2 containers. The distances are as follows:

|  | Genoa | Venice | Ancona | Naples | Bari |
| :---: | :---: | :---: | :---: | :---: | :---: |
| Verona | $290 \mathrm{~km}$ | $115 \mathrm{~km}$ | $355 \mathrm{~km}$ | $715 \mathrm{~km}$ | $810 \mathrm{~km}$ |
| Perugia | $380 \mathrm{~km}$ | $340 \mathrm{~km}$ | $165 \mathrm{~km}$ | $380 \mathrm{~km}$ | $610 \mathrm{~km}$ |
| Rome | $505 \mathrm{~km}$ | $530 \mathrm{~km}$ | $285 \mathrm{~km}$ | $220 \mathrm{~km}$ | $450 \mathrm{~km}$ |
| Pescara | $655 \mathrm{~km}$ | $450 \mathrm{~km}$ | $155 \mathrm{~km}$ | $240 \mathrm{~km}$ | $315 \mathrm{~km}$ |
| Taranto | $1010 \mathrm{~km}$ | $840 \mathrm{~km}$ | $550 \mathrm{~km}$ | $305 \mathrm{~km}$ | $95 \mathrm{~km}$ |
| La Spezia | $1072 \mathrm{~km}$ | $1097 \mathrm{~km}$ | $747 \mathrm{~km}$ | $372 \mathrm{~km}$ | $333 \mathrm{~km}$ |

Write a mathematical program to find the transportation policy that minimizes cost and solve it using COPTPY.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"supply": {"base":[10,12,20,24,18,40],"perturb":{"mode":"rel","r":0.25}}
"demand": {"base":[20,15,25,33,21],"perturb":{"mode":"rel","r":0.25}}
"cost_rate": {"base":30,"perturb":{"mode":"rel","r":0.3}}
"distance": {"base":[[290,115,355,715,810],[380,340,165,380,610],[505,530,285,220,450],[655,450,155,240,315],[1010,840,550,305,95],[1072,1097,747,372,333]],"perturb":{"mode":"rel","r":0.15}}
"truck_capacity": {"base":2,"perturb":{"mode":"abs","lo":2.0,"hi":2.0,"integer":true}}
```

Warnings:

```
[truck_capacity] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_rate = params["cost_rate"]
    distance = params["distance"]
    truck_capacity = params["truck_capacity"]

    warehouses = ["Verona", "Perugia", "Rome", "Pescara", "Taranto", "La Spezia"]
    ports = ["Genoa", "Venice", "Ancona", "Naples", "Bari"]

    model = pyo.ConcreteModel()
    model.W = pyo.Set(initialize=warehouses)
    model.P = pyo.Set(initialize=ports)

    model.x = pyo.Var(model.W, model.P, within=pyo.NonNegativeIntegers)

    def obj_rule(mdl):
        return sum(
            mdl.x[w, p] * (distance[warehouses.index(w)][ports.index(p)] * cost_rate / truck_capacity)
            for w in mdl.W for p in mdl.P
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.supply_con = pyo.Constraint(
        model.W,
        rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w]
    )
    model.demand_con = pyo.Constraint(
        model.P,
        rule=lambda mdl, p: sum(mdl.x[w, p] for w in mdl.W) >= demand[p]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"W":["Verona","Perugia","Rome","Pescara","Taranto","La Spezia"],"P":["Genoa","Venice","Ancona","Naples","Bari"]},"params":{"supply":"nonnegative[W]","demand":"nonnegative[P]","cost_rate":"nonnegative scalar","distance":"nonnegative[W,P]","truck_capacity":"nonnegative scalar"},"variables":{"containers[W,P]":"nonnegative integer","trucks[W,P]":"nonnegative integer"},"constraints":{"warehouse_supply":"sum(p in P, containers[w,p]) <= supply[w] for w in W","port_demand":"sum(w in W, containers[w,p]) == demand[p] for p in P","truck_loading":"containers[w,p] <= truck_capacity * trucks[w,p] for (w,p) in W x P"},"objective":"minimize sum((w,p) in W x P, cost_rate * distance[w,p] * containers[w,p])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouses = (
        "Verona",
        "Perugia",
        "Rome",
        "Pescara",
        "Taranto",
        "La Spezia",
    )
    ports = ("Genoa", "Venice", "Ancona", "Naples", "Bari")

    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_rate_data = params["cost_rate"]
    distance_data = params["distance"]
    truck_capacity_data = params["truck_capacity"]

    # Vectors accept ordered sequences or mappings keyed by location name.
    def vector_value(data, position, location):
        if isinstance(data, Mapping):
            return data[location]
        return data[position]

    # Distances accept an ordered matrix, nested location mappings,
    # or a mapping keyed by (warehouse_name, port_name).
    def distance_value(warehouse_position, port_position):
        warehouse = warehouses[warehouse_position]
        port = ports[port_position]
        if isinstance(distance_data, Mapping):
            if (warehouse, port) in distance_data:
                return distance_data[warehouse, port]
            row = distance_data[warehouse]
        else:
            row = distance_data[warehouse_position]
        return vector_value(row, port_position, port)

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses, ordered=True)
    model.P = pyo.Set(initialize=ports, ordered=True)

    model.supply = pyo.Param(
        model.W,
        initialize={
            warehouse: vector_value(supply_data, position, warehouse)
            for position, warehouse in enumerate(warehouses)
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.P,
        initialize={
            port: vector_value(demand_data, position, port)
            for position, port in enumerate(ports)
        },
        within=pyo.NonNegativeReals,
    )
    model.cost_rate = pyo.Param(
        initialize=cost_rate_data,
        within=pyo.NonNegativeReals,
    )
    model.distance = pyo.Param(
        model.W,
        model.P,
        initialize={
            (warehouse, port): distance_value(
                warehouse_position, port_position
            )
            for warehouse_position, warehouse in enumerate(warehouses)
            for port_position, port in enumerate(ports)
        },
        within=pyo.NonNegativeReals,
    )
    model.truck_capacity = pyo.Param(
        initialize=truck_capacity_data,
        within=pyo.NonNegativeReals,
    )

    model.containers = pyo.Var(
        model.W, model.P, domain=pyo.NonNegativeIntegers
    )
    model.trucks = pyo.Var(
        model.W, model.P, domain=pyo.NonNegativeIntegers
    )

    def warehouse_supply_rule(instance, warehouse):
        return (
            sum(instance.containers[warehouse, port] for port in instance.P)
            <= instance.supply[warehouse]
        )

    def port_demand_rule(instance, port):
        return (
            sum(
                instance.containers[warehouse, port]
                for warehouse in instance.W
            )
            == instance.demand[port]
        )

    def truck_loading_rule(instance, warehouse, port):
        return (
            instance.containers[warehouse, port]
            <= instance.truck_capacity * instance.trucks[warehouse, port]
        )

    model.warehouse_supply = pyo.Constraint(
        model.W, rule=warehouse_supply_rule
    )
    model.port_demand = pyo.Constraint(
        model.P, rule=port_demand_rule
    )
    model.truck_loading = pyo.Constraint(
        model.W, model.P, rule=truck_loading_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_rate
            * model.distance[warehouse, port]
            * model.containers[warehouse, port]
            for warehouse in model.W
            for port in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    supply = params["supply"]       # list of 6 values
    demand = params["demand"]       # list of 5 values
    cost_rate = params["cost_rate"] # euros per km per container
    distance = params["distance"]   # 6x5 matrix
    truck_capacity = params["truck_capacity"]  # max containers per truck

    warehouses = range(6)
    ports = range(5)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = number of containers shipped from warehouse i to port j
    x = model.addVars(warehouses, ports, vtype=GRB.INTEGER, lb=0, name="x")

    # Number of trucks needed for each route (ceiling of containers / truck_capacity)
    # Cost = cost_rate * distance[i][j] * x[i,j]
    # (cost per container proportional to distance, so total cost = cost_rate * dist * containers)
    obj = gp.quicksum(
        cost_rate * distance[i][j] * x[i, j]
        for i in warehouses for j in ports
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Supply constraints
    for i in warehouses:
        model.addConstr(
            gp.quicksum(x[i, j] for j in ports) <= supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints
    for j in ports:
        model.addConstr(
            gp.quicksum(x[i, j] for i in warehouses) >= demand[j],
            name=f"demand_{j}"
        )

    # Truck capacity constraint: containers on each route must be in multiples
    # such that x[i,j] <= trucks[i,j] * truck_capacity
    # Equivalently, introduce integer truck variables
    trucks = model.addVars(warehouses, ports, vtype=GRB.INTEGER, lb=0, name="trucks")
    for i in warehouses:
        for j in ports:
            model.addConstr(
                x[i, j] <= trucks[i, j] * truck_capacity,
                name=f"truck_cap_{i}_{j}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | 904590.0 (optimal) | 904590.0 (optimal) |
| 1 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | 1246037.633630915 (optimal) | 1246037.633630915 (optimal) |
| 2 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | none (solve_failed) | none (infeasible) |
| 3 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | none (solve_failed) | none (infeasible) |
| 4 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | 950630.1532712057 (optimal) | 950630.1532712056 (optimal) |
| 5 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | 781760.3520100393 (optimal) | 781760.3520100394 (optimal) |

#### independent

Decision: UNINFORMATIVE; clique none; informative instances [0]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | 904590.0 (optimal) | 904590.0 (optimal) |
| 1 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | none (solve_failed) | 948704.4574589911 (optimal) |
| 2 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | none (solve_failed) | none (infeasible) |
| 3 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | none (solve_failed) | none (infeasible) |
| 4 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | none (solve_failed) | 850177.8154108704 (optimal) |
| 5 | none (crash:rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w] \| ~~~~~~^^^ \| TypeError: list indices must be integers or slices, not str) | none (solve_failed) | none (infeasible) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 4. industryor_32 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_32` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 32) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 9100.0 |
| Label (original benchmark) | 8800 |
| Rules that certify it | gate 9100.0, panel_base_2of3 9100.0, ind_gate 9100.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A certain store has formulated a purchasing and selling plan for a certain product from July to December. It is known that the store's warehouse capacity cannot exceed 500 units. By the end of June, there are already 200 units in stock. From then on, the store will purchase once at the beginning of each month. Assuming the purchase and selling prices of the product for each month are as shown in Table 1-21, how many units should be purchased and sold each month to maximize total revenue?

Table 1-21
\begin{tabular}{c|cccccc}
\hline Month & 7 & 8 & 9 & 10 & 11 & 12 \\
\hline Purchase & 28 & 24 & 25 & 27 & 23 & 23 \\
\hline Sale & 29 & 24 & 26 & 28 & 22 & 25 \\
\hline Sale & 29 & 24 & 26 & 28 & 22 & 25 \\
\hline
\end{tabular}
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"warehouse_capacity": {"base":500,"perturb":{"mode":"abs","lo":250.0,"hi":750.0,"integer":true}}
"initial_inventory": {"base":200,"perturb":{"mode":"abs","lo":100.0,"hi":400.0,"integer":true}}
"purchase_prices": {"base":[28,24,25,27,23,23],"perturb":{"mode":"rel","r":0.25}}
"sale_prices": {"base":[29,24,26,28,22,25],"perturb":{"mode":"rel","r":0.25}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    purchase_prices = params["purchase_prices"]
    sale_prices = params["sale_prices"]

    n_months = len(purchase_prices)
    months = list(range(n_months))
    last = n_months - 1

    model = pyo.ConcreteModel()
    model.months = pyo.Set(initialize=months)

    model.purchase = pyo.Var(model.months, within=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.months, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, within=pyo.NonNegativeReals)

    def inventory_balance_rule(mdl, t):
        if t == 0:
            return mdl.inventory[t] == initial_inventory + mdl.purchase[t] - mdl.sale[t]
        return mdl.inventory[t] == mdl.inventory[t - 1] + mdl.purchase[t] - mdl.sale[t]

    model.inventory_balance = pyo.Constraint(model.months, rule=inventory_balance_rule)

    def capacity_rule(mdl, t):
        return mdl.inventory[t] <= capacity

    model.capacity_limit = pyo.Constraint(model.months, rule=capacity_rule)

    def ending_rule(mdl):
        return mdl.inventory[last] == 0

    model.ending_inventory = pyo.Constraint(rule=ending_rule)

    def objective_rule(mdl):
        return sum(sale_prices[t] * mdl.sale[t] - purchase_prices[t] * mdl.purchase[t] for t in mdl.months)

    model.total_profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"warehouse_capacity":"scalar","initial_inventory":"scalar","purchase_prices":"length-6 vector indexed by T","sale_prices":"length-6 vector indexed by T"},"variables":{"purchase[t]":"nonnegative real","sales[t]":"nonnegative real","inventory[t]":"nonnegative real, end-of-month"},"constraints":["inventory[0] = initial_inventory + purchase[0] - sales[0]","inventory[t] = inventory[t-1] + purchase[t] - sales[t], t=1..5","initial_inventory + purchase[0] <= warehouse_capacity","inventory[t-1] + purchase[t] <= warehouse_capacity, t=1..5"],"objective":"maximize sum(sale_prices[t]*sales[t] - purchase_prices[t]*purchase[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    purchase_prices = params["purchase_prices"]
    sale_prices = params["sale_prices"]

    if len(purchase_prices) != 6 or len(sale_prices) != 6:
        raise ValueError("Each price vector must contain six monthly prices.")

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(0, 5)

    model.warehouse_capacity = pyo.Param(initialize=warehouse_capacity)
    model.initial_inventory = pyo.Param(initialize=initial_inventory)
    model.purchase_prices = pyo.Param(
        model.months,
        initialize={t: purchase_prices[t] for t in range(6)},
    )
    model.sale_prices = pyo.Param(
        model.months,
        initialize={t: sale_prices[t] for t in range(6)},
    )

    model.purchase = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def inventory_balance_rule(instance, t):
        starting_inventory = (
            instance.initial_inventory if t == 0 else instance.inventory[t - 1]
        )
        return (
            instance.inventory[t]
            == starting_inventory + instance.purchase[t] - instance.sales[t]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    def warehouse_limit_rule(instance, t):
        starting_inventory = (
            instance.initial_inventory if t == 0 else instance.inventory[t - 1]
        )
        return (
            starting_inventory + instance.purchase[t]
            <= instance.warehouse_capacity
        )

    model.warehouse_limit = pyo.Constraint(
        model.months, rule=warehouse_limit_rule
    )

    model.total_net_revenue = pyo.Objective(
        expr=sum(
            model.sale_prices[t] * model.sales[t]
            - model.purchase_prices[t] * model.purchase[t]
            for t in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this when it cannot load a feasible solution.
        # Still use objective retrieval as the sole success criterion.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_net_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory  = params["initial_inventory"]
    purchase_prices    = params["purchase_prices"]   # list of 6 values, July–December
    sale_prices        = params["sale_prices"]        # list of 6 values, July–December

    n_months = 6  # structural constant: July through December

    model = gp.Model("purchasing_selling_plan")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # buy[t]  : units purchased at the beginning of month t
    # sell[t] : units sold during month t
    buy  = model.addVars(n_months, lb=0.0, name="buy")
    sell = model.addVars(n_months, lb=0.0, name="sell")

    # Inventory after transactions in month t
    # inv[t] = inventory at end of month t
    inv = model.addVars(n_months, lb=0.0, name="inv")

    # Inventory balance constraints
    for t in range(n_months):
        prev_inv = initial_inventory if t == 0 else inv[t - 1]
        # At start of month: receive buy[t], then sell sell[t]
        # End-of-month inventory
        model.addConstr(inv[t] == prev_inv + buy[t] - sell[t],
                        name=f"balance_{t}")

    # Warehouse capacity: inventory after purchasing but before selling
    # must not exceed capacity; also end-of-month inventory ≤ capacity
    for t in range(n_months):
        prev_inv = initial_inventory if t == 0 else inv[t - 1]
        # inventory right after purchasing (before selling)
        model.addConstr(prev_inv + buy[t] <= warehouse_capacity,
                        name=f"capacity_{t}")

    # Objective: total revenue = sales revenue - purchase costs
    revenue = gp.quicksum(sale_prices[t] * sell[t] - purchase_prices[t] * buy[t]
                          for t in range(n_months))
    model.setObjective(revenue, GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 9100.0 (optimal) | 9100.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 10321.602171870727 (optimal) | 10321.602171870725 (optimal) |
| 2 | none (infeasible_or_unbounded) | 14870.328006552609 (optimal) | 14870.328006552607 (optimal) |
| 3 | none (infeasible_or_unbounded) | 15393.681850161553 (optimal) | 15393.68185016155 (optimal) |
| 4 | none (infeasible_or_unbounded) | 12879.084475410784 (optimal) | 12879.084475410782 (optimal) |
| 5 | none (infeasible_or_unbounded) | 12617.352063837036 (optimal) | 12617.352063837036 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 9100.0 (optimal) | 9100.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 10321.602171870727 (optimal) | 10321.602171870725 (optimal) |
| 2 | none (infeasible_or_unbounded) | 14870.328006552609 (optimal) | 14870.328006552607 (optimal) |
| 3 | none (infeasible_or_unbounded) | 15393.681850161553 (optimal) | 15393.68185016155 (optimal) |
| 4 | none (infeasible_or_unbounded) | 12879.084475410784 (optimal) | 12879.084475410782 (optimal) |
| 5 | none (infeasible_or_unbounded) | 12617.352063837036 (optimal) | 12617.352063837036 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 5. industryor_33 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_33` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 33) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | -700.0 |
| Label (original benchmark) | 1360 |
| Rules that certify it | panel_base_2of3 -700.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A trading company specializes in wholesale business of a certain kind of miscellaneous grain. The company has a warehouse with a capacity of 5000 units. On January 1st, the company has a stock of 1000 units of miscellaneous grain and a capital of 20000 yuan. The estimated prices of the grain for the first quarter are shown in Table 1-8.
Table $1-8$
\begin{tabular}{c|c|c}
\hline Month & Purchase Price/(yuan/unit) & Selling Price $/$ (yuan $/$ unit) \\
\hline 1 & 2.85 & 3.10 \\
2 & 3.05 & 3.25 \\
3 & 2.90 & 2.95 \\
\hline
\end{tabular}

The purchased grain arrives in the same month but can only be sold in the following month, and it is required to be paid upon delivery. The company wants to have a stock of 2000 units at the end of the quarter. What buying and selling strategies should be adopted to maximize the total profit over the three months?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"warehouse_capacity": {"base":5000,"perturb":{"mode":"rel","r":0.3}}
"initial_stock": {"base":1000,"perturb":{"mode":"abs","lo":0.0,"hi":3000.0,"integer":true}}
"initial_capital": {"base":20000,"perturb":{"mode":"rel","r":0.5}}
"purchase_price": {"base":[2.85,3.05,2.9],"perturb":{"mode":"rel","r":0.2}}
"selling_price": {"base":[3.1,3.25,2.95],"perturb":{"mode":"rel","r":0.2}}
"terminal_stock_requirement": {"base":2000,"perturb":{"mode":"abs","lo":0.0,"hi":4000.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["warehouse_capacity"]
    init_stock = params["initial_stock"]
    init_capital = params["initial_capital"]
    buy_price = params["purchase_price"]
    sell_price = params["selling_price"]
    terminal_stock = params["terminal_stock_requirement"]

    months = [1, 2, 3]

    model = pyo.ConcreteModel()
    model.M = pyo.Set(initialize=months)

    # Indexing choice: variables indexed by real month numbers (1,2,3)
    model.buy = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.stock = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.capital = pyo.Var(model.M, within=pyo.NonNegativeReals)

    def buy_p(m):
        return buy_price[m - 1]

    def sell_p(m):
        return sell_price[m - 1]

    def prev_stock(m):
        return init_stock if m == 1 else model.stock[m - 1]

    def prev_capital(m):
        return init_capital if m == 1 else model.capital[m - 1]

    def stock_balance_rule(m):
        return model.stock[m] == prev_stock(m) + model.buy[m] - model.sell[m]

    model.stock_balance_con = pyo.Constraint(model.M, rule=stock_balance_rule)

    def cap_rule(m):
        return model.stock[m] <= capacity

    model.cap_con = pyo.Constraint(model.M, rule=cap_rule)

    # Grain bought this month cannot be sold this month
    def sell_limit_rule(m):
        return model.sell[m] <= prev_stock(m)

    model.sell_limit_con = pyo.Constraint(model.M, rule=sell_limit_rule)

    def cash_balance_rule(m):
        return model.capital[m] == prev_capital(m) - buy_p(m) * model.buy[m] \
            + sell_p(m) * model.sell[m]

    model.cash_balance_con = pyo.Constraint(model.M, rule=cash_balance_rule)

    # Pay on delivery: cannot spend more than available cash this month
    def cash_limit_rule(m):
        return buy_p(m) * model.buy[m] <= prev_capital(m) + sell_p(m) * model.sell[m]

    model.cash_limit_con = pyo.Constraint(model.M, rule=cash_limit_rule)

    model.terminal_con = pyo.Constraint(expr=model.stock[3] == terminal_stock)

    def obj_rule(m):
        return m.capital[3]

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"T":[1,2,3],"T0":[0,1,2,3]},"params":["warehouse_capacity","initial_stock","initial_capital","purchase_price[t]","selling_price[t]","terminal_stock_requirement"],"variables":{"buy[t]":"continuous nonnegative, t in T","sell[t]":"continuous nonnegative, t in T","stock[t]":"continuous nonnegative, t in T0","cash[t]":"continuous nonnegative, t in T0"},"constraints":["stock[0] = initial_stock","cash[0] = initial_capital","stock[t] <= warehouse_capacity, t in T0","sell[t] <= stock[t-1], t in T","stock[t] = stock[t-1] + buy[t] - sell[t], t in T","cash[t] = cash[t-1] + selling_price[t]*sell[t] - purchase_price[t]*buy[t], t in T","stock[3] = terminal_stock_requirement"],"objective":"maximize sum(selling_price[t]*sell[t] - purchase_price[t]*buy[t] for t in T)","timing":"Sales use beginning-of-month stock; sales receipts may fund same-month purchases; sales may precede deliveries, so warehouse capacity applies to beginning and ending stock."}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Prices accept three-element sequences or mappings keyed by 1, 2, 3
    (integer keys or their string equivalents). Profit is trading revenue
    minus purchasing expenditure; ending inventory is held without liquidation.
    """
    purchase_data = params["purchase_price"]
    selling_data = params["selling_price"]

    def monthly_value(data, month):
        if isinstance(data, Mapping):
            if month in data:
                return data[month]
            return data[str(month)]
        return data[month - 1]

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 3)
    model.periods = pyo.RangeSet(0, 3)

    model.warehouse_capacity = pyo.Param(
        initialize=params["warehouse_capacity"]
    )
    model.initial_stock = pyo.Param(
        initialize=params["initial_stock"]
    )
    model.initial_capital = pyo.Param(
        initialize=params["initial_capital"]
    )
    model.purchase_price = pyo.Param(
        model.months,
        initialize={
            month: monthly_value(purchase_data, month)
            for month in model.months
        },
    )
    model.selling_price = pyo.Param(
        model.months,
        initialize={
            month: monthly_value(selling_data, month)
            for month in model.months
        },
    )
    model.terminal_stock_requirement = pyo.Param(
        initialize=params["terminal_stock_requirement"]
    )

    model.buy = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.stock = pyo.Var(model.periods, domain=pyo.NonNegativeReals)
    model.cash = pyo.Var(model.periods, domain=pyo.NonNegativeReals)

    model.starting_stock_constraint = pyo.Constraint(
        expr=model.stock[0] == model.initial_stock
    )
    model.starting_cash_constraint = pyo.Constraint(
        expr=model.cash[0] == model.initial_capital
    )

    def capacity_rule(instance, period):
        return instance.stock[period] <= instance.warehouse_capacity

    model.storage_capacity_constraints = pyo.Constraint(
        model.periods, rule=capacity_rule
    )

    def sales_availability_rule(instance, month):
        return instance.sell[month] <= instance.stock[month - 1]

    model.sales_availability_constraints = pyo.Constraint(
        model.months, rule=sales_availability_rule
    )

    def stock_balance_rule(instance, month):
        return instance.stock[month] == (
            instance.stock[month - 1]
            + instance.buy[month]
            - instance.sell[month]
        )

    model.stock_balance_constraints = pyo.Constraint(
        model.months, rule=stock_balance_rule
    )

    def cash_balance_rule(instance, month):
        return instance.cash[month] == (
            instance.cash[month - 1]
            + instance.selling_price[month] * instance.sell[month]
            - instance.purchase_price[month] * instance.buy[month]
        )

    model.cash_balance_constraints = pyo.Constraint(
        model.months, rule=cash_balance_rule
    )

    model.ending_stock_constraint = pyo.Constraint(
        expr=model.stock[3] == model.terminal_stock_requirement
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.selling_price[month] * model.sell[month]
            - model.purchase_price[month] * model.buy[month]
            for month in model.months
        ),
        sense=pyo.maximize,
    )

    # HiGHS can raise RuntimeError when no feasible solution can be loaded.
    # Success is determined solely by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_stock = params["initial_stock"]
    initial_capital = params["initial_capital"]
    purchase_price = params["purchase_price"]   # list of length 3
    selling_price = params["selling_price"]     # list of length 3
    terminal_stock_requirement = params["terminal_stock_requirement"]

    # Months indexed 0,1,2 (Jan, Feb, Mar)
    T = 3

    model = gp.Model("grain_trading")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # buy[t]: units purchased in month t (arrives same month, can sell next month)
    # sell[t]: units sold in month t
    buy  = model.addVars(T, lb=0.0, name="buy")
    sell = model.addVars(T, lb=0.0, name="sell")

    # Stock at end of each month (after purchases arrive and sales depart)
    # sell[t] draws from stock that existed at the START of month t (before new purchases)
    # buy[t] arrives same month but can only be sold the FOLLOWING month
    # So: stock_end[t] = stock_end[t-1] - sell[t] + buy[t]
    # where stock_end[-1] = initial_stock

    # Capital at end of each month
    # capital_end[t] = capital_end[t-1] - buy[t]*purchase_price[t] + sell[t]*selling_price[t]
    # where capital_end[-1] = initial_capital

    # Note: sell[t] draws from the stock available at start of month t,
    # which is stock_end[t-1] (old stock only, since new purchases can't be sold yet).
    # So sell[t] <= stock_end[t-1], which is stock before buy[t] is added for selling purposes.

    # We introduce auxiliary stock variables for clarity
    # stock_before_buy[t] = stock available for selling in month t = stock_end[t-1]
    # stock_end[t] = stock_before_buy[t] - sell[t] + buy[t]

    stock_end = {}
    capital_end = {}

    for t in range(T):
        stock_before = initial_stock if t == 0 else stock_end[t - 1]
        cap_before   = initial_capital if t == 0 else capital_end[t - 1]

        stock_end[t]   = model.addVar(lb=0.0, name=f"stock_end_{t}")
        capital_end[t] = model.addVar(lb=0.0, name=f"capital_end_{t}")

        # Stock balance
        model.addConstr(
            stock_end[t] == stock_before - sell[t] + buy[t],
            name=f"stock_balance_{t}"
        )

        # Capital balance
        model.addConstr(
            capital_end[t] == cap_before
                              - buy[t]  * purchase_price[t]
                              + sell[t] * selling_price[t],
            name=f"capital_balance_{t}"
        )

        # Warehouse capacity: stock after purchases arrive
        model.addConstr(stock_end[t] <= warehouse_capacity, name=f"warehouse_{t}")

        # Can only sell what was in stock BEFORE this month's purchase
        model.addConstr(sell[t] <= stock_before, name=f"sell_limit_{t}")

        # Must have enough capital to pay for purchases
        model.addConstr(
            buy[t] * purchase_price[t] <= cap_before,
            name=f"capital_limit_{t}"
        )

    # Terminal stock requirement
    model.addConstr(stock_end[T - 1] >= terminal_stock_requirement, name="terminal_stock")

    # Objective: maximize total profit = final capital - initial capital
    # (profit = revenue from sales - cost of purchases)
    model.setObjective(capital_end[T - 1] - initial_capital, GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | -700.0 (optimal) | -700.0 (optimal) |
| 1 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 1681.1989859384491 (optimal) | 1681.1989859384466 (optimal) |
| 2 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 8010.689925054371 (optimal) | 7777.8885771378355 (optimal) |
| 3 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 4230.465655631876 (optimal) | 4230.465655631873 (optimal) |
| 4 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 3744.3907012940326 (optimal) | 3705.9548352830097 (optimal) |
| 5 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 1767.027310559295 (optimal) | -357.67826095648525 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | -700.0 (optimal) | -700.0 (optimal) |
| 1 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 1681.1989859384491 (optimal) | 1681.1989859384466 (optimal) |
| 2 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 8010.689925054371 (optimal) | 7777.8885771378355 (optimal) |
| 3 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 4230.465655631876 (optimal) | 4230.465655631873 (optimal) |
| 4 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 3744.3907012940326 (optimal) | 3705.9548352830097 (optimal) |
| 5 | none (crash:File "<PATH>/constraint.py", line 698, in construct \| raise IndexError( \| IndexError: Constraint 'stock_balance_con': Cannot initialize mul) | 1767.027310559295 (optimal) | -357.67826095648525 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 6. industryor_34 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_34` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 34) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 2555.997963020646 |
| Label (original benchmark) | 770 |
| Rules that certify it | gate 2555.997963020646, panel_base_2of3 2555.997963020646, ind_gate 2555.997963020646 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
There are 8 villages in Tuanjie Township, with their respective coordinates and the number of elementary school students shown in Table 5-14.

Table 5-14
\begin{tabular}{c|c|c|c}
\hline Village Code & \multicolumn{2}{|c|}{Coordinate Position} & \multirow{2}{*}{Number of Elementary School Students} \
\cline {2-4} 1 & $x$ & $y$ & 60 \
2 & 10 & 0 & 80 \
3 & 12 & 3 & 100 \
4 & 14 & 15 & 120 \
5 & 16 & 13 & 80 \
6 & 18 & 9 & 60 \
7 & 8 & 6 & 40 \
8 & 6 & 12 & 80 \
\hline
\end{tabular}

Considering the economies of scale for the schools, it is planned to build one elementary school in each of the two villages. Where should the two schools be built to minimize the walking distance for the elementary school students? (The walking distance for the students is calculated based on the Euclidean distance between the two villages.)
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"x_coords": {"base":[0,10,12,14,16,18,8,6],"perturb":{"mode":"abs","lo":-5.0,"hi":25.0,"integer":false}}
"y_coords": {"base":[0,0,3,15,13,9,6,12],"perturb":{"mode":"abs","lo":-5.0,"hi":25.0,"integer":false}}
"student_counts": {"base":[60,80,100,120,80,60,40,80],"perturb":{"mode":"rel","r":0.5}}
"num_schools": {"base":2,"perturb":{"mode":"abs","lo":2.0,"hi":2.0,"integer":true}}
```

Warnings:

```
[num_schools] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    x_coords = params["x_coords"]
    y_coords = params["y_coords"]
    student_counts = params["student_counts"]
    num_schools = params["num_schools"]

    n = len(x_coords)
    villages = range(n)

    model = pyo.ConcreteModel()

    model.build = pyo.Var(villages, domain=pyo.Binary)

    model.total_cost = pyo.Objective(
        expr=sum(
            student_counts[i]
            * min(
                ((x_coords[i] - x_coords[j]) ** 2 + (y_coords[i] - y_coords[j]) ** 2) ** 0.5
                for j in villages
                if j != i
            )
            * model.build[i]
            for i in villages
        ),
        sense=pyo.minimize,
    )

    model.num_schools_constraint = pyo.Constraint(
        expr=sum(model.build[i] for i in villages) == num_schools
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"V":"0,...,7"},"params":{"x_coords":"village x-coordinates","y_coords":"village y-coordinates","student_counts":"students per village","num_schools":"required number of schools","distance[i,j]":"Euclidean distance derived from x_coords and y_coords"},"variables":{"school[j]":"binary","assign[i,j]":"binary"},"constraints":["sum_j school[j] = num_schools","sum_j assign[i,j] = 1 for each i","assign[i,j] <= school[j] for each i,j"],"objective":"minimize sum_i sum_j student_counts[i] * distance[i,j] * assign[i,j]"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    x_coords = params["x_coords"]
    y_coords = params["y_coords"]
    student_counts = params["student_counts"]
    num_schools = params["num_schools"]

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, 7)

    model.distance = pyo.Param(
        model.V,
        model.V,
        initialize={
            (i, j): math.hypot(
                x_coords[i] - x_coords[j],
                y_coords[i] - y_coords[j],
            )
            for i in model.V
            for j in model.V
        },
        within=pyo.NonNegativeReals,
    )
    model.students = pyo.Param(
        model.V,
        initialize={i: student_counts[i] for i in model.V},
        within=pyo.NonNegativeReals,
    )
    model.required_schools = pyo.Param(
        initialize=num_schools,
        within=pyo.NonNegativeIntegers,
    )

    model.school = pyo.Var(model.V, domain=pyo.Binary)
    model.assign = pyo.Var(model.V, model.V, domain=pyo.Binary)

    model.school_count = pyo.Constraint(
        expr=sum(model.school[j] for j in model.V)
        == model.required_schools
    )

    def assignment_rule(instance, i):
        return sum(instance.assign[i, j] for j in instance.V) == 1

    model.assignment_constraints = pyo.Constraint(
        model.V, rule=assignment_rule
    )

    def open_school_rule(instance, i, j):
        return instance.assign[i, j] <= instance.school[j]

    model.open_school_constraints = pyo.Constraint(
        model.V, model.V, rule=open_school_rule
    )

    model.total_walking_distance = pyo.Objective(
        expr=sum(
            model.students[i] * model.distance[i, j] * model.assign[i, j]
            for i in model.V
            for j in model.V
        ),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_walking_distance))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solve_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    x_coords = params["x_coords"]
    y_coords = params["y_coords"]
    student_counts = params["student_counts"]
    num_schools = params["num_schools"]

    n = len(x_coords)
    villages = list(range(n))

    # Precompute Euclidean distances between all pairs of villages
    dist = {}
    for i in villages:
        for j in villages:
            dx = x_coords[i] - x_coords[j]
            dy = y_coords[i] - y_coords[j]
            dist[i, j] = math.sqrt(dx * dx + dy * dy)

    model = gp.Model("school_location")
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if a school is built in village j
    y = model.addVars(villages, vtype=GRB.BINARY, name="y")

    # x_var[i, j] = 1 if village i is assigned to school in village j
    x_var = model.addVars(villages, villages, vtype=GRB.BINARY, name="x")

    # Objective: minimize total weighted walking distance
    model.setObjective(
        gp.quicksum(student_counts[i] * dist[i, j] * x_var[i, j]
                    for i in villages for j in villages),
        GRB.MINIMIZE
    )

    # Exactly num_schools schools are built
    model.addConstr(gp.quicksum(y[j] for j in villages) == num_schools, "num_schools")

    # Each village is assigned to exactly one school
    for i in villages:
        model.addConstr(gp.quicksum(x_var[i, j] for j in villages) == 1, f"assign_{i}")

    # Village i can only be assigned to village j if a school is built there
    for i in villages:
        for j in villages:
            model.addConstr(x_var[i, j] <= y[j], f"link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 426.2741699796952 (optimal) | 2555.997963020646 (optimal) | 2555.9979630206453 (optimal) |
| 1 | 401.65645289121665 (optimal) | 2759.7904310337717 (optimal) | 2759.7904310337717 (optimal) |
| 2 | 136.53252616200115 (optimal) | 1732.7209203118402 (optimal) | 1732.7209203118405 (optimal) |
| 3 | 430.92651824461893 (optimal) | 2600.1329308055074 (optimal) | 2600.1329308055074 (optimal) |
| 4 | 154.7447314303255 (optimal) | 2935.1091790791033 (optimal) | 2935.1091790791033 (optimal) |
| 5 | 407.72390105266754 (optimal) | 3055.13523639085 (optimal) | 3055.13523639085 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 426.2741699796952 (optimal) | 2555.997963020646 (optimal) | 2555.9979630206453 (optimal) |
| 1 | 481.9877434694599 (optimal) | 3311.748517240526 (optimal) | 3311.748517240526 (optimal) |
| 2 | 163.8390313944013 (optimal) | 2079.265104374208 (optimal) | 2079.265104374208 (optimal) |
| 3 | 517.111821893543 (optimal) | 3120.1595169666093 (optimal) | 3120.1595169666093 (optimal) |
| 4 | 185.6936777163906 (optimal) | 3522.131014894924 (optimal) | 3522.131014894924 (optimal) |
| 5 | 489.26868126320124 (optimal) | 3666.1622836690203 (optimal) | 3666.16228366902 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "x_coords", "evidence": "the x-coordinate of village 1 is blank in the table (only 10, 12, 14, 16, 18, 8, 6 are given); the blank cell is not a stated value"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"x_coords","evidence":"Village 1's row gives \"$x$ & $y$ & 60\"; no numeric x-coordinate is stated."},{"parameter":"y_coords","evidence":"Village 1's row gives \"$x$ & $y$ & 60\"; no numeric y-coordinate is stated."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

````json
Looking at the table carefully:

- Village 1's x-coordinate is missing (the table header row appears malformed, with the "60" students entry on the same row as the column headers, leaving x and y blank for village 1).
- Village 1's y-coordinate: the extracted value is 0, but the statement does not provide it.

The x-coordinate placeholder of 0 and y-coordinate of 0 for village 1 are both not stated. The extraction note acknowledges the x issue but silently fills in y=0 as well without flagging it.

```json
{
  "mismatch": [],
  "not_stated": [
    {
      "parameter": "x_coords",
      "evidence": "Village 1's x-coordinate is absent from the table; value 0 is a placeholder not given in the statement"
    },
    {
      "parameter": "y_coords",
      "evidence": "Village 1's y-coordinate is absent from the table; value 0 is a placeholder not given in the statement"
    }
  ]
}
```
````


## 7. industryor_41 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_41` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 41) |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 2630369.9999999995 |
| Label (original benchmark) | 1581550 |
| Rules that certify it | gate 2630369.9999999995, panel_base_2of3 2630369.9999999995, ind_gate 2630369.9999999995 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A company plans to produce three products, $A_{1}, A_{2}, A_{3}$, within a four-month timeframe (January to April). The demand for the products is shown in the table below:

| Demand | January | February | March | April |
| :---: | :---: | :---: | :---: | :---: |
| $A_{1}$ | 5300 | 1200 | 7400 | 5300 |
| $A_{2}$ | 4500 | 5400 | 6500 | 7200 |
| $A_{3}$ | 4400 | 6700 | 12500 | 13200 |

The prices, production costs, production quotas, activation costs, and minimum batch sizes (refer to the definitions in Exercise 4.3) are as follows:

| Product | $A_{1}$ | $A_{2}$ | $A_{3}$ |
| :---: | :---: | :---: | :---: |
| Unit Price | $\\$ 124$ | $\\$ 109$ | $\\$ 115$ |
| Activation Cost | $\\$ 150000$ | $\\$ 150000$ | $\\$ 100000$ |
| Production Cost | $\\$ 73.30$ | $\\$ 52.90$ | $\\$ 65.40$ |
| Production Quota | 500 | 450 | 550 |
| Minimum Batch Size | 20 | 20 | 16 |

January has 23 production days, February has 20, March has 23, and April has 22. The activation status of the production lines can be changed each month. The minimum batch size is calculated on a monthly basis.

In addition, storage space can be rented monthly at a cost of $\\$ 3.50$ for $A_{1}$, $\\$ 4.00$ for $A_{2}$, and $\\$ 3.00$ for $A_{3}$. Each product takes up the same amount of storage space. The total available capacity is 800 units.

Write a mathematical program to maximize revenue.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"demand_A1": {"base":[5300,1200,7400,5300],"perturb":{"mode":"rel","r":0.5}}
"demand_A2": {"base":[4500,5400,6500,7200],"perturb":{"mode":"rel","r":0.5}}
"demand_A3": {"base":[4400,6700,12500,13200],"perturb":{"mode":"rel","r":0.5}}
"price": {"base":[124,109,115],"perturb":{"mode":"rel","r":0.4}}
"production_cost": {"base":[73.3,52.9,65.4],"perturb":{"mode":"rel","r":0.4}}
"activation_cost": {"base":[150000,150000,100000],"perturb":{"mode":"rel","r":0.6}}
"production_quota": {"base":[500,450,550],"perturb":{"mode":"rel","r":0.3}}
"min_batch_size": {"base":[20,20,16],"perturb":{"mode":"rel","r":0.5}}
"production_days": {"base":[23,20,23,22],"perturb":{"mode":"rel","r":0.2}}
"storage_cost": {"base":[3.5,4.0,3.0],"perturb":{"mode":"rel","r":0.5}}
"storage_capacity": {"base":800,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    products = ['A1', 'A2', 'A3']
    months = ['Jan', 'Feb', 'Mar', 'Apr']

    demand = {
        'A1': params["demand_A1"],
        'A2': params["demand_A2"],
        'A3': params["demand_A3"],
    }
    price = dict(zip(products, params["price"]))
    prod_cost = dict(zip(products, params["production_cost"]))
    act_cost = dict(zip(products, params["activation_cost"]))
    quota = dict(zip(products, params["production_quota"]))
    min_batch = dict(zip(products, params["min_batch_size"]))
    days = dict(zip(months, params["production_days"]))
    stor_cost = dict(zip(products, params["storage_cost"]))
    stor_cap = params["storage_capacity"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.M = pyo.Set(initialize=months)

    # Decision variables
    model.prod = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.active_flag = pyo.Var(model.P, model.M, domain=pyo.Binary)
    model.stock = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)

    # Inventory balance
    def balance_rule(model, p, m):
        idx = months.index(m)
        prev_stock = model.stock[p, months[idx - 1]] if idx > 0 else 0
        return model.stock[p, m] == prev_stock + model.prod[p, m] - demand[p][idx]
    model.balance = pyo.Constraint(model.P, model.M, rule=balance_rule)

    # Quota & minimum batch linked to activation
    def quota_rule(model, p, m):
        return model.prod[p, m] <= quota[p] * days[m] * model.active_flag[p, m]
    model.quota_con = pyo.Constraint(model.P, model.M, rule=quota_rule)

    def batch_rule(model, p, m):
        return model.prod[p, m] >= min_batch[p] * days[m] * model.active_flag[p, m]
    model.batch_con = pyo.Constraint(model.P, model.M, rule=batch_rule)

    # Storage capacity
    def storage_rule(model, m):
        return sum(model.stock[p, m] for p in products) <= stor_cap
    model.storage_con = pyo.Constraint(model.M, rule=storage_rule)

    # Revenue objective
    revenue = sum(price[p] * demand[p][i] for p in products for i in range(len(months)))
    storage_total = sum(stor_cost[p] * model.stock[p, m] for p in products for m in months)
    prod_total = sum(prod_cost[p] * model.prod[p, m] for p in products for m in months)
    act_total = sum(act_cost[p] * model.active_flag[p, m] for p in products for m in months)

    model.obj = pyo.Objective(
        expr=revenue - prod_total - act_total - storage_total,
        sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"P":["A1","A2","A3"],"T":[0,1,2,3]},"params":{"demand_A1":"length-4 array","demand_A2":"length-4 array","demand_A3":"length-4 array","price":"length-3 array","production_cost":"length-3 array","activation_cost":"length-3 array","production_quota":"length-3 array","min_batch_size":"length-3 array","production_days":"length-4 array","storage_cost":"length-3 array","storage_capacity":"scalar"},"interpretation":{"quota":"daily quota multiplied by production_days, as implied by the production calendar","minimum_batch":"monthly minimum","demand":"sales upper bound; unmet demand is lost","initial_inventory":0,"revenue":"sales revenue minus production, activation, and storage costs"},"variables":{"production[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous; end-of-month inventory","line_on[p,t]":"binary"},"constraints":["sales[p,t] <= demand[p,t]","production[p,t] <= production_quota[p]*production_days[t]*line_on[p,t]","production[p,t] >= min_batch_size[p]*line_on[p,t]","inventory[p,t] = (0 if t=0 else inventory[p,t-1]) + production[p,t] - sales[p,t]","sum_p inventory[p,t] <= storage_capacity"],"objective":"maximize sum_(p,t)(price[p]*sales[p,t] - production_cost[p]*production[p,t] - activation_cost[p]*line_on[p,t] - storage_cost[p]*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Product arrays are ordered A1, A2, A3.
    Monthly arrays are ordered January, February, March, April.

    Production quotas are interpreted as daily limits, multiplied by the
    supplied production days. Minimum batch sizes apply monthly.
    """
    products = ("A1", "A2", "A3")
    months = range(4)

    demand_arrays = {
        "A1": params["demand_A1"],
        "A2": params["demand_A2"],
        "A3": params["demand_A3"],
    }
    prices = params["price"]
    production_costs = params["production_cost"]
    activation_costs = params["activation_cost"]
    quotas = params["production_quota"]
    minimum_batches = params["min_batch_size"]
    days = params["production_days"]
    storage_costs = params["storage_cost"]
    storage_capacity = params["storage_capacity"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.months = pyo.Set(initialize=months, ordered=True)

    model.demand = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): demand_arrays[product][month]
            for product in products
            for month in months
        },
        within=pyo.NonNegativeReals,
    )

    product_parameters = (
        ("unit_price", prices),
        ("unit_production_cost", production_costs),
        ("line_activation_cost", activation_costs),
        ("daily_quota", quotas),
        ("minimum_batch", minimum_batches),
        ("unit_storage_cost", storage_costs),
    )
    for component_name, values in product_parameters:
        model.add_component(
            component_name,
            pyo.Param(
                model.products,
                initialize={
                    product: values[position]
                    for position, product in enumerate(products)
                },
                within=pyo.NonNegativeReals,
            ),
        )

    model.days_available = pyo.Param(
        model.months,
        initialize={month: days[month] for month in months},
        within=pyo.NonNegativeReals,
    )
    model.inventory_capacity = pyo.Param(
        initialize=storage_capacity,
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.line_on = pyo.Var(
        model.products, model.months, domain=pyo.Binary
    )

    def sales_limit_rule(instance, product, month):
        return instance.sales[product, month] <= instance.demand[product, month]

    model.sales_limit = pyo.Constraint(
        model.products, model.months, rule=sales_limit_rule
    )

    def production_limit_rule(instance, product, month):
        return instance.production[product, month] <= (
            instance.daily_quota[product]
            * instance.days_available[month]
            * instance.line_on[product, month]
        )

    model.production_limit = pyo.Constraint(
        model.products, model.months, rule=production_limit_rule
    )

    def minimum_batch_rule(instance, product, month):
        return instance.production[product, month] >= (
            instance.minimum_batch[product] * instance.line_on[product, month]
        )

    model.batch_requirement = pyo.Constraint(
        model.products, model.months, rule=minimum_batch_rule
    )

    def inventory_balance_rule(instance, product, month):
        previous_inventory = (
            0 if month == 0 else instance.inventory[product, month - 1]
        )
        return instance.inventory[product, month] == (
            previous_inventory
            + instance.production[product, month]
            - instance.sales[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def storage_limit_rule(instance, month):
        return (
            sum(
                instance.inventory[product, month]
                for product in instance.products
            )
            <= instance.inventory_capacity
        )

    model.storage_limit = pyo.Constraint(
        model.months, rule=storage_limit_rule
    )

    model.net_revenue = pyo.Objective(
        expr=sum(
            model.unit_price[product] * model.sales[product, month]
            - model.unit_production_cost[product]
            * model.production[product, month]
            - model.line_activation_cost[product]
            * model.line_on[product, month]
            - model.unit_storage_cost[product]
            * model.inventory[product, month]
            for product in model.products
            for month in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Continue to objective retrieval only for the known no-solution error.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.net_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_A1 = params["demand_A1"]           # list of 4
    demand_A2 = params["demand_A2"]           # list of 4
    demand_A3 = params["demand_A3"]           # list of 4
    price = params["price"]                   # list of 3
    production_cost = params["production_cost"]  # list of 3
    activation_cost = params["activation_cost"]  # list of 3
    production_quota = params["production_quota"]  # list of 3
    min_batch_size = params["min_batch_size"]     # list of 3
    production_days = params["production_days"]   # list of 4
    storage_cost = params["storage_cost"]         # list of 3
    storage_capacity = params["storage_capacity"] # scalar

    num_products = 3
    num_months = 4
    products = range(num_products)
    months = range(num_months)

    demand = [demand_A1, demand_A2, demand_A3]

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # x[i][t]: units produced of product i in month t
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{t}") for t in months] for i in products]

    # s[i][t]: units stored of product i at end of month t
    s = [[model.addVar(lb=0.0, name=f"s_{i}_{t}") for t in months] for i in products]

    # q[i][t]: units sold of product i in month t (sales <= demand)
    q = [[model.addVar(lb=0.0, name=f"q_{i}_{t}") for t in months] for i in products]

    # y[i][t]: binary, 1 if production line i is active in month t
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{t}") for t in months] for i in products]

    # Inventory balance: prev_stock + x[i][t] - s[i][t] = q[i][t]
    # (produced + carried in = sold + carried out)
    for i in products:
        for t in months:
            prev_stock = s[i][t - 1] if t > 0 else 0.0
            model.addConstr(
                prev_stock + x[i][t] - s[i][t] == q[i][t],
                name=f"balance_{i}_{t}"
            )

    # Sales cannot exceed demand
    for i in products:
        for t in months:
            model.addConstr(
                q[i][t] <= demand[i][t],
                name=f"demand_{i}_{t}"
            )

    # Production quota: x[i][t] <= production_quota[i] * production_days[t] * y[i][t]
    for i in products:
        for t in months:
            model.addConstr(
                x[i][t] <= production_quota[i] * production_days[t] * y[i][t],
                name=f"quota_{i}_{t}"
            )

    # Minimum batch size: x[i][t] >= min_batch_size[i] * y[i][t]
    for i in products:
        for t in months:
            model.addConstr(
                x[i][t] >= min_batch_size[i] * y[i][t],
                name=f"min_batch_{i}_{t}"
            )

    # Storage capacity: sum over products of s[i][t] <= storage_capacity for each month
    for t in months:
        model.addConstr(
            gp.quicksum(s[i][t] for i in products) <= storage_capacity,
            name=f"storage_cap_{t}"
        )

    # Objective: maximize profit = revenue - production costs - activation costs - storage costs
    revenue = gp.quicksum(
        price[i] * q[i][t]
        for i in products for t in months
    )

    prod_costs = gp.quicksum(
        production_cost[i] * x[i][t]
        for i in products for t in months
    )

    act_costs = gp.quicksum(
        activation_cost[i] * y[i][t]
        for i in products for t in months
    )

    stor_costs = gp.quicksum(
        storage_cost[i] * s[i][t]
        for i in products for t in months
    )

    model.setObjective(revenue - prod_costs - act_costs - stor_costs, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 2630369.9999999995 (optimal) | 2630370.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 1903457.7558276744 (optimal) | 1903457.7558276744 (optimal) |
| 2 | 1571775.148149882 (optimal) | 1768748.975750751 (optimal) | 1768748.975750751 (optimal) |
| 3 | none (infeasible_or_unbounded) | 3795806.9763915306 (optimal) | 3795806.976391531 (optimal) |
| 4 | none (infeasible_or_unbounded) | 1868200.9294481971 (optimal) | 1868200.9294481971 (optimal) |
| 5 | none (infeasible_or_unbounded) | 2183265.8914946085 (optimal) | 2183265.891494609 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 2630369.9999999995 (optimal) | 2630370.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 1903457.7558276744 (optimal) | 1903457.7558276744 (optimal) |
| 2 | 1571775.148149882 (optimal) | 1768748.975750751 (optimal) | 1768748.975750751 (optimal) |
| 3 | none (infeasible_or_unbounded) | 3795806.9763915306 (optimal) | 3795806.976391531 (optimal) |
| 4 | none (infeasible_or_unbounded) | 1868200.9294481971 (optimal) | 1868200.9294481971 (optimal) |
| 5 | none (infeasible_or_unbounded) | 2183265.8914946085 (optimal) | 2183265.891494609 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{
  "mismatch": [],
  "not_stated": []
}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 8. industryor_47 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_47` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 47) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 4913500.0 |
| Label (original benchmark) | 5069500 |
| Rules that certify it | gate 4913500.0, panel_base_2of3 4913500.0, ind_gate 4913500.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
The market demand for products I and II is as follows: Product I requires 10,000 units per month from January to April, 30,000 units per month from May to September, and 100,000 units per month from October to December. Product II requires 15,000 units per month from March to September and 50,000 units per month for the other months. The production cost for these two products is as follows: Product I costs $5 per unit to produce from January to May and $4.50 per unit to produce from June to December. Product II costs $8 per unit to produce from January to May and $7 per unit to produce from June to December. The total production capacity for both products should not exceed 120,000 units per month. Product I occupies 0.2 cubic meters per unit, while Product II occupies 0.4 cubic meters per unit. The warehouse capacity of the factory is 15,000 cubic meters. If the warehouse is not sufficient, the factory can rent additional space from an external facility. If occupying 1 cubic meter of the factory's storage space incurs a cost of $1 per month, and renting storage space from an external facility incurs an additional cost of $1.5 per month, how should the factory arrange its production to minimize the total production cost including storage fees while meeting market demand?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"demand_I": {"base":[10000,10000,10000,10000,30000,30000,30000,30000,30000,100000,100000,100000],"perturb":{"mode":"rel","r":0.3}}
"demand_II": {"base":[50000,50000,15000,15000,15000,15000,15000,15000,15000,50000,50000,50000],"perturb":{"mode":"rel","r":0.3}}
"cost_I": {"base":[5,5,5,5,5,4.5,4.5,4.5,4.5,4.5,4.5,4.5],"perturb":{"mode":"rel","r":0.2}}
"cost_II": {"base":[8,8,8,8,8,7,7,7,7,7,7,7],"perturb":{"mode":"rel","r":0.2}}
"production_capacity": {"base":120000,"perturb":{"mode":"abs","lo":80000.0,"hi":200000.0,"integer":true}}
"warehouse_capacity": {"base":15000,"perturb":{"mode":"abs","lo":5000.0,"hi":30000.0,"integer":true}}
"space_I": {"base":0.2,"perturb":{"mode":"abs","lo":0.1,"hi":0.35,"integer":false}}
"space_II": {"base":0.4,"perturb":{"mode":"abs","lo":0.2,"hi":0.7,"integer":false}}
"own_storage_cost": {"base":1,"perturb":{"mode":"abs","lo":0.5,"hi":2.0,"integer":false}}
"external_storage_cost": {"base":1.5,"perturb":{"mode":"abs","lo":1.0,"hi":3.0,"integer":false}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_I = params["demand_I"]
    demand_II = params["demand_II"]
    cost_I = params["cost_I"]
    cost_II = params["cost_II"]
    production_capacity = params["production_capacity"]
    warehouse_capacity = params["warehouse_capacity"]
    space_I = params["space_I"]
    space_II = params["space_II"]
    own_storage_cost = params["own_storage_cost"]
    external_storage_cost = params["external_storage_cost"]

    T = list(range(12))

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=T, ordered=True)

    model.xI = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.xII = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.ext = pyo.Var(model.T, within=pyo.NonNegativeReals)

    def prod_cap_rule(m, t):
        return m.xI[t] + m.xII[t] <= production_capacity
    model.prod_cap = pyo.Constraint(model.T, rule=prod_cap_rule)

    def demand_I_rule(m, t):
        return m.xI[t] >= demand_I[t]
    model.demand_I_c = pyo.Constraint(model.T, rule=demand_I_rule)

    def demand_II_rule(m, t):
        return m.xII[t] >= demand_II[t]
    model.demand_II_c = pyo.Constraint(model.T, rule=demand_II_rule)

    # Storage: only the portion within own warehouse capacity incurs own_storage_cost,
    # any overflow is rented externally at external_storage_cost.
    def storage_rule(m, t):
        used = space_I * m.xI[t] + space_II * m.xII[t]
        return used <= warehouse_capacity + m.ext[t]
    model.storage_c = pyo.Constraint(model.T, rule=storage_rule)

    def obj_rule(m):
        return sum(
            cost_I[t] * m.xI[t]
            + cost_II[t] * m.xII[t]
            + own_storage_cost * (space_I * m.xI[t] + space_II * m.xII[t])
            + external_storage_cost * m.ext[t]
            for t in m.T
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"P":["I","II"],"T":[1,2,3,4,5,6,7,8,9,10,11,12]},"params":{"demand_I":"12 monthly values","demand_II":"12 monthly values","cost_I":"12 monthly values","cost_II":"12 monthly values","production_capacity":"scalar","warehouse_capacity":"scalar","space_I":"scalar","space_II":"scalar","own_storage_cost":"scalar","external_storage_cost":"scalar additional external-space charge"},"variables":{"production[p,t]":"nonnegative continuous units","inventory[p,t]":"nonnegative continuous end-of-month units","own_space[t]":"nonnegative continuous cubic meters","external_space[t]":"nonnegative continuous cubic meters"},"constraints":["production[p,t]+(inventory[p,t-1] if t>1 else 0)=demand[p,t]+inventory[p,t]","sum_p production[p,t]<=production_capacity","own_space[t]+external_space[t]=sum_p space[p]*inventory[p,t]","own_space[t]<=warehouse_capacity"],"objective":"min sum_t(sum_p cost[p,t]*production[p,t]+own_storage_cost*(own_space[t]+external_space[t])+external_storage_cost*external_space[t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using monthly sequences ordered January through December.

    Initial inventory is zero. Storage charges apply to end-of-month
    inventory. External space incurs the base storage charge plus the
    additional external storage charge.
    """
    demand_by_product = {
        "I": params["demand_I"],
        "II": params["demand_II"],
    }
    cost_by_product = {
        "I": params["cost_I"],
        "II": params["cost_II"],
    }
    space_by_product = {
        "I": params["space_I"],
        "II": params["space_II"],
    }

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["I", "II"], ordered=True)
    model.months = pyo.RangeSet(1, 12)

    model.demand = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: (
            demand_by_product[product][month - 1]
        ),
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: (
            cost_by_product[product][month - 1]
        ),
        within=pyo.NonNegativeReals,
    )
    model.unit_space = pyo.Param(
        model.products,
        initialize=space_by_product,
        within=pyo.NonNegativeReals,
    )
    model.production_capacity = pyo.Param(
        initialize=params["production_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.warehouse_capacity = pyo.Param(
        initialize=params["warehouse_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.own_storage_cost = pyo.Param(
        initialize=params["own_storage_cost"],
        within=pyo.NonNegativeReals,
    )
    model.external_storage_cost = pyo.Param(
        initialize=params["external_storage_cost"],
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.own_space = pyo.Var(
        model.months, domain=pyo.NonNegativeReals
    )
    model.external_space = pyo.Var(
        model.months, domain=pyo.NonNegativeReals
    )

    def inventory_balance_rule(mdl, product, month):
        previous_inventory = (
            0 if month == 1 else mdl.inventory[product, month - 1]
        )
        return (
            mdl.production[product, month] + previous_inventory
            == mdl.demand[product, month] + mdl.inventory[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def production_limit_rule(mdl, month):
        return (
            sum(mdl.production[product, month] for product in mdl.products)
            <= mdl.production_capacity
        )

    model.production_limit = pyo.Constraint(
        model.months, rule=production_limit_rule
    )

    def storage_balance_rule(mdl, month):
        return (
            mdl.own_space[month] + mdl.external_space[month]
            == sum(
                mdl.unit_space[product] * mdl.inventory[product, month]
                for product in mdl.products
            )
        )

    model.storage_balance = pyo.Constraint(
        model.months, rule=storage_balance_rule
    )

    model.own_storage_limit = pyo.Constraint(
        model.months,
        rule=lambda mdl, month: (
            mdl.own_space[month] <= mdl.warehouse_capacity
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            sum(
                model.unit_cost[product, month]
                * model.production[product, month]
                for product in model.products
            )
            + model.own_storage_cost
            * (model.own_space[month] + model.external_space[month])
            + model.external_storage_cost * model.external_space[month]
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_I = params["demand_I"]        # list of 12
    demand_II = params["demand_II"]      # list of 12
    cost_I = params["cost_I"]            # list of 12
    cost_II = params["cost_II"]          # list of 12
    production_capacity = params["production_capacity"]
    warehouse_capacity = params["warehouse_capacity"]
    space_I = params["space_I"]
    space_II = params["space_II"]
    own_storage_cost = params["own_storage_cost"]
    external_storage_cost = params["external_storage_cost"]

    months = range(12)  # 0..11

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # prod_I[t], prod_II[t]: units produced in month t
    prod_I = model.addVars(months, lb=0.0, name="prod_I")
    prod_II = model.addVars(months, lb=0.0, name="prod_II")

    # inv_I[t], inv_II[t]: inventory at end of month t (units)
    inv_I = model.addVars(months, lb=0.0, name="inv_I")
    inv_II = model.addVars(months, lb=0.0, name="inv_II")

    # own_space[t]: cubic meters used in own warehouse at end of month t
    # ext_space[t]: cubic meters rented externally at end of month t
    own_space = model.addVars(months, lb=0.0, name="own_space")
    ext_space = model.addVars(months, lb=0.0, name="ext_space")

    # Inventory balance constraints (starting inventory = 0)
    for t in months:
        if t == 0:
            model.addConstr(inv_I[t] == prod_I[t] - demand_I[t], name=f"inv_bal_I_{t}")
            model.addConstr(inv_II[t] == prod_II[t] - demand_II[t], name=f"inv_bal_II_{t}")
        else:
            model.addConstr(inv_I[t] == inv_I[t-1] + prod_I[t] - demand_I[t], name=f"inv_bal_I_{t}")
            model.addConstr(inv_II[t] == inv_II[t-1] + prod_II[t] - demand_II[t], name=f"inv_bal_II_{t}")

    # Production capacity constraints
    for t in months:
        model.addConstr(prod_I[t] + prod_II[t] <= production_capacity, name=f"prod_cap_{t}")

    # Storage space linkage: total space = own + external
    for t in months:
        total_space_used = space_I * inv_I[t] + space_II * inv_II[t]
        model.addConstr(own_space[t] + ext_space[t] == total_space_used, name=f"storage_link_{t}")

    # Own warehouse capacity
    for t in months:
        model.addConstr(own_space[t] <= warehouse_capacity, name=f"own_cap_{t}")

    # Objective: production costs + own storage costs + external storage costs
    production_cost = gp.quicksum(
        cost_I[t] * prod_I[t] + cost_II[t] * prod_II[t]
        for t in months
    )
    storage_cost = gp.quicksum(
        own_storage_cost * own_space[t] + (own_storage_cost + external_storage_cost) * ext_space[t]
        for t in months
    )

    model.setObjective(production_cost + storage_cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}


if __name__ == "__main__":
    params = {
        "demand_I": [10000, 10000, 10000, 10000,
                     30000, 30000, 30000, 30000, 30000,
                     100000, 100000, 100000],
        "demand_II": [50000, 50000,
                      15000, 15000, 15000, 15000, 15000, 15000, 15000,
                      50000, 50000, 50000],
        "cost_I": [5, 5, 5, 5, 5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5],
        "cost_II": [8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7],
        "production_capacity": 120000,
        "warehouse_capacity": 15000,
        "space_I": 0.2,
        "space_II": 0.4,
        "own_storage_cost": 1.0,
        "external_storage_cost": 1.5,
    }
    result = solve(params)
    print(result)
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 4913500.0 (optimal) | 4913500.0 (optimal) |
| 1 | 4751144.627013119 (optimal) | 4320408.073886922 (optimal) | 4320408.073886923 (optimal) |
| 2 | none (infeasible_or_unbounded) | 4623593.39990729 (optimal) | 4623593.399907289 (optimal) |
| 3 | none (infeasible_or_unbounded) | 4607263.705836503 (optimal) | 4607263.705836503 (optimal) |
| 4 | none (infeasible_or_unbounded) | 4881314.318248041 (optimal) | 4881314.318248042 (optimal) |
| 5 | 5600898.05621987 (optimal) | 4845007.888074968 (optimal) | 4845007.888074968 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 4913500.0 (optimal) | 4913500.0 (optimal) |
| 1 | 4751144.627013119 (optimal) | 4320408.073886922 (optimal) | 4320408.073886923 (optimal) |
| 2 | none (infeasible_or_unbounded) | 4623593.39990729 (optimal) | 4623593.399907289 (optimal) |
| 3 | none (infeasible_or_unbounded) | 4607263.705836503 (optimal) | 4607263.705836503 (optimal) |
| 4 | none (infeasible_or_unbounded) | 4881314.318248041 (optimal) | 4881314.318248042 (optimal) |
| 5 | 5600898.05621987 (optimal) | 4845007.888074968 (optimal) | 4845007.888074968 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
I need to check each parameter against the statement carefully.

**demand_I**: Statement says January to April = 10,000, May to September = 30,000, October to December = 100,000. That gives months 1–4 = 10,000, months 5–9 = 30,000, months 10–12 = 100,000. Extracted matches.

**demand_II**: Statement says March to September = 15,000, other months = 50,000. "Other months" = January, February, October, November, December. So months 1–2 = 50,000, months 3–9 = 15,000, months 10–12 = 50,000. Extracted matches.

**cost_I**: Statement says January to May = $5, June to December = $4.50. That is months 1–5 = 5, months 6–12 = 4.5. Extracted has months 1–5 = 5 and months 6–12 = 4.5. Matches.

**cost_II**: Statement says January to May = $8, June to December = $7. Months 1–5 = 8, months 6–12 = 7. Extracted has months 1–5 = 8 and months 6–12 = 7. Matches.

**production_capacity**: 120,000. Matches.

**warehouse_capacity**: 15,000. Matches.

**space_I**: 0.2. Matches.

**space_II**: 0.4. Matches.

**own_storage_cost**: Statement says "occupying 1 cubic meter of the factory's storage space incurs a cost of $1 per month." Matches.

**external_storage_cost**: Statement says renting external space incurs "an additional cost of $1.5 per month." The extracted value is 1.5 as the full rental cost, but the statement says this is an *additional* cost on top of the $1 own storage cost, meaning the total external cost is $2.5/m²/month, not $1.5. However, this is a modeling interpretation question — the statement says "additional cost of $1.5," which could mean the marginal extra cost is 1.5. The extracted value of 1.5 matches the stated number, so no mismatch in the number itself.

All parameters match the statement.

```json
{"mismatch": [], "not_stated": []}
```
````


## 9. industryor_48 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_48` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 48) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 156000.0 |
| Label (original benchmark) | 105.52 |
| Rules that certify it | gate 156000.0, panel_base_2of3 156000.0, ind_gate 156000.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A factory produces two types of food, I and II. There are currently 50 skilled workers. It is known that one skilled worker can produce food I at a rate of 10 kg/h or food II at a rate of 6 kg/h. According to the contract, the demand for these two types of food will sharply increase each week, as shown in Table 1-11. To meet this demand, the factory plans to train 50 new workers by the end of the 8th week, with production in two shifts. It is known that one worker works 40 hours per week, and a skilled worker can train no more than three new workers in two weeks (during the training period, skilled workers and trainees do not participate in production). Skilled workers earn a weekly salary of 360 yuan, trainees earn a weekly salary of 120 yuan during the training period, and a weekly salary of 240 yuan after training is completed. Their production efficiency is the same as that of skilled workers. During the training transition period, many skilled workers are willing to work overtime. The factory decides to arrange for some workers to work 60 hours per week at a salary of 540 yuan per week. If the ordered food cannot be delivered on time, there is a compensation fee of 0.50 yuan per kg for food I and 0.60 yuan per kg for food II. Under the above conditions, how should the factory make comprehensive arrangements to minimize the total cost?

Table 1-11
\begin{tabular}{|c|c|c|c|c|c|c|c|c|}
\hline Food Week & 1 & 2 & 3 & 4 & 5 & 6 & 7 & 8 \\
\hline I & 10 & 10 & 12 & 12 & 16 & 16 & 20 & 20 \\
\hline II & 6 & 7. 2 & 8.4 & 10.8 & 10.8 & 12 & 12 & 12 \\
\hline
\end{tabular}
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"prod_rate_I": {"base":10,"perturb":{"mode":"rel","r":0.2}}
"prod_rate_II": {"base":6,"perturb":{"mode":"rel","r":0.2}}
"initial_skilled_workers": {"base":50,"perturb":{"mode":"abs","lo":50.0,"hi":50.0,"integer":true}}
"target_new_workers": {"base":50,"perturb":{"mode":"abs","lo":50.0,"hi":50.0,"integer":true}}
"weekly_hours_normal": {"base":40,"perturb":{"mode":"rel","r":0.15}}
"weekly_hours_overtime": {"base":60,"perturb":{"mode":"rel","r":0.15}}
"max_trainees_per_trainer": {"base":3,"perturb":{"mode":"abs","lo":2.0,"hi":4.0,"integer":true}}
"training_duration_weeks": {"base":2,"perturb":{"mode":"abs","lo":2.0,"hi":2.0,"integer":true}}
"salary_skilled_weekly": {"base":360,"perturb":{"mode":"rel","r":0.25}}
"salary_trainee_training_weekly": {"base":120,"perturb":{"mode":"rel","r":0.3}}
"salary_trainee_after_weekly": {"base":240,"perturb":{"mode":"rel","r":0.25}}
"salary_overtime_weekly": {"base":540,"perturb":{"mode":"rel","r":0.2}}
"penalty_shortage_I": {"base":0.5,"perturb":{"mode":"rel","r":0.5}}
"penalty_shortage_II": {"base":0.6,"perturb":{"mode":"rel","r":0.5}}
"demand_I": {"base":[10,10,12,12,16,16,20,20],"perturb":{"mode":"rel","r":0.25}}
"demand_II": {"base":[6,7.2,8.4,10.8,10.8,12,12,12],"perturb":{"mode":"rel","r":0.25}}
```

Warnings:

```
[initial_skilled_workers] degenerate abs range (lo == hi); perturbation has no effect
[target_new_workers] degenerate abs range (lo == hi); perturbation has no effect
[training_duration_weeks] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # ---- Read parameters ----
    rate_I = params["prod_rate_I"]
    rate_II = params["prod_rate_II"]
    init_skilled = params["initial_skilled_workers"]
    target_new = params["target_new_workers"]
    hours_normal = params["weekly_hours_normal"]
    hours_overtime = params["weekly_hours_overtime"]
    max_trainees = params["max_trainees_per_trainer"]
    train_weeks = params["training_duration_weeks"]
    sal_skilled = params["salary_skilled_weekly"]
    sal_trainee_train = params["salary_trainee_training_weekly"]
    sal_trainee_after = params["salary_trainee_after_weekly"]
    sal_overtime = params["salary_overtime_weekly"]
    pen_I = params["penalty_shortage_I"]
    pen_II = params["penalty_shortage_II"]
    dem_I = params["demand_I"]
    dem_II = params["demand_II"]

    weeks = list(range(1, 9))
    n_train_weeks = int(train_weeks)

    model = pyo.ConcreteModel()

    # ---- Variables ----
    # Number of skilled workers assigned as trainers in training block starting at week t
    model.trainers = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    # Number of trainees in training block starting at week t
    model.trainees = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    # Skilled workers working overtime (60h) / normally (40h) in production in week w
    model.prod_skilled_overtime = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    model.prod_skilled_normal = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    # Trained workers (now skilled) working overtime / normally in production in week w
    model.prod_trained_normal = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    model.prod_trained_overtime = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    # Production amounts and shortages
    model.prod_food_I = pyo.Var(weeks, within=pyo.NonNegativeReals)
    model.prod_food_II = pyo.Var(weeks, within=pyo.NonNegativeReals)
    model.shortage_I = pyo.Var(weeks, within=pyo.NonNegativeReals)
    model.shortage_II = pyo.Var(weeks, within=pyo.NonNegativeReals)

    # ---- Constraints ----
    # Trainee capacity per trainer
    model.trainer_capacity = pyo.Constraint(
        weeks, rule=lambda m, w: m.trainees[w] <= max_trainees * m.trainers[w]
    )

    # Training blocks must fit in horizon
    model.training_fit = pyo.ConstraintList()
    for w in weeks:
        if w + n_train_weeks > 8:
            model.training_fit.add(model.trainees[w] == 0)
            model.training_fit.add(model.trainers[w] == 0)

    # Must train target number of new workers
    model.target_constraint = pyo.Constraint(
        expr=sum(model.trainees[w] for w in weeks) == target_new
    )

    # Skilled worker balance: for each week, available skilled workers come from
    # initial pool + trained workers (who finished training) - those currently training / training
    # We track trained workers that are "active skilled" after finishing training.
    # Number of trained workers that completed training before week w (available for production):
    model.finished_trained = pyo.Expression(
        weeks,
        rule=lambda m, w: sum(
            m.trainees[t] for t in weeks if t + n_train_weeks <= w
        ),
    )

    # Number of skilled workers in training (either as trainers or being in initial pool):
    # In a training block starting at week t, trainers are out of production for weeks t..t+n-1
    model.skilled_in_training = pyo.Expression(
        weeks,
        rule=lambda m, w: sum(
            m.trainers[t] for t in weeks if t <= w <= t + n_train_weeks - 1
        ),
    )

    # Total skilled workers pool available (initial + finished trained, but trainees becoming skilled)
    # The people in production as skilled are either initial skilled or finished-trained.
    # Constraints on skilled worker allocation each week:
    # number of skilled workers producing (normal + overtime) <= available skilled (initial + finished trained)
    for w in weeks:
        expr_lhs = (
            model.prod_skilled_normal[w]
            + model.prod_skilled_overtime[w]
        )
        # initial skilled reduces by those in training
        avail = init_skilled + model.finished_trained[w]
        model.add_component(
            f"skilled_avail_{w}",
            pyo.Constraint(expr=expr_lhs <= avail),
        )

    # Trained workers (now skilled) production constraints
    for w in weeks:
        model.add_component(
            f"trained_avail_{w}",
            pyo.Constraint(
                expr=model.prod_trained_normal[w] + model.prod_trained_overtime[w]
                <= model.finished_trained[w]
            ),
        )

    # Total skilled-equivalent production capacity (initial skilled workers producing are constrained above;
    # but we also must ensure the training trainers are from initial skilled pool, not from finished trained)
    # Total trainers + producing skilled from initial pool <= initial_skilled
    for w in weeks:
        model.add_component(
            f"init_skilled_total_{w}",
            pyo.Constraint(
                expr=model.prod_skilled_normal[w]
                + model.prod_skilled_overtime[w]
                + model.skilled_in_training[w]
                <= init_skilled
            ),
        )

    # Production capacity from hours: each week, total skilled-equivalent hours
    # Normal-hours contribution
    for w in weeks:
        hours_available = (
            model.prod_skilled_normal[w] * hours_normal
            + model.prod_trained_normal[w] * hours_normal
            + model.prod_skilled_overtime[w] * hours_overtime
            + model.prod_trained_overtime[w] * hours_overtime
        )
        model.add_component(
            f"prod_capacity_{w}",
            pyo.Constraint(
                expr=model.prod_food_I[w] / rate_I + model.prod_food_II[w] / rate_II
                <= hours_available
            ),
        )

    # Demand / shortage balance
    for w in weeks:
        model.add_component(
            f"demand_I_{w}",
            pyo.Constraint(
                expr=model.prod_food_I[w] + model.shortage_I[w] >= dem_I[w - 1]
            ),
        )
        model.add_component(
            f"demand_II_{w}",
            pyo.Constraint(
                expr=model.prod_food_II[w] + model.shortage_II[w] >= dem_II[w - 1]
            ),
        )

    # ---- Objective ----
    def obj_rule(m):
        # Salaries: skilled workers (initial) always paid skilled salary
        # Overtime premium: overtime workers paid sal_overtime instead of sal_skilled
        # Trainees paid training salary during training, then after-training salary once trained
        cost_skilled_base = 0
        cost_overtime_premium = 0
        cost_trainee_training = 0
        cost_trainee_after = 0
        cost_penalty = 0

        for w in weeks:
            # Initial skilled workers all get base salary
            cost_skilled_base += init_skilled * sal_skilled
            # Overtime skilled workers: paid sal_overtime (replaces base for those assigned OT)
            cost_overtime_premium += (
                m.prod_skilled_overtime[w] + m.prod_trained_overtime[w]
            ) * (sal_overtime - sal_skilled)
            # Trainees in training
            cost_trainee_training += m.trainees[w] * sal_trainee_train
            # Finished trainees get after-training salary (skilled-like salary)
            cost_trainee_after += m.finished_trained[w] * sal_trainee_after
            # Shortage penalties
            cost_penalty += (
                m.shortage_I[w] * pen_I + m.shortage_II[w] * pen_II
            )

        # Note: base salary for finished trained workers handled by cost_trainee_after;
        # for those assigned overtime we already added premium relative to sal_skilled
        return (
            cost_skilled_base
            + cost_overtime_premium
            + cost_trainee_training
            + cost_trainee_after
            + cost_penalty
        )

    model.cost = pyo.Expression(rule=obj_rule)
    model.objective = pyo.Objective(expr=model.cost, sense=pyo.minimize)

    # ---- Solve ----
    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR (JSON):
# {"sets":{"W":"weeks 1..8","F":["I","II"],"S":"training starts 1..(9-D)","A[w]":"s in S with s<=w<s+D","C[w]":"s in S with s+D<=w"},"params":["prod_rate_I","prod_rate_II","initial_skilled_workers","target_new_workers","weekly_hours_normal","weekly_hours_overtime","max_trainees_per_trainer","training_duration_weeks","salary_skilled_weekly","salary_trainee_training_weekly","salary_trainee_after_weekly","salary_overtime_weekly","penalty_shortage_I","penalty_shortage_II","demand_I","demand_II"],"variables":{"trainees[s]":"nonnegative integer","trainers[s]":"nonnegative integer","original_normal[w]":"nonnegative integer","original_overtime[w]":"nonnegative integer","new_normal[w]":"nonnegative integer","new_overtime[w]":"nonnegative integer","hours[w,f]":"nonnegative continuous","shortage[w,f]":"nonnegative continuous"},"constraints":["sum_s trainees[s] = target_new_workers","trainees[s] <= max_trainees_per_trainer * trainers[s]","original_normal[w] + original_overtime[w] + sum_A[w] trainers[s] = initial_skilled_workers","new_normal[w] + new_overtime[w] = sum_C[w] trainees[s]","sum_f hours[w,f] <= weekly_hours_normal*(original_normal[w]+new_normal[w]) + weekly_hours_overtime*(original_overtime[w]+new_overtime[w])","prod_rate[f]*hours[w,f] + shortage[w,f] = demand[w,f]"],"objective":"minimize sum_w {salary_skilled_weekly*(original_normal[w]+sum_A[w] trainers[s]) + salary_trainee_training_weekly*sum_A[w] trainees[s] + salary_trainee_after_weekly*new_normal[w] + salary_overtime_weekly*(original_overtime[w]+new_overtime[w]) + sum_f penalty_shortage[f]*shortage[w,f]}","assumptions":["Demand inputs are already in kg; production rates are kg/hour.","Only original skilled workers train; trainers remain assigned throughout each cohort's training.","Training finishes at the end of start_week+D-1; graduates can produce the following week.","Either class of qualified production worker may work overtime; overtime salary replaces normal salary.","All available qualified workers receive a weekly salary, including workers with unused production hours.","Production hours are divisible between foods; no inventory, backlog, or separate shift-capacity restriction is modeled."]}

from collections.abc import Mapping
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    rate_I = float(params["prod_rate_I"])
    rate_II = float(params["prod_rate_II"])
    initial_workers_raw = params["initial_skilled_workers"]
    target_workers_raw = params["target_new_workers"]
    normal_hours = float(params["weekly_hours_normal"])
    overtime_hours = float(params["weekly_hours_overtime"])
    training_capacity = float(params["max_trainees_per_trainer"])
    duration_raw = params["training_duration_weeks"]
    skilled_salary = float(params["salary_skilled_weekly"])
    training_salary = float(params["salary_trainee_training_weekly"])
    graduate_salary = float(params["salary_trainee_after_weekly"])
    overtime_salary = float(params["salary_overtime_weekly"])
    penalty_I = float(params["penalty_shortage_I"])
    penalty_II = float(params["penalty_shortage_II"])
    demand_I_input = params["demand_I"]
    demand_II_input = params["demand_II"]

    def integer_parameter(value, label, minimum):
        numeric = float(value)
        if (
            not math.isfinite(numeric)
            or not numeric.is_integer()
            or numeric < minimum
        ):
            raise ValueError(
                f"{label} must be an integer greater than or equal to {minimum}."
            )
        return int(numeric)

    initial_workers = integer_parameter(
        initial_workers_raw, "initial_skilled_workers", 0
    )
    target_workers = integer_parameter(
        target_workers_raw, "target_new_workers", 0
    )
    duration = integer_parameter(
        duration_raw, "training_duration_weeks", 1
    )

    weeks = tuple(range(1, 9))
    foods = ("I", "II")
    starts = tuple(range(1, 10 - duration))

    nonnegative_parameters = {
        "prod_rate_I": rate_I,
        "prod_rate_II": rate_II,
        "weekly_hours_normal": normal_hours,
        "weekly_hours_overtime": overtime_hours,
        "max_trainees_per_trainer": training_capacity,
        "salary_skilled_weekly": skilled_salary,
        "salary_trainee_training_weekly": training_salary,
        "salary_trainee_after_weekly": graduate_salary,
        "salary_overtime_weekly": overtime_salary,
        "penalty_shortage_I": penalty_I,
        "penalty_shortage_II": penalty_II,
    }
    for label, value in nonnegative_parameters.items():
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{label} must be finite and nonnegative.")

    def weekly_demands(values, label):
        # Sequences use positions 0..7. Mappings use week keys 1..8
        # or their string equivalents.
        if isinstance(values, Mapping):
            result = {
                week: float(
                    values[week] if week in values else values[str(week)]
                )
                for week in weeks
            }
        else:
            sequence = list(values)
            if len(sequence) != len(weeks):
                raise ValueError(f"{label} must contain eight weekly demands.")
            result = {
                week: float(sequence[week - 1])
                for week in weeks
            }

        if any(
            not math.isfinite(value) or value < 0
            for value in result.values()
        ):
            raise ValueError(f"{label} must contain finite, nonnegative demands.")
        return result

    demand_I = weekly_demands(demand_I_input, "demand_I")
    demand_II = weekly_demands(demand_II_input, "demand_II")

    rates = {"I": rate_I, "II": rate_II}
    penalties = {"I": penalty_I, "II": penalty_II}
    demands = {
        (week, food): demand_I[week] if food == "I" else demand_II[week]
        for week in weeks
        for food in foods
    }
    active_starts = {
        week: tuple(
            start for start in starts
            if start <= week < start + duration
        )
        for week in weeks
    }
    completed_starts = {
        week: tuple(
            start for start in starts
            if start + duration <= week
        )
        for week in weeks
    }

    model = pyo.ConcreteModel()
    model.W = pyo.Set(initialize=weeks, ordered=True)
    model.F = pyo.Set(initialize=foods, ordered=True)
    model.S = pyo.Set(initialize=starts, ordered=True)

    model.trainees = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)
    model.trainers = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)
    model.original_normal = pyo.Var(model.W, domain=pyo.NonNegativeIntegers)
    model.original_overtime = pyo.Var(model.W, domain=pyo.NonNegativeIntegers)
    model.new_normal = pyo.Var(model.W, domain=pyo.NonNegativeIntegers)
    model.new_overtime = pyo.Var(model.W, domain=pyo.NonNegativeIntegers)
    model.hours = pyo.Var(model.W, model.F, domain=pyo.NonNegativeReals)
    model.shortage = pyo.Var(model.W, model.F, domain=pyo.NonNegativeReals)

    # A symbolic zero also handles an empty feasible training-start set.
    model.training_target = pyo.Constraint(
        expr=(
            pyo.quicksum(model.trainees[start] for start in starts)
            + 0 * model.original_normal[weeks[0]]
            == target_workers
        )
    )

    def training_capacity_rule(block, start):
        return (
            block.trainees[start]
            <= training_capacity * block.trainers[start]
        )

    model.training_capacity_limit = pyo.Constraint(
        model.S, rule=training_capacity_rule
    )

    def original_workforce_rule(block, week):
        return (
            block.original_normal[week]
            + block.original_overtime[week]
            + pyo.quicksum(
                block.trainers[start] for start in active_starts[week]
            )
            == initial_workers
        )

    model.original_workforce_balance = pyo.Constraint(
        model.W, rule=original_workforce_rule
    )

    def graduate_workforce_rule(block, week):
        return (
            block.new_normal[week] + block.new_overtime[week]
            == pyo.quicksum(
                block.trainees[start] for start in completed_starts[week]
            )
        )

    model.graduate_workforce_balance = pyo.Constraint(
        model.W, rule=graduate_workforce_rule
    )

    def production_capacity_rule(block, week):
        return (
            pyo.quicksum(block.hours[week, food] for food in foods)
            <= normal_hours
            * (block.original_normal[week] + block.new_normal[week])
            + overtime_hours
            * (block.original_overtime[week] + block.new_overtime[week])
        )

    model.production_capacity_limit = pyo.Constraint(
        model.W, rule=production_capacity_rule
    )

    def demand_balance_rule(block, week, food):
        return (
            rates[food] * block.hours[week, food]
            + block.shortage[week, food]
            == demands[week, food]
        )

    model.weekly_demand_balance = pyo.Constraint(
        model.W, model.F, rule=demand_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            skilled_salary
            * (
                model.original_normal[week]
                + pyo.quicksum(
                    model.trainers[start]
                    for start in active_starts[week]
                )
            )
            + training_salary
            * pyo.quicksum(
                model.trainees[start]
                for start in active_starts[week]
            )
            + graduate_salary * model.new_normal[week]
            + overtime_salary
            * (model.original_overtime[week] + model.new_overtime[week])
            + pyo.quicksum(
                penalties[food] * model.shortage[week, food]
                for food in foods
            )
            for week in weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when its automatic solution loading finds
        # no feasible solution. Unexpected runtime errors propagate.
        message = str(exc).lower()
        if (
            "feasible solution was not found" in message
            and "no solution can be loaded" in message
        ):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    prod_rate_I = params["prod_rate_I"]
    prod_rate_II = params["prod_rate_II"]
    initial_skilled_workers = params["initial_skilled_workers"]
    target_new_workers = params["target_new_workers"]
    weekly_hours_normal = params["weekly_hours_normal"]
    weekly_hours_overtime = params["weekly_hours_overtime"]
    max_trainees_per_trainer = params["max_trainees_per_trainer"]
    training_duration_weeks = params["training_duration_weeks"]
    salary_skilled_weekly = params["salary_skilled_weekly"]
    salary_trainee_training_weekly = params["salary_trainee_training_weekly"]
    salary_trainee_after_weekly = params["salary_trainee_after_weekly"]
    salary_overtime_weekly = params["salary_overtime_weekly"]
    penalty_shortage_I = params["penalty_shortage_I"]
    penalty_shortage_II = params["penalty_shortage_II"]
    demand_I = params["demand_I"]    # list of 8 values (kg)
    demand_II = params["demand_II"]  # list of 8 values (kg)

    # Number of weeks
    T = 8
    weeks = range(T)  # 0..7 representing weeks 1..8

    # Training batches: training lasts training_duration_weeks (2 weeks)
    # Batches can start at the beginning of weeks 1,3,5,7 (0-indexed: 0,2,4,6)
    # A batch starting at week t (0-indexed) trains during weeks t and t+1,
    # and workers are available from week t+2 onward.
    # Possible start weeks (0-indexed): 0, 2, 4, 6
    batch_starts = [0, 2, 4, 6]  # 0-indexed week indices where a batch can start

    model = gp.Model("factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables:
    # n[b]: number of trainees in batch b (batch starts at week batch_starts[b])
    n = {}
    for b, bs in enumerate(batch_starts):
        n[b] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"n_{b}")

    # trainer[b]: number of skilled workers assigned as trainers in batch b
    trainer = {}
    for b, bs in enumerate(batch_starts):
        trainer[b] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"trainer_{b}")

    # For each week t (0-indexed), for each food type:
    # x_I[t]: number of normal-hour workers producing food I in week t
    # x_II[t]: number of normal-hour workers producing food II in week t
    # o_I[t]: number of overtime workers producing food I in week t
    # o_II[t]: number of overtime workers producing food II in week t
    x_I = {}
    x_II = {}
    o_I = {}
    o_II = {}
    for t in weeks:
        x_I[t] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"xI_{t}")
        x_II[t] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"xII_{t}")
        o_I[t] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"oI_{t}")
        o_II[t] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"oII_{t}")

    # Shortage variables
    short_I = {}
    short_II = {}
    for t in weeks:
        short_I[t] = model.addVar(lb=0, name=f"shortI_{t}")
        short_II[t] = model.addVar(lb=0, name=f"shortII_{t}")

    # Constraints

    # 1. Total new workers trained = target_new_workers
    model.addConstr(gp.quicksum(n[b] for b in range(len(batch_starts))) == target_new_workers,
                    name="total_trainees")

    # 2. Trainer capacity: trainers for batch b can train at most max_trainees_per_trainer each
    for b in range(len(batch_starts)):
        model.addConstr(n[b] <= max_trainees_per_trainer * trainer[b],
                        name=f"trainer_cap_{b}")

    # 3. Available skilled workers for production in each week
    # In week t (0-indexed):
    # - Initial skilled workers = initial_skilled_workers
    # - Graduated workers from batches that finished before week t:
    #   batch b finishes at week batch_starts[b] + training_duration_weeks
    #   so available from week batch_starts[b] + training_duration_weeks onward
    # - Workers assigned as trainers in batches active during week t cannot produce
    #   A batch b is active during weeks batch_starts[b] and batch_starts[b]+1

    for t in weeks:
        # Skilled workers: initial + graduated
        skilled_available = initial_skilled_workers
        for b, bs in enumerate(batch_starts):
            grad_week = bs + training_duration_weeks  # week index when they become available
            if t >= grad_week:
                skilled_available = skilled_available + n[b]

        # Trainers occupied in week t (from active batches)
        trainers_busy = gp.LinExpr()
        for b, bs in enumerate(batch_starts):
            if bs <= t < bs + training_duration_weeks:
                trainers_busy += trainer[b]

        # Total productive workers in week t (normal + overtime)
        # Normal workers: x_I[t] + x_II[t]
        # Overtime workers: o_I[t] + o_II[t]
        # All productive workers come from available skilled (including graduated) minus trainers
        # Note: overtime workers are a subset of the productive workers (they work more hours)
        # We model: total workers assigned to production = x_I[t] + x_II[t] (normal)
        #           plus o_I[t] + o_II[t] (overtime)
        # These must not exceed available_productive workers

        # Trainees during training do not produce, so only count graduated ones
        # Trainers don't produce during their training weeks
        model.addConstr(
            x_I[t] + x_II[t] + o_I[t] + o_II[t] <= skilled_available - trainers_busy,
            name=f"worker_cap_{t}"
        )

        # Also trainers must not exceed skilled_available at that time
        # (trainers must be skilled workers available at start of batch)

    # 4. Trainer availability: trainers for batch b must be from initial skilled workers
    #    (since batches can overlap, sum of concurrent trainers <= initial_skilled)
    #    More precisely, at any week, total trainers busy + production workers <= available skilled
    #    Already handled above. But we need trainer[b] to come from available skilled at batch start.
    for b, bs in enumerate(batch_starts):
        # At week bs, the skilled workers available = initial + graduated before bs
        skilled_at_start = initial_skilled_workers
        for b2, bs2 in enumerate(batch_starts):
            if bs2 + training_duration_weeks <= bs:
                skilled_at_start = skilled_at_start + n[b2]
        # trainer[b] <= skilled_at_start (but skilled_at_start may contain n variables)
        # This is implicitly handled by the weekly worker capacity constraint
        # Add explicit constraint that trainers <= available skilled at that time
        model.addConstr(trainer[b] <= skilled_at_start, name=f"trainer_avail_{b}")

    # 5. Supply/demand with shortages
    for t in weeks:
        prod_I = (x_I[t] * weekly_hours_normal + o_I[t] * weekly_hours_overtime) * prod_rate_I
        prod_II = (x_II[t] * weekly_hours_normal + o_II[t] * weekly_hours_overtime) * prod_rate_II

        model.addConstr(prod_I + short_I[t] >= demand_I[t], name=f"demand_I_{t}")
        model.addConstr(prod_II + short_II[t] >= demand_II[t], name=f"demand_II_{t}")

    # 6. Objective: minimize total cost
    # Cost components:
    # a) Salary for skilled workers (not training): salary_skilled_weekly per week
    # b) Salary for overtime skilled workers: salary_overtime_weekly (instead of salary_skilled_weekly)
    #    So extra cost for overtime = salary_overtime_weekly - salary_skilled_weekly per overtime worker
    # c) Trainers: salary_skilled_weekly
    # d) Trainees during training: salary_trainee_training_weekly
    # e) Graduated trainees after training: salary_trainee_after_weekly
    # f) Penalty for shortages

    # We pay ALL skilled workers (including trainers) their base salary each week.
    # Overtime workers get salary_overtime_weekly instead of salary_skilled_weekly.
    # So total salary cost per week t:
    #   - All available skilled workers (not in training as trainers, not overtime): salary_skilled_weekly
    #   - Trainers: salary_skilled_weekly
    #   - Overtime workers: salary_overtime_weekly (they replace normal salary)
    #   - Trainees in training: salary_trainee_training_weekly
    #   - Graduated trainees: salary_trainee_after_weekly

    # Simpler approach: 
    # Total workers available in week t = initial_skilled + graduated_by_t
    # They all get salary_skilled_weekly EXCEPT:
    #   - overtime workers get salary_overtime_weekly
    # So cost = (available - overtime_workers)*salary_skilled + overtime_workers*salary_overtime
    #         + trainees_in_training * salary_trainee_training
    #         + graduated_trainees * salary_trainee_after

    cost = gp.LinExpr()

    for t in weeks:
        # Available skilled workers (initial + graduated)
        skilled_base = initial_skilled_workers
        for b, bs in enumerate(batch_starts):
            grad_week = bs + training_duration_weeks
            if t >= grad_week:
                skilled_base = skilled_base + n[b]

        overtime_workers = o_I[t] + o_II[t]

        # Skilled worker salary: 
        # (skilled_base - overtime_workers) * salary_skilled + overtime_workers * salary_overtime
        # = skilled_base * salary_skilled + overtime_workers * (salary_overtime - salary_skilled)
        cost += skilled_base * salary_skilled_weekly
        cost += overtime_workers * (salary_overtime_weekly - salary_skilled_weekly)

        # Trainees in training during week t
        for b, bs in enumerate(batch_starts):
            if bs <= t < bs + training_duration_weeks:
                cost += n[b] * salary_trainee_training_weekly

        # Graduated trainees in week t
        for b, bs in enumerate(batch_starts):
            grad_week = bs + training_duration_weeks
            if t >= grad_week:
                cost += n[b] * salary_trainee_after_weekly

        # Penalties
        cost += short_I[t] * penalty_shortage_I
        cost += short_II[t] * penalty_shortage_II

    model.setObjective(cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 162000.0 (optimal) | 156000.0 (optimal) | 156000.0 (optimal) |
| 1 | 152997.46885613818 (optimal) | 146992.9109972936 (optimal) | 146992.9109972936 (optimal) |
| 2 | 189548.79556258986 (optimal) | 182599.83226822465 (optimal) | 182599.83226822465 (optimal) |
| 3 | 146142.38367528436 (optimal) | 141040.35376727895 (optimal) | 141040.35376727892 (optimal) |
| 4 | 194285.33624788158 (optimal) | 192515.25704426886 (optimal) | 192515.25704426883 (optimal) |
| 5 | 189307.05586138548 (optimal) | 185655.96701466976 (optimal) | 185655.96701466976 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 162000.0 (optimal) | 156000.0 (optimal) | 156000.0 (optimal) |
| 1 | 152997.46885613818 (optimal) | 146992.9109972936 (optimal) | 146992.9109972936 (optimal) |
| 2 | 189548.79556258986 (optimal) | 182599.83226822465 (optimal) | 182599.83226822465 (optimal) |
| 3 | 146142.38367528436 (optimal) | 141040.35376727895 (optimal) | 141040.35376727892 (optimal) |
| 4 | 194285.33624788158 (optimal) | 192515.25704426886 (optimal) | 192515.25704426883 (optimal) |
| 5 | 189307.05586138548 (optimal) | 185655.96701466976 (optimal) | 185655.96701466976 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 10. industryor_57 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_57` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 57) |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 28.0 |
| Label (original benchmark) | 770 |
| Rules that certify it | gate 28.0, panel_base_2of3 28.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Changjiang Comprehensive Shopping Mall has an area of $5000 \mathrm{~m}^2$ for rent and plans to attract tenants from the following 5 types of stores. It is known the area occupied by each store, the minimum and maximum number of stores to be opened in the mall, and the annual expected profit (in ten thousand yuan) for each store at different numbers of stores opened, as shown in Table 5-12. Each store is required to pay the mall 20% of their annual profit as rent. What is the optimal number of each type of store the mall should rent in order to maximize the total rental income?

Table 5-12:
\begin{tabular}{c|c|c|c|c|c|c|c}
\hline 
\multirow{2}{*}{Code} & \multirow{2}{*}{Store Type} & Store Area $/ \mathrm{m}^2$ & \multicolumn{2}{|c|}{Number of Stores} & \multicolumn{3}{|c}{Profit per Store at Different Numbers} \\
\cline{3-8} 
& & & Minimum & Maximum & 1 & 2 & 3 \\
\hline 
1 & Jewelry & 250 & 1 & 3 & 9 & 8 & 7 \\
2 & Shoes and Hats & 350 & 1 & 2 & 10 & 9 & - \\
3 & Department Store & 800 & 1 & 3 & 27 & 21 & 20 \\
4 & Bookstore & 400 & 0 & -2 & 16 & 10 & - \\
5 & Restaurant & 500 & 1 & 3 & 17 & 15 & 12 \\
\hline
\end{tabular}
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"area_per_store": {"base":[250,350,800,400,500],"perturb":{"mode":"rel","r":0.2}}
"min_stores": {"base":[1,1,1,0,1],"perturb":{"mode":"abs","lo":0.0,"hi":1.0,"integer":true}}
"max_stores": {"base":[3,2,3],"perturb":{"mode":"abs","lo":2.0,"hi":3.0,"integer":true}}
"profit_type1": {"base":[9,8,7],"perturb":{"mode":"rel","r":0.3}}
"profit_type2": {"base":[10,9],"perturb":{"mode":"rel","r":0.3}}
"profit_type3": {"base":[27,21,20],"perturb":{"mode":"rel","r":0.3}}
"profit_type4": {"base":[16,10],"perturb":{"mode":"rel","r":0.3}}
"profit_type5": {"base":[17,15,12],"perturb":{"mode":"rel","r":0.3}}
"rent_share": {"base":0.2,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    area = params["area_per_store"]
    min_s = params["min_stores"]
    max_s = params["max_stores"]
    p1 = params["profit_type1"]
    p2 = params["profit_type2"]
    p3 = params["profit_type3"]
    p4 = params["profit_type4"]
    p5 = params["profit_type5"]
    rent = params["rent_share"]

    # per-store profit tables indexed by type (1..5), then position (0,1,2 for 1st..3rd store)
    profit = {1: p1, 2: p2, 3: p3, 4: p4, 5: p5}
    max_count = {1: 3, 2: 2, 3: 3, 4: 2, 5: 3}

    model = pyo.ConcreteModel()

    model.TYPES = pyo.Set(initialize=[1, 2, 3, 4, 5])
    model.UNITS = pyo.Set(initialize=[1, 2, 3])

    # y[t, k] = 1 if type t has at least k stores (k-th store opened)
    model.y = pyo.Var(model.TYPES, model.UNITS, domain=pyo.Binary)

    # enforce y[t,k] = 0 when k exceeds max_count for type t
    def _cap_rule(md, t, k):
        if k > max_count[t]:
            return md.y[t, k] == 0
        return pyo.Constraint.Skip

    model.cap_con = pyo.Constraint(model.TYPES, model.UNITS, rule=_cap_rule)

    # monotone nesting: y[t,k] <= y[t,k-1]
    def _nest_rule(md, t, k):
        if k >= 2 and k <= max_count[t]:
            return md.y[t, k] <= md.y[t, k - 1]
        return pyo.Constraint.Skip

    model.nest_con = pyo.Constraint(model.TYPES, model.UNITS, rule=_nest_rule)

    # number of stores per type
    def _num_rule(md, t):
        return sum(md.y[t, k] for k in md.UNITS if k <= max_count[t])

    model.num = pyo.Expression(model.TYPES, rule=_num_rule)

    # area constraint
    def _area_rule(md):
        return sum(area[t - 1] * md.num[t] for t in md.TYPES) <= 5000

    model.area_con = pyo.Constraint(rule=_area_rule)

    # min/max number constraints
    def _min_rule(md, t):
        return md.num[t] >= min_s[t - 1]

    model.min_con = pyo.Constraint(model.TYPES, rule=_min_rule)

    def _max_rule(md, t):
        if t <= len(max_s):
            return md.num[t] <= max_s[t - 1]
        return pyo.Constraint.Skip

    model.max_con = pyo.Constraint(model.TYPES, rule=_max_rule)

    # objective: rental income = rent_share * total profit
    # profit for type t with num stores = sum_k profit[t][k-1] * y[t,k]
    def _obj_rule(md):
        return rent * sum(
            profit[t][k - 1] * md.y[t, k]
            for t in md.TYPES
            for k in md.UNITS
            if k <= max_count[t]
        )

    model.obj = pyo.Objective(rule=_obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"T":[1,2,3,4,5],"B":[1,2,3],"K":{"1":[0,1,2,3],"2":[0,1,2],"3":[0,1,2,3],"4":[0,1,2],"5":[0,1,2,3]}},"params":{"area_per_store":"params[area_per_store], indexed by T","min_stores":"params[min_stores], indexed by T","max_stores":"params[max_stores], indexed by B","profit_type1":"params[profit_type1], indexed by positive K[1]","profit_type2":"params[profit_type2], indexed by positive K[2]","profit_type3":"params[profit_type3], indexed by positive K[3]","profit_type4":"params[profit_type4], indexed by positive K[4]","profit_type5":"params[profit_type5], indexed by positive K[5]","rent_share":"params[rent_share]","capacity":5000,"profit_at_zero":0},"variables":{"choose[t,k]":"binary; selects exactly k stores of type t"},"expressions":{"store_count[t]":"sum(k*choose[t,k] for k in K[t])"},"constraints":["sum(choose[t,k] for k in K[t]) == 1 for each t in T","store_count[t] >= min_stores[t] for each t in T","store_count[t] <= max_stores[t] for each t in B","sum(area_per_store[t]*store_count[t] for t in T) <= capacity"],"objective":"maximize rent_share*sum(k*profit_type_t[k]*choose[t,k] for t in T for k in K[t]); zero-count contribution is zero"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(values, position):
    """Accept sequences or mappings keyed by one-based integers or strings."""
    if isinstance(values, Mapping):
        if position in values:
            return values[position]
        return values[str(position)]
    return values[position - 1]


def solve(params):
    store_types = (1, 2, 3, 4, 5)
    bounded_types = (1, 2, 3)

    # Available counts follow the supplied profit-table structure.
    # The Bookstore entry "-2" is interpreted as a maximum of two stores.
    count_options = {
        1: (0, 1, 2, 3),
        2: (0, 1, 2),
        3: (0, 1, 2, 3),
        4: (0, 1, 2),
        5: (0, 1, 2, 3),
    }

    area_input = params["area_per_store"]
    minimum_input = params["min_stores"]
    maximum_input = params["max_stores"]
    profit_inputs = {
        1: params["profit_type1"],
        2: params["profit_type2"],
        3: params["profit_type3"],
        4: params["profit_type4"],
        5: params["profit_type5"],
    }
    rent_share_input = params["rent_share"]

    option_pairs = [
        (store_type, count)
        for store_type in store_types
        for count in count_options[store_type]
    ]

    profit_data = {
        (store_type, count): (
            0
            if count == 0
            else _indexed_value(profit_inputs[store_type], count)
        )
        for store_type, count in option_pairs
    }

    model = pyo.ConcreteModel()
    model.store_types = pyo.Set(initialize=store_types, ordered=True)
    model.bounded_types = pyo.Set(initialize=bounded_types, ordered=True)
    model.option_pairs = pyo.Set(
        dimen=2, initialize=option_pairs, ordered=True
    )

    model.area_per_store = pyo.Param(
        model.store_types,
        initialize={
            store_type: _indexed_value(area_input, store_type)
            for store_type in store_types
        },
    )
    model.min_stores = pyo.Param(
        model.store_types,
        initialize={
            store_type: _indexed_value(minimum_input, store_type)
            for store_type in store_types
        },
    )
    model.max_stores = pyo.Param(
        model.bounded_types,
        initialize={
            store_type: _indexed_value(maximum_input, store_type)
            for store_type in bounded_types
        },
    )
    model.profit_per_store = pyo.Param(
        model.option_pairs, initialize=profit_data
    )
    model.rent_share = pyo.Param(initialize=rent_share_input)
    model.capacity = pyo.Param(initialize=5000)

    model.choose = pyo.Var(model.option_pairs, domain=pyo.Binary)

    model.store_count = pyo.Expression(
        model.store_types,
        rule=lambda mdl, store_type: sum(
            count * mdl.choose[store_type, count]
            for count in count_options[store_type]
        ),
    )

    model.select_one_count = pyo.Constraint(
        model.store_types,
        rule=lambda mdl, store_type: sum(
            mdl.choose[store_type, count]
            for count in count_options[store_type]
        ) == 1,
    )
    model.minimum_store_limits = pyo.Constraint(
        model.store_types,
        rule=lambda mdl, store_type: (
            mdl.store_count[store_type] >= mdl.min_stores[store_type]
        ),
    )
    model.maximum_store_limits = pyo.Constraint(
        model.bounded_types,
        rule=lambda mdl, store_type: (
            mdl.store_count[store_type] <= mdl.max_stores[store_type]
        ),
    )
    model.area_limit = pyo.Constraint(
        expr=sum(
            model.area_per_store[store_type]
            * model.store_count[store_type]
            for store_type in store_types
        ) <= model.capacity
    )

    model.rental_income = pyo.Objective(
        expr=model.rent_share * sum(
            count
            * model.profit_per_store[store_type, count]
            * model.choose[store_type, count]
            for store_type, count in option_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.rental_income))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    area_per_store = params["area_per_store"]   # list of 5 values, index 0..4
    min_stores     = params["min_stores"]        # list of 5 values
    max_stores     = params["max_stores"]        # list of 3 values (for types 1..3, i.e. index 0,1,2)
    profit_type1   = params["profit_type1"]      # list of 3: per-store profits at n=1,2,3
    profit_type2   = params["profit_type2"]      # list of 2: per-store profits at n=1,2
    profit_type3   = params["profit_type3"]      # list of 3: per-store profits at n=1,2,3
    profit_type4   = params["profit_type4"]      # list of 2: per-store profits at n=1,2
    profit_type5   = params["profit_type5"]      # list of 3: per-store profits at n=1,2,3
    rent_share     = params["rent_share"]        # fraction, e.g. 0.20

    profits_per_store = [
        profit_type1,   # type 0 (Jewelry):         n=1,2,3
        profit_type2,   # type 1 (Shoes and Hats):  n=1,2
        profit_type3,   # type 2 (Department Store): n=1,2,3
        profit_type4,   # type 3 (Bookstore):        n=1,2
        profit_type5,   # type 4 (Restaurant):       n=1,2,3
    ]

    # min for all 5 types
    type_min = [int(min_stores[i]) for i in range(5)]

    # max: params provides max_stores for types 0,1,2 (3 entries);
    # for types 3 and 4, infer max from length of their profit lists
    type_max = []
    for i in range(3):
        type_max.append(int(max_stores[i]))
    for i in range(3, 5):
        type_max.append(len(profits_per_store[i]))

    total_area = 5000

    model = gp.Model("mall_rental")
    model.setParam("OutputFlag", 0)

    # Binary variable z[i, n] = 1 if exactly n stores of type i are opened
    z = {}
    for i in range(5):
        lo = type_min[i]
        hi = type_max[i]
        for n in range(lo, hi + 1):
            z[i, n] = model.addVar(vtype=GRB.BINARY, name=f"z_{i}_{n}")

    model.update()

    # Exactly one count selected per type
    for i in range(5):
        lo = type_min[i]
        hi = type_max[i]
        model.addConstr(
            gp.quicksum(z[i, n] for n in range(lo, hi + 1)) == 1,
            name=f"one_count_{i}"
        )

    # Total area constraint
    area_expr = gp.LinExpr()
    for i in range(5):
        lo = type_min[i]
        hi = type_max[i]
        for n in range(lo, hi + 1):
            area_expr += area_per_store[i] * n * z[i, n]
    model.addConstr(area_expr <= total_area, name="area_limit")

    # Objective: maximize rent = rent_share * sum_i [ n_i * per_store_profit_i(n_i) ]
    obj = gp.LinExpr()
    for i in range(5):
        lo = type_min[i]
        hi = type_max[i]
        for n in range(lo, hi + 1):
            if n == 0:
                total_profit_n = 0.0
            else:
                per_store = profits_per_store[i][n - 1]
                total_profit_n = n * per_store
            obj += rent_share * total_profit_n * z[i, n]

    model.setObjective(obj, GRB.MAXIMIZE)
    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 30.400000000000002 (optimal) | 28.0 (optimal) | 28.0 (optimal) |
| 1 | 38.21748685696273 (optimal) | 35.236364812555955 (optimal) | 35.236364812555955 (optimal) |
| 2 | 37.018342790645214 (optimal) | 34.61067193917174 (optimal) | 34.61067193917174 (optimal) |
| 3 | 19.893821095277865 (optimal) | 16.733799131024135 (optimal) | 16.73379913102414 (optimal) |
| 4 | 25.78975476875852 (optimal) | 24.14058847741437 (optimal) | 24.14058847741437 (optimal) |
| 5 | 17.70047791807642 (optimal) | 15.079383030137974 (optimal) | 15.079383030137972 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 30.400000000000002 (optimal) | 28.0 (optimal) | 28.0 (optimal) |
| 1 | 17.908089033438067 (optimal) | 14.786468862722582 (optimal) | none (crash:per_store = profits_per_store[i][n - 1] \| ~~~~~~~~~~~~~~~~~~~~^^^^^^^ \| IndexError: list index out of range) |
| 2 | 36.96945224717633 (optimal) | 33.33577040301057 (optimal) | none (crash:per_store = profits_per_store[i][n - 1] \| ~~~~~~~~~~~~~~~~~~~~^^^^^^^ \| IndexError: list index out of range) |
| 3 | 32.293718075945016 (optimal) | 27.562325620620253 (optimal) | none (crash:per_store = profits_per_store[i][n - 1] \| ~~~~~~~~~~~~~~~~~~~~^^^^^^^ \| IndexError: list index out of range) |
| 4 | 28.308963293117948 (optimal) | 25.456343054317077 (optimal) | none (crash:per_store = profits_per_store[i][n - 1] \| ~~~~~~~~~~~~~~~~~~~~^^^^^^^ \| IndexError: list index out of range) |
| 5 | 17.020926390147686 (optimal) | 17.134438295410806 (optimal) | 17.134438295410803 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch True; flag_not_stated True; flag_any True.

```json
{"mismatch": [{"parameter": "max_stores", "extracted": [3, 2, 3], "stated": [3, 2, 3, -2, 3], "evidence": "Maximum: 3, 2, 3, -2, 3"}], "not_stated": [{"parameter": "max_stores", "evidence": "Table gives maximum for all 5 types (3, 2, 3, -2, 3), but only 3 entries extracted; and -2 is given as a maximum"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

````json
Looking at each parameter against the table:

**max_stores**: The extracted value covers only types 1–3, but the table has max values for all 5 types (2 and 3 for types 4 and 5 respectively). However, the index range declared is "by type 1..3," so the missing entries for types 4 and 5 are the issue. Actually, re-reading: the extracted array is `[3,2,3]` for types 1–3 only, omitting types 4 and 5. The statement gives max=2 for Bookstore and max=3 for Restaurant.

**min_stores for type 4 (Bookstore)**: The table shows "0" for minimum and "-2" for maximum, which looks like a formatting artifact. The statement cell reads "0 | -2" — the minimum is 0, which matches the extraction. The maximum "-2" is clearly a table error, but that's a modeling judgment. The extracted min of 0 matches the "0" in the table.

**max_stores for Bookstore**: The table shows "-2" which is likely a misprint for "2", but the extraction omits it entirely since max_stores only covers types 1–3.

```json
{
  "mismatch": [
    {
      "parameter": "max_stores",
      "extracted": [3, 2, 3],
      "stated": [3, 2, 3, 2, 3],
      "evidence": "Table row 4 Bookstore maximum column shows \"-2\" (i.e. 2), row 5 Restaurant maximum column shows \"3\"; the parameter covers only types 1–3 and omits these"
    }
  ],
  "not_stated": []
}
```
````


## 11. industryor_62 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_62` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 62) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 0.0 |
| Label (original benchmark) | 11250 |
| Rules that certify it | gate 0.0, panel_base_2of3 0.0, ind_gate 0.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A factory produces two models of microcomputers, A and B. Each model requires two identical processes. The processing time, sales profit, and maximum processing capacity of the factory per week for each microcomputer model are shown in Table 3.1.

Table 3.1

| Process | Model | Maximum Processing Capacity |
| :---: | :---: | :---: |
|  | A | B |  |
| Process I (hours per unit) | 4 | 6 | 150 |
| Process II (hours per unit) | 3 | 2 | 70 |
| Profit (RMB per unit) | 300 | 450 |  |

If the factory's desired objectives and priority levels are as follows:

$p_{1}$: Total profit per week should not be less than 10,000 RMB;

$p_{2}$: Due to contractual requirements, at least 10 units of model A and 15 units of model B must be produced per week;

$p_{3}$: The weekly production time for Process I should be exactly 150 hours, and the production time for Process II should be maximized, even if overtime is necessary.

Establish the goal programming model for this problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"profit_A": {"base":300,"perturb":{"mode":"rel","r":0.5}}
"profit_B": {"base":450,"perturb":{"mode":"rel","r":0.5}}
"time_procI_A": {"base":4,"perturb":{"mode":"rel","r":0.3}}
"time_procI_B": {"base":6,"perturb":{"mode":"rel","r":0.3}}
"time_procII_A": {"base":3,"perturb":{"mode":"rel","r":0.3}}
"time_procII_B": {"base":2,"perturb":{"mode":"rel","r":0.3}}
"cap_procI": {"base":150,"perturb":{"mode":"rel","r":0.4}}
"cap_procII": {"base":70,"perturb":{"mode":"rel","r":0.4}}
"profit_target": {"base":10000,"perturb":{"mode":"rel","r":0.5}}
"min_A": {"base":10,"perturb":{"mode":"abs","lo":5.0,"hi":25.0,"integer":true}}
"min_B": {"base":15,"perturb":{"mode":"abs","lo":5.0,"hi":30.0,"integer":true}}
"procI_target": {"base":150,"perturb":{"mode":"rel","r":0.4}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)

    pA = params["profit_A"]
    pB = params["profit_B"]
    t1A = params["time_procI_A"]
    t1B = params["time_procI_B"]
    t2A = params["time_procII_A"]
    t2B = params["time_procII_B"]
    cap1 = params["cap_procI"]
    cap2 = params["cap_procII"]
    profit_target = params["profit_target"]
    minA = params["min_A"]
    minB = params["min_B"]
    procI_target = params["procI_target"]

    # Deviation variables
    # p1: profit >= target -> minimize d1_minus
    model.d1_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d1_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # p2: contractual minimums -> minimize d2A_minus, d2B_minus
    model.d2A_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2A_plus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2B_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2B_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # p3 process I exact target -> minimize d3I_minus + d3I_plus
    model.d3I_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d3I_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # p3 process II maximized (even with overtime) -> minimize d3II_minus
    model.d3II_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d3II_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # p1 goal: profit constraint
    model.profit_goal = pyo.Constraint(
        expr=pA * model.xA + pB * model.xB + model.d1_minus - model.d1_plus
        == profit_target
    )

    # p2 goal: contractual minimums
    model.goal_min_A = pyo.Constraint(
        expr=model.xA + model.d2A_minus - model.d2A_plus == minA
    )
    model.goal_min_B = pyo.Constraint(
        expr=model.xB + model.d2B_minus - model.d2B_plus == minB
    )

    # p3 goal: Process I exact time
    model.goal_procI = pyo.Constraint(
        expr=t1A * model.xA + t1B * model.xB + model.d3I_minus - model.d3I_plus
        == procI_target
    )

    # p3 goal: Process II time (to be maximized, allow overtime)
    model.goal_procII = pyo.Constraint(
        expr=t2A * model.xA + t2B * model.xB + model.d3II_minus - model.d3II_plus
        == cap2
    )

    # Preemptive (lexicographic) weights: p1 >> p2 >> p3
    W1 = 1e8
    W2 = 1e4
    W3 = 1.0

    # Objective: weighted deviations
    model.obj = pyo.Objective(
        expr=(
            W1 * model.d1_minus
            + W2 * (model.d2A_minus + model.d2B_minus)
            + W3 * (model.d3I_minus + model.d3I_plus + model.d3II_minus)
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"products":["A","B"],"goals":["profit","A_min","B_min","procI","procII"]},"params":["profit_A","profit_B","time_procI_A","time_procI_B","time_procII_A","time_procII_B","cap_procI","cap_procII","profit_target","min_A","min_B","procI_target"],"variables":{"production[products]":"NonNegativeReals","under[goals]":"NonNegativeReals","over[goals]":"NonNegativeReals"},"constraints":["hours_I = time_procI_A*production[A] + time_procI_B*production[B] <= cap_procI","profit_A*production[A] + profit_B*production[B] + under[profit] - over[profit] = profit_target","production[A] + under[A_min] - over[A_min] = min_A","production[B] + under[B_min] - over[B_min] = min_B","hours_I + under[procI] - over[procI] = procI_target","time_procII_A*production[A] + time_procII_B*production[B] + under[procII] - over[procII] = cap_procII"],"objective":{"sense":"lexicographic_minimize","priorities":["under[profit]","under[A_min] + under[B_min]","under[procI] + over[procI] + under[procII] - over[procII]"],"returned_value":"optimal third-priority objective"}}
#
# Modeling conventions:
# - Production is continuous because no integrality requirement is specified.
# - Process I capacity is a hard constraint.
# - Process II capacity is a soft reference level because overtime is allowed.
# - Within each priority, stated goals have equal unit weights.
# - At priority 3, under[procII] - over[procII] equals
#   cap_procII - hours_II, so minimizing it maximizes Process II hours,
#   including hours beyond regular capacity.
# - Priorities are enforced by sequential solves, fixing each earlier optimum.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    time_procI_A = params["time_procI_A"]
    time_procI_B = params["time_procI_B"]
    time_procII_A = params["time_procII_A"]
    time_procII_B = params["time_procII_B"]
    cap_procI = params["cap_procI"]
    cap_procII = params["cap_procII"]
    profit_target = params["profit_target"]
    min_A = params["min_A"]
    min_B = params["min_B"]
    procI_target = params["procI_target"]

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.goals = pyo.Set(
        initialize=["profit", "A_min", "B_min", "procI", "procII"],
        ordered=True,
    )

    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.under = pyo.Var(model.goals, domain=pyo.NonNegativeReals)
    model.over = pyo.Var(model.goals, domain=pyo.NonNegativeReals)

    model.weekly_profit = pyo.Expression(
        expr=profit_A * model.production["A"]
        + profit_B * model.production["B"]
    )
    model.hours_I = pyo.Expression(
        expr=time_procI_A * model.production["A"]
        + time_procI_B * model.production["B"]
    )
    model.hours_II = pyo.Expression(
        expr=time_procII_A * model.production["A"]
        + time_procII_B * model.production["B"]
    )

    model.process_I_capacity = pyo.Constraint(
        expr=model.hours_I <= cap_procI
    )

    model.profit_goal = pyo.Constraint(
        expr=model.weekly_profit
        + model.under["profit"]
        - model.over["profit"]
        == profit_target
    )
    model.contract_A_goal = pyo.Constraint(
        expr=model.production["A"]
        + model.under["A_min"]
        - model.over["A_min"]
        == min_A
    )
    model.contract_B_goal = pyo.Constraint(
        expr=model.production["B"]
        + model.under["B_min"]
        - model.over["B_min"]
        == min_B
    )
    model.process_I_goal = pyo.Constraint(
        expr=model.hours_I
        + model.under["procI"]
        - model.over["procI"]
        == procI_target
    )
    model.process_II_goal = pyo.Constraint(
        expr=model.hours_II
        + model.under["procII"]
        - model.over["procII"]
        == cap_procII
    )

    model.priority_one = pyo.Expression(expr=model.under["profit"])
    model.priority_two = pyo.Expression(
        expr=model.under["A_min"] + model.under["B_min"]
    )
    model.priority_three = pyo.Expression(
        expr=model.under["procI"]
        + model.over["procI"]
        + model.under["procII"]
        - model.over["procII"]
    )

    priority_expressions = (
        model.priority_one,
        model.priority_two,
        model.priority_three,
    )

    model.fixed_priorities = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=model.priority_one,
        sense=pyo.minimize,
    )

    for priority_index, priority_expression in enumerate(priority_expressions):
        model.goal_objective.set_value(priority_expression)

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solver_failed"}

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_index < len(priority_expressions) - 1:
            model.fixed_priorities.add(priority_expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    time_procI_A = params["time_procI_A"]
    time_procI_B = params["time_procI_B"]
    time_procII_A = params["time_procII_A"]
    time_procII_B = params["time_procII_B"]
    cap_procI = params["cap_procI"]
    cap_procII = params["cap_procII"]
    profit_target = params["profit_target"]
    min_A = params["min_A"]
    min_B = params["min_B"]
    procI_target = params["procI_target"]

    model = gp.Model("goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of A and B produced
    x_A = model.addVar(lb=0, name="x_A")
    x_B = model.addVar(lb=0, name="x_B")

    # Deviation variables for each goal
    # p1: profit >= profit_target
    # d1m = negative deviation (underachievement), d1p = positive deviation (overachievement)
    d1m = model.addVar(lb=0, name="d1m")
    d1p = model.addVar(lb=0, name="d1p")

    # p2a: x_A >= min_A
    d2am = model.addVar(lb=0, name="d2am")
    d2ap = model.addVar(lb=0, name="d2ap")

    # p2b: x_B >= min_B
    d2bm = model.addVar(lb=0, name="d2bm")
    d2bp = model.addVar(lb=0, name="d2bp")

    # p3a: Process I usage = procI_target (exactly)
    d3am = model.addVar(lb=0, name="d3am")
    d3ap = model.addVar(lb=0, name="d3ap")

    # p3b: Process II usage should be maximized (maximize d4p, i.e. overachievement of cap_procII)
    # Constraint: procII usage - d4m + d4p = cap_procII
    # We want to maximize d4p (maximize overtime/usage of Process II)
    d4m = model.addVar(lb=0, name="d4m")
    d4p = model.addVar(lb=0, name="d4p")

    # Hard capacity constraints (Process I and II as soft goals, so no hard cap here;
    # but Process I has a target of procI_target = cap_procI, handled via goal constraint)
    # Process II is to be maximized with no hard upper bound restriction beyond the goal formulation.

    # Goal constraints
    # p1: profit goal
    model.addConstr(
        profit_A * x_A + profit_B * x_B - d1p + d1m == profit_target,
        name="goal_profit"
    )

    # p2a: minimum units of A
    model.addConstr(
        x_A - d2ap + d2am == min_A,
        name="goal_minA"
    )

    # p2b: minimum units of B
    model.addConstr(
        x_B - d2bp + d2bm == min_B,
        name="goal_minB"
    )

    # p3a: Process I exact target
    model.addConstr(
        time_procI_A * x_A + time_procI_B * x_B - d3ap + d3am == procI_target,
        name="goal_procI"
    )

    # p3b: Process II maximization (maximize usage relative to cap_procII)
    model.addConstr(
        time_procII_A * x_A + time_procII_B * x_B - d4p + d4m == cap_procII,
        name="goal_procII"
    )

    # Preemptive goal programming via weighted objective with large penalty weights
    # Priority levels: p1 >> p2 >> p3
    # Within p3: minimize d3am + d3ap (Process I exact) and maximize Process II usage (minimize d4m)
    # We use penalty weights: p1 weight = M^2, p2 weight = M, p3 weight = 1
    M = 1e6

    # Objective: minimize weighted deviations
    # p1: minimize underachievement of profit (d1m)
    # p2: minimize underachievement of min_A (d2am) and min_B (d2bm)
    # p3: minimize both deviations of Process I (d3am + d3ap), and minimize d4m (maximize Process II usage)
    model.setObjective(
        M * M * d1m
        + M * (d2am + d2bm)
        + 1.0 * (d3am + d3ap)
        + 1.0 * d4m,
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 0.0 (optimal) | -5.0 (optimal) | 0.0 (optimal) |
| 1 | 0.0 (optimal) | -74.8579876406059 (optimal) | 0.0 (optimal) |
| 2 | 171.23052464102236 (optimal) | 56.84549212479063 (optimal) | 171.23052464102236 (optimal) |
| 3 | 0.0 (optimal) | -64.0182191673812 (optimal) | 0.0 (optimal) |
| 4 | 0.0 (optimal) | 6.134580132246015 (optimal) | 0.0 (optimal) |
| 5 | 0.0 (optimal) | -10.234032898159455 (optimal) | 0.0 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 0.0 (optimal) | -5.0 (optimal) | 0.0 (optimal) |
| 1 | 0.0 (optimal) | -74.8579876406059 (optimal) | 0.0 (optimal) |
| 2 | 171.23052464102236 (optimal) | 56.84549212479063 (optimal) | 171.23052464102236 (optimal) |
| 3 | 0.0 (optimal) | -64.0182191673812 (optimal) | 0.0 (optimal) |
| 4 | 0.0 (optimal) | 6.134580132246015 (optimal) | 0.0 (optimal) |
| 5 | 0.0 (optimal) | -10.234032898159455 (optimal) | 0.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 12. industryor_65 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_65` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 65) |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 194.66666666666669 |
| Label (original benchmark) | 6105 |
| Rules that certify it | panel_base_2of3 194.66666666666669 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A company produces two types of small motorcycles, with Type A being completely manufactured by the company and Type B being assembled from imported parts. The manufacturing, assembly, and inspection times required for these two products are shown in Table 3.2.
Table 3.2

| Type | Manufacturing | Assembly | Inspection | Selling Price <br> (yuan per unit) |
| :---: | :---: | :---: | :---: | :---: |
|  |  |  |  |  |
| Type A (hours per unit) | 20 | 5 | 3 | 650 |
| Type B (hours per unit) | 0 | 7 | 6 | 725 |
| Maximum weekly production capacity (hours) | 120 | 80 | 40 |  |
| Hourly production cost (yuan) | 12 | 8 | 10 |  |

If the company's expected goals and priority levels are as follows:

$p_{1}$: Total weekly profit is at least 3000 yuan;

$p_{2}$: At least 5 units of Type A motorcycles are produced weekly;

$p_{3}$: Minimize the idle time of each process, with the coefficients of the three processes being proportional to their hourly costs, and no overtime is allowed.

Formulate an objective programming model for this problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"man_hours_A": {"base":20,"perturb":{"mode":"abs","lo":10.0,"hi":30.0,"integer":false}}
"man_hours_B": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":10.0,"integer":false}}
"asm_hours_A": {"base":5,"perturb":{"mode":"abs","lo":2.0,"hi":9.0,"integer":false}}
"asm_hours_B": {"base":7,"perturb":{"mode":"abs","lo":3.0,"hi":11.0,"integer":false}}
"insp_hours_A": {"base":3,"perturb":{"mode":"abs","lo":1.0,"hi":6.0,"integer":false}}
"insp_hours_B": {"base":6,"perturb":{"mode":"abs","lo":2.0,"hi":10.0,"integer":false}}
"price_A": {"base":650,"perturb":{"mode":"abs","lo":450.0,"hi":850.0,"integer":false}}
"price_B": {"base":725,"perturb":{"mode":"abs","lo":500.0,"hi":950.0,"integer":false}}
"cap_manufacturing": {"base":120,"perturb":{"mode":"abs","lo":70.0,"hi":180.0,"integer":false}}
"cap_assembly": {"base":80,"perturb":{"mode":"abs","lo":50.0,"hi":130.0,"integer":false}}
"cap_inspection": {"base":40,"perturb":{"mode":"abs","lo":25.0,"hi":70.0,"integer":false}}
"cost_manufacturing": {"base":12,"perturb":{"mode":"abs","lo":6.0,"hi":20.0,"integer":false}}
"cost_assembly": {"base":8,"perturb":{"mode":"abs","lo":4.0,"hi":15.0,"integer":false}}
"cost_inspection": {"base":10,"perturb":{"mode":"abs","lo":5.0,"hi":18.0,"integer":false}}
"profit_goal": {"base":3000,"perturb":{"mode":"abs","lo":1500.0,"hi":5000.0,"integer":false}}
"min_A_goal": {"base":5,"perturb":{"mode":"abs","lo":1.0,"hi":10.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
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
```

#### B-structured.py

```python
# IR: {"sets":{"products":["A","B"],"processes":["manufacturing","assembly","inspection"],"priorities":[1,2,3]},"params":["man_hours_A","man_hours_B","asm_hours_A","asm_hours_B","insp_hours_A","insp_hours_B","price_A","price_B","cap_manufacturing","cap_assembly","cap_inspection","cost_manufacturing","cost_assembly","cost_inspection","profit_goal","min_A_goal"],"derived":{"hours":{"manufacturing":{"A":"man_hours_A","B":"man_hours_B"},"assembly":{"A":"asm_hours_A","B":"asm_hours_B"},"inspection":{"A":"insp_hours_A","B":"insp_hours_B"}},"unit_profit[t]":"price[t]-sum(cost[r]*hours[r,t] for r in processes)"},"variables":{"production[t]":"NonNegativeIntegers","profit_shortfall":"NonNegativeReals","A_shortfall":"NonNegativeReals","idle[r]":"NonNegativeReals"},"constraints":["sum(hours[r,t]*production[t] for t in products)+idle[r]=capacity[r] for each process r; nonnegative idle forbids overtime","sum(unit_profit[t]*production[t] for t in products)+profit_shortfall>=profit_goal","production[A]+A_shortfall>=min_A_goal","After each of priorities 1 and 2, fix its objective expression at its retrieved optimum."],"objective":{"sense":"minimize","method":"sequential lexicographic optimization","priority_1":"profit_shortfall","priority_2":"A_shortfall","priority_3":"sum(cost[r]*idle[r] for r in processes)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.processes = pyo.Set(
        initialize=["manufacturing", "assembly", "inspection"],
        ordered=True,
    )

    model.hours = pyo.Param(
        model.processes,
        model.products,
        initialize={
            ("manufacturing", "A"): params["man_hours_A"],
            ("manufacturing", "B"): params["man_hours_B"],
            ("assembly", "A"): params["asm_hours_A"],
            ("assembly", "B"): params["asm_hours_B"],
            ("inspection", "A"): params["insp_hours_A"],
            ("inspection", "B"): params["insp_hours_B"],
        },
        within=pyo.Reals,
    )
    model.selling_price = pyo.Param(
        model.products,
        initialize={
            "A": params["price_A"],
            "B": params["price_B"],
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.processes,
        initialize={
            "manufacturing": params["cap_manufacturing"],
            "assembly": params["cap_assembly"],
            "inspection": params["cap_inspection"],
        },
        within=pyo.Reals,
    )
    model.hourly_cost = pyo.Param(
        model.processes,
        initialize={
            "manufacturing": params["cost_manufacturing"],
            "assembly": params["cost_assembly"],
            "inspection": params["cost_inspection"],
        },
        within=pyo.Reals,
    )
    model.profit_target = pyo.Param(
        initialize=params["profit_goal"], within=pyo.Reals
    )
    model.A_target = pyo.Param(
        initialize=params["min_A_goal"], within=pyo.Reals
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeIntegers
    )
    model.profit_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.A_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.idle = pyo.Var(model.processes, domain=pyo.NonNegativeReals)

    def unit_profit_rule(current_model, product):
        return current_model.selling_price[product] - sum(
            current_model.hourly_cost[process]
            * current_model.hours[process, product]
            for process in current_model.processes
        )

    model.unit_profit = pyo.Expression(
        model.products, rule=unit_profit_rule
    )
    model.weekly_profit = pyo.Expression(
        expr=sum(
            model.unit_profit[product] * model.production[product]
            for product in model.products
        )
    )

    def capacity_rule(current_model, process):
        return (
            sum(
                current_model.hours[process, product]
                * current_model.production[product]
                for product in current_model.products
            )
            + current_model.idle[process]
            == current_model.capacity[process]
        )

    model.capacity_balance = pyo.Constraint(
        model.processes, rule=capacity_rule
    )
    model.profit_goal_constraint = pyo.Constraint(
        expr=model.weekly_profit + model.profit_shortfall
        >= model.profit_target
    )
    model.A_goal_constraint = pyo.Constraint(
        expr=model.production["A"] + model.A_shortfall >= model.A_target
    )

    model.weighted_idle_cost = pyo.Expression(
        expr=sum(
            model.hourly_cost[process] * model.idle[process]
            for process in model.processes
        )
    )
    model.priority_locks = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=model.profit_shortfall, sense=pyo.minimize
    )

    priority_expressions = (
        model.profit_shortfall,
        model.A_shortfall,
        model.weighted_idle_cost,
    )

    for priority_position, expression in enumerate(priority_expressions):
        model.goal_objective.set_value(expression)

        try:
            Highs().solve(model)
        except RuntimeError as exc:
            if "a feasible solution was not found" in str(exc).lower():
                return {
                    "objective": None,
                    "status": "no_feasible_solution",
                }
            raise

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except ValueError:
            return {
                "objective": None,
                "status": "objective_unavailable",
            }

        if priority_position < len(priority_expressions) - 1:
            model.priority_locks.add(expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    man_hours_A = params["man_hours_A"]
    man_hours_B = params["man_hours_B"]
    asm_hours_A = params["asm_hours_A"]
    asm_hours_B = params["asm_hours_B"]
    insp_hours_A = params["insp_hours_A"]
    insp_hours_B = params["insp_hours_B"]
    price_A = params["price_A"]
    price_B = params["price_B"]
    cap_manufacturing = params["cap_manufacturing"]
    cap_assembly = params["cap_assembly"]
    cap_inspection = params["cap_inspection"]
    cost_manufacturing = params["cost_manufacturing"]
    cost_assembly = params["cost_assembly"]
    cost_inspection = params["cost_inspection"]
    profit_goal = params["profit_goal"]
    min_A_goal = params["min_A_goal"]

    # Compute profit per unit (selling price minus production costs)
    profit_A = (price_A
                - man_hours_A * cost_manufacturing
                - asm_hours_A * cost_assembly
                - insp_hours_A * cost_inspection)
    profit_B = (price_B
                - man_hours_B * cost_manufacturing
                - asm_hours_B * cost_assembly
                - insp_hours_B * cost_inspection)

    model = gp.Model("goal_programming_motorcycles")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of Type A and Type B produced
    x_A = model.addVar(lb=0.0, name="x_A")
    x_B = model.addVar(lb=0.0, name="x_B")

    # Goal deviation variables (non-negative)
    # Goal 1: profit >= profit_goal  =>  profit_A*x_A + profit_B*x_B + d1_neg - d1_pos = profit_goal
    d1_neg = model.addVar(lb=0.0, name="d1_neg")  # underachievement (bad)
    d1_pos = model.addVar(lb=0.0, name="d1_pos")  # overachievement (fine)

    # Goal 2: x_A >= min_A_goal  =>  x_A + d2_neg - d2_pos = min_A_goal
    d2_neg = model.addVar(lb=0.0, name="d2_neg")  # underachievement (bad)
    d2_pos = model.addVar(lb=0.0, name="d2_pos")  # overachievement (fine)

    # Goal 3: minimize idle time in each process (no overtime => only d3x_neg matters as idle,
    #         and we penalize underutilization weighted by hourly cost; no overtime means d3x_pos = 0 is desired)
    # Manufacturing: man_hours_A*x_A + man_hours_B*x_B + d3m_neg - d3m_pos = cap_manufacturing
    d3m_neg = model.addVar(lb=0.0, name="d3m_neg")  # idle manufacturing hours
    d3m_pos = model.addVar(lb=0.0, name="d3m_pos")  # overtime manufacturing (to be zeroed by constraint)

    # Assembly: asm_hours_A*x_A + asm_hours_B*x_B + d3a_neg - d3a_pos = cap_assembly
    d3a_neg = model.addVar(lb=0.0, name="d3a_neg")  # idle assembly hours
    d3a_pos = model.addVar(lb=0.0, name="d3a_pos")  # overtime assembly

    # Inspection: insp_hours_A*x_A + insp_hours_B*x_B + d3i_neg - d3i_pos = cap_inspection
    d3i_neg = model.addVar(lb=0.0, name="d3i_neg")  # idle inspection hours
    d3i_pos = model.addVar(lb=0.0, name="d3i_pos")  # overtime inspection

    # Goal constraints
    model.addConstr(
        profit_A * x_A + profit_B * x_B + d1_neg - d1_pos == profit_goal,
        name="goal_profit"
    )
    model.addConstr(
        x_A + d2_neg - d2_pos == min_A_goal,
        name="goal_min_A"
    )
    model.addConstr(
        man_hours_A * x_A + man_hours_B * x_B + d3m_neg - d3m_pos == cap_manufacturing,
        name="goal_manufacturing"
    )
    model.addConstr(
        asm_hours_A * x_A + asm_hours_B * x_B + d3a_neg - d3a_pos == cap_assembly,
        name="goal_assembly"
    )
    model.addConstr(
        insp_hours_A * x_A + insp_hours_B * x_B + d3i_neg - d3i_pos == cap_inspection,
        name="goal_inspection"
    )

    # No overtime hard constraints (p3: no overtime allowed)
    model.addConstr(d3m_pos == 0.0, name="no_overtime_manufacturing")
    model.addConstr(d3a_pos == 0.0, name="no_overtime_assembly")
    model.addConstr(d3i_pos == 0.0, name="no_overtime_inspection")

    # Preemptive goal programming via weighted objective over priorities.
    # We use a large-M weighting approach to encode lexicographic priorities:
    #   p1 >> p2 >> p3
    # Weights: M^2 for p1, M for p2, 1 for p3 (M large enough to separate priorities).
    # p1: minimize d1_neg (profit underachievement)
    # p2: minimize d2_neg (Type A underproduction)
    # p3: minimize weighted idle time (cost_manufacturing*d3m_neg + cost_assembly*d3a_neg + cost_inspection*d3i_neg)
    big_M = 1e6

    obj = (big_M * big_M * d1_neg
           + big_M * d2_neg
           + cost_manufacturing * d3m_neg
           + cost_assembly * d3a_neg
           + cost_inspection * d3i_neg)

    model.setObjective(obj, GRB.MINIMIZE)
    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 194.66666666666669 (optimal) | 272.0 (optimal) | 194.66666666666666 (optimal) |
| 1 | 768903656.2540754 (optimal) | 449.7822961190948 (optimal) | 768902640637902.2 (optimal) |
| 2 | 2506982976.477302 (optimal) | 1416.5235044317594 (optimal) | 2506979672794183.0 (optimal) |
| 3 | 162.16556352452804 (optimal) | 393.533900728801 (optimal) | 162.16556352452807 (optimal) |
| 4 | 846792118.3793048 (optimal) | 1504.4306031845665 (optimal) | 846787427547154.2 (optimal) |
| 5 | 408.92555700045784 (optimal) | 419.85743991836046 (optimal) | 408.925557000457 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 194.66666666666669 (optimal) | 272.0 (optimal) | 194.66666666666666 (optimal) |
| 1 | 768903656.2540754 (optimal) | 449.7822961190948 (optimal) | 768902640637902.2 (optimal) |
| 2 | 2506982976.477302 (optimal) | 1416.5235044317594 (optimal) | 2506979672794183.0 (optimal) |
| 3 | 162.16556352452804 (optimal) | 393.533900728801 (optimal) | 162.16556352452807 (optimal) |
| 4 | 846792118.3793048 (optimal) | 1504.4306031845665 (optimal) | 846787427547154.2 (optimal) |
| 5 | 408.92555700045784 (optimal) | 419.85743991836046 (optimal) | 408.925557000457 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 13. industryor_79 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_79` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 79) |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 479830000.0 |
| Label (original benchmark) | 435431000 |
| Rules that certify it | gate 479830000.0, panel_base_2of3 479830000.0, ind_gate 479830000.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 435431000 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol) |

### 2. Problem text

```
The independent country of Carelland primarily exports four commodities: steel, engines, electronic components, and plastics. The Finance Minister of Carelland (i.e., the Minister of Economy) wants to maximize exports and minimize imports. The unit prices of steel, engines, electronics, and plastics on the world market, expressed in the local currency (Klunz), are: 500, 1500, 300, and 1200, respectively. Producing 1 unit of steel requires 0.02 units of engines, 0.01 units of plastics, 250 Klunz of other imported goods, and 6 person-months of work. Producing 1 unit of engines requires 0.8 units of steel, 0.15 units of electronic components, 0.11 units of plastics, 300 Klunz of imported goods, and 1 person-year. Producing 1 unit of electronics requires 0.01 units of steel, 0.01 units of engines, 0.05 units of plastics, 50 Klunz of imported goods, and 6 person-months. Producing 1 unit of plastics requires 0.03 units of engines, 0.2 units of steel, 0.05 units of electronic components, 300 Klunz of imported goods, and 2 person-years. The production limit for engines is 650,000 units, and the production limit for plastics is 60,000 units. The total available labor force per year is 830,000. Write a mathematical program to maximize the gross domestic product and solve the problem using AMPL.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"steel_price": {"base":500,"perturb":{"mode":"rel","r":0.4}}
"engines_price": {"base":1500,"perturb":{"mode":"rel","r":0.4}}
"electronics_price": {"base":300,"perturb":{"mode":"rel","r":0.4}}
"plastics_price": {"base":1200,"perturb":{"mode":"rel","r":0.4}}
"a_steel_engines": {"base":0.02,"perturb":{"mode":"rel","r":0.5}}
"a_steel_plastics": {"base":0.01,"perturb":{"mode":"rel","r":0.5}}
"import_cost_steel": {"base":250,"perturb":{"mode":"rel","r":0.4}}
"labor_steel": {"base":6,"perturb":{"mode":"rel","r":0.3}}
"a_engines_steel": {"base":0.8,"perturb":{"mode":"rel","r":0.3}}
"a_engines_electronics": {"base":0.15,"perturb":{"mode":"rel","r":0.5}}
"a_engines_plastics": {"base":0.11,"perturb":{"mode":"rel","r":0.5}}
"import_cost_engines": {"base":300,"perturb":{"mode":"rel","r":0.4}}
"labor_engines": {"base":1,"perturb":{"mode":"rel","r":0.3}}
"a_electronics_steel": {"base":0.01,"perturb":{"mode":"rel","r":0.5}}
"a_electronics_engines": {"base":0.01,"perturb":{"mode":"rel","r":0.5}}
"a_electronics_plastics": {"base":0.05,"perturb":{"mode":"rel","r":0.5}}
"import_cost_electronics": {"base":50,"perturb":{"mode":"rel","r":0.4}}
"labor_electronics": {"base":6,"perturb":{"mode":"rel","r":0.3}}
"a_plastics_engines": {"base":0.03,"perturb":{"mode":"rel","r":0.5}}
"a_plastics_steel": {"base":0.2,"perturb":{"mode":"rel","r":0.4}}
"a_plastics_electronics": {"base":0.05,"perturb":{"mode":"rel","r":0.5}}
"import_cost_plastics": {"base":300,"perturb":{"mode":"rel","r":0.4}}
"labor_plastics": {"base":2,"perturb":{"mode":"rel","r":0.3}}
"engine_capacity": {"base":650000,"perturb":{"mode":"rel","r":0.5}}
"plastics_capacity": {"base":60000,"perturb":{"mode":"rel","r":0.5}}
"labor_capacity": {"base":830000,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    # Prices (Klunz per unit)
    p_steel = params["steel_price"]
    p_eng = params["engines_price"]
    p_elec = params["electronics_price"]
    p_plas = params["plastics_price"]

    # Inter-industry requirements
    a_steel_eng = params["a_steel_engines"]
    a_steel_plas = params["a_steel_plastics"]
    a_eng_steel = params["a_engines_steel"]
    a_eng_elec = params["a_engines_electronics"]
    a_eng_plas = params["a_engines_plastics"]
    a_elec_steel = params["a_electronics_steel"]
    a_elec_eng = params["a_electronics_engines"]
    a_elec_plas = params["a_electronics_plastics"]
    a_plas_eng = params["a_plastics_engines"]
    a_plas_steel = params["a_plastics_steel"]
    a_plas_elec = params["a_plastics_electronics"]

    # Import costs (Klunz per unit)
    ic_steel = params["import_cost_steel"]
    ic_eng = params["import_cost_engines"]
    ic_elec = params["import_cost_electronics"]
    ic_plas = params["import_cost_plastics"]

    # Labor requirements
    lab_steel = params["labor_steel"]          # person-months
    lab_eng = params["labor_engines"]          # person-years
    lab_elec = params["labor_electronics"]     # person-months
    lab_plas = params["labor_plastics"]        # person-years

    # Capacities
    eng_cap = params["engine_capacity"]
    plas_cap = params["plastics_capacity"]
    labor_cap = params["labor_capacity"]

    # Convert person-months to person-years (12 months per year)
    months_per_year = 12

    model = pyo.ConcreteModel()

    # Decision variables: gross production of each commodity
    model.x_steel = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_engines = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_electronics = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_plastics = pyo.Var(domain=pyo.NonNegativeReals)

    # Net exports (production minus intermediate use minus imports)
    # GDP in market prices = value of net exports for each good
    def obj_rule(m):
        net_steel = m.x_steel - a_eng_steel * m.x_engines - a_elec_steel * m.x_electronics - a_plas_steel * m.x_plastics
        net_eng = m.x_engines - a_steel_eng * m.x_steel - a_elec_eng * m.x_electronics - a_plas_eng * m.x_plastics
        net_elec = m.x_electronics - a_eng_elec * m.x_engines - a_plas_elec * m.x_plastics
        net_plas = m.x_plastics - a_steel_plas * m.x_steel - a_eng_plas * m.x_engines - a_elec_plas * m.x_electronics
        imports = (ic_steel * m.x_steel + ic_eng * m.x_engines +
                   ic_elec * m.x_electronics + ic_plas * m.x_plastics)
        return (p_steel * net_steel + p_eng * net_eng +
                p_elec * net_elec + p_plas * net_plas - imports)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Capacity constraints
    model.eng_cap_con = pyo.Constraint(expr=model.x_engines <= eng_cap)
    model.plas_cap_con = pyo.Constraint(expr=model.x_plastics <= plas_cap)

    # Labor constraint (convert person-months to person-years)
    def labor_rule(m):
        return ((lab_steel / months_per_year) * m.x_steel +
                lab_eng * m.x_engines +
                (lab_elec / months_per_year) * m.x_electronics +
                lab_plas * m.x_plastics) <= labor_cap

    model.labor_con = pyo.Constraint(rule=labor_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "solve_failed: " + type(exc).__name__}
```

#### B-structured.py

```python
# IR: {"sets":{"C":["steel","engines","electronics","plastics"],"E":[["engines","steel"],["plastics","steel"],["steel","engines"],["electronics","engines"],["plastics","engines"],["steel","electronics"],["engines","electronics"],["plastics","electronics"],["engines","plastics"],["steel","plastics"],["electronics","plastics"]]},"params":{"price":["steel_price","engines_price","electronics_price","plastics_price"],"a_input_output":["a_steel_engines","a_steel_plastics","a_engines_steel","a_engines_electronics","a_engines_plastics","a_electronics_steel","a_electronics_engines","a_electronics_plastics","a_plastics_engines","a_plastics_steel","a_plastics_electronics"],"other_import_cost":["import_cost_steel","import_cost_engines","import_cost_electronics","import_cost_plastics"],"labor_years":{"steel":"labor_steel/12","engines":"labor_engines","electronics":"labor_electronics/12","plastics":"labor_plastics"},"capacity":["engine_capacity","plastics_capacity"],"labor_capacity":"labor_capacity"},"variables":{"production[c]":"nonnegative continuous","exports[c]":"nonnegative continuous","imports[c]":"nonnegative continuous"},"constraints":["For each c: production[c]+imports[c]=exports[c]+sum(a[c,j]*production[j] for (c,j) in E).","production[engines]<=engine_capacity.","production[plastics]<=plastics_capacity.","sum(labor_years[c]*production[c] for c in C)<=labor_capacity."],"objective":"maximize sum(price[c]*(exports[c]-imports[c])-other_import_cost[c]*production[c] for c in C)","assumptions":["Annual steady state; commodity imports and exports are allowed at the given world prices; 12 months equal one year."]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Maximize annual net export value, including other imported inputs."""
    commodities = ("steel", "engines", "electronics", "plastics")

    price_data = {
        "steel": params["steel_price"],
        "engines": params["engines_price"],
        "electronics": params["electronics_price"],
        "plastics": params["plastics_price"],
    }

    # Keys are (input commodity, output commodity).
    input_data = {
        ("engines", "steel"): params["a_steel_engines"],
        ("plastics", "steel"): params["a_steel_plastics"],
        ("steel", "engines"): params["a_engines_steel"],
        ("electronics", "engines"): params["a_engines_electronics"],
        ("plastics", "engines"): params["a_engines_plastics"],
        ("steel", "electronics"): params["a_electronics_steel"],
        ("engines", "electronics"): params["a_electronics_engines"],
        ("plastics", "electronics"): params["a_electronics_plastics"],
        ("engines", "plastics"): params["a_plastics_engines"],
        ("steel", "plastics"): params["a_plastics_steel"],
        ("electronics", "plastics"): params["a_plastics_electronics"],
    }

    other_import_cost_data = {
        "steel": params["import_cost_steel"],
        "engines": params["import_cost_engines"],
        "electronics": params["import_cost_electronics"],
        "plastics": params["import_cost_plastics"],
    }

    # Twelve is a unit-conversion constant, not a problem-data value.
    labor_years_data = {
        "steel": params["labor_steel"] / 12,
        "engines": params["labor_engines"],
        "electronics": params["labor_electronics"] / 12,
        "plastics": params["labor_plastics"],
    }

    model = pyo.ConcreteModel()

    model.commodities = pyo.Set(initialize=commodities, ordered=True)
    model.input_edges = pyo.Set(
        dimen=2, initialize=tuple(input_data), ordered=True
    )

    model.world_price = pyo.Param(
        model.commodities,
        initialize=price_data,
        within=pyo.NonNegativeReals,
    )
    model.input_requirement = pyo.Param(
        model.input_edges,
        initialize=input_data,
        within=pyo.NonNegativeReals,
    )
    model.other_import_cost = pyo.Param(
        model.commodities,
        initialize=other_import_cost_data,
        within=pyo.NonNegativeReals,
    )
    model.labor_years = pyo.Param(
        model.commodities,
        initialize=labor_years_data,
        within=pyo.NonNegativeReals,
    )
    model.engine_capacity = pyo.Param(
        initialize=params["engine_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.plastics_capacity = pyo.Param(
        initialize=params["plastics_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.labor_capacity = pyo.Param(
        initialize=params["labor_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.commodities, domain=pyo.NonNegativeReals
    )
    model.exports = pyo.Var(
        model.commodities, domain=pyo.NonNegativeReals
    )
    model.imports = pyo.Var(
        model.commodities, domain=pyo.NonNegativeReals
    )

    def commodity_balance_rule(block, commodity):
        intermediate_demand = sum(
            block.input_requirement[input_commodity, output_commodity]
            * block.production[output_commodity]
            for input_commodity, output_commodity in block.input_edges
            if input_commodity == commodity
        )
        return (
            block.production[commodity] + block.imports[commodity]
            == block.exports[commodity] + intermediate_demand
        )

    model.commodity_balance = pyo.Constraint(
        model.commodities, rule=commodity_balance_rule
    )
    model.engine_limit = pyo.Constraint(
        expr=model.production["engines"] <= model.engine_capacity
    )
    model.plastics_limit = pyo.Constraint(
        expr=model.production["plastics"] <= model.plastics_capacity
    )
    model.labor_limit = pyo.Constraint(
        expr=sum(
            model.labor_years[commodity] * model.production[commodity]
            for commodity in model.commodities
        )
        <= model.labor_capacity
    )

    model.gdp = pyo.Objective(
        expr=sum(
            model.world_price[commodity]
            * (model.exports[commodity] - model.imports[commodity])
            - model.other_import_cost[commodity]
            * model.production[commodity]
            for commodity in model.commodities
        ),
        sense=pyo.maximize,
    )

    # Appsi can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines the returned success status.
    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.gdp))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    steel_price         = params["steel_price"]
    engines_price       = params["engines_price"]
    electronics_price   = params["electronics_price"]
    plastics_price      = params["plastics_price"]

    a_steel_engines         = params["a_steel_engines"]
    a_steel_plastics        = params["a_steel_plastics"]
    import_cost_steel       = params["import_cost_steel"]
    labor_steel             = params["labor_steel"]          # person-months

    a_engines_steel         = params["a_engines_steel"]
    a_engines_electronics   = params["a_engines_electronics"]
    a_engines_plastics      = params["a_engines_plastics"]
    import_cost_engines     = params["import_cost_engines"]
    labor_engines           = params["labor_engines"]        # person-years

    a_electronics_steel     = params["a_electronics_steel"]
    a_electronics_engines   = params["a_electronics_engines"]
    a_electronics_plastics  = params["a_electronics_plastics"]
    import_cost_electronics = params["import_cost_electronics"]
    labor_electronics       = params["labor_electronics"]    # person-months

    a_plastics_engines      = params["a_plastics_engines"]
    a_plastics_steel        = params["a_plastics_steel"]
    a_plastics_electronics  = params["a_plastics_electronics"]
    import_cost_plastics    = params["import_cost_plastics"]
    labor_plastics          = params["labor_plastics"]       # person-years

    engine_capacity   = params["engine_capacity"]
    plastics_capacity = params["plastics_capacity"]
    labor_capacity    = params["labor_capacity"]             # person-years

    # Convert person-months to person-years for the labor constraint
    labor_steel_py       = labor_steel / 12.0
    labor_electronics_py = labor_electronics / 12.0

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: total (gross) production of each commodity
    x_steel       = model.addVar(lb=0.0, name="x_steel")
    x_engines     = model.addVar(lb=0.0, name="x_engines")
    x_electronics = model.addVar(lb=0.0, name="x_electronics")
    x_plastics    = model.addVar(lb=0.0, name="x_plastics")

    # Objective: maximize GDP
    # GDP = total export revenues - total import costs - value of intermediate goods consumed
    # For each commodity i:
    #   contribution = price_i * x_i
    #                - import_cost_i * x_i
    #                - sum_j (a_{i,j} * price_j) * x_i   [domestic intermediates valued at world price]
    #
    # Inputs to steel:    engines (a_steel_engines),   plastics (a_steel_plastics)
    # Inputs to engines:  steel   (a_engines_steel),   electronics (a_engines_electronics), plastics (a_engines_plastics)
    # Inputs to electronics: steel (a_electronics_steel), engines (a_electronics_engines), plastics (a_electronics_plastics)
    # Inputs to plastics: engines (a_plastics_engines), steel (a_plastics_steel), electronics (a_plastics_electronics)

    coeff_steel = (steel_price
                   - import_cost_steel
                   - a_steel_engines   * engines_price
                   - a_steel_plastics  * plastics_price)

    coeff_engines = (engines_price
                     - import_cost_engines
                     - a_engines_steel        * steel_price
                     - a_engines_electronics  * electronics_price
                     - a_engines_plastics     * plastics_price)

    coeff_electronics = (electronics_price
                         - import_cost_electronics
                         - a_electronics_steel   * steel_price
                         - a_electronics_engines * engines_price
                         - a_electronics_plastics * plastics_price)

    coeff_plastics = (plastics_price
                      - import_cost_plastics
                      - a_plastics_engines     * engines_price
                      - a_plastics_steel       * steel_price
                      - a_plastics_electronics * electronics_price)

    model.setObjective(
        coeff_steel       * x_steel
        + coeff_engines     * x_engines
        + coeff_electronics * x_electronics
        + coeff_plastics    * x_plastics,
        GRB.MAXIMIZE
    )

    # Material balance: production of each good >= internal use as intermediate input
    # (ensures net exports >= 0, i.e., Carelland doesn't import what it can produce)

    # Steel is used by: engines production, electronics production, plastics production
    model.addConstr(
        x_steel >= a_engines_steel * x_engines
                 + a_electronics_steel * x_electronics
                 + a_plastics_steel * x_plastics,
        name="balance_steel"
    )

    # Engines are used by: steel production, electronics production, plastics production
    model.addConstr(
        x_engines >= a_steel_engines * x_steel
                   + a_electronics_engines * x_electronics
                   + a_plastics_engines * x_plastics,
        name="balance_engines"
    )

    # Electronics are used by: engines production, plastics production
    model.addConstr(
        x_electronics >= a_engines_electronics * x_engines
                        + a_plastics_electronics * x_plastics,
        name="balance_electronics"
    )

    # Plastics are used by: steel production, engines production, electronics production
    model.addConstr(
        x_plastics >= a_steel_plastics * x_steel
                    + a_engines_plastics * x_engines
                    + a_electronics_plastics * x_electronics,
        name="balance_plastics"
    )

    # Capacity constraints
    model.addConstr(x_engines  <= engine_capacity,   name="cap_engines")
    model.addConstr(x_plastics <= plastics_capacity, name="cap_plastics")

    # Labor constraint (all in person-years)
    model.addConstr(
        labor_steel_py       * x_steel
        + labor_engines        * x_engines
        + labor_electronics_py * x_electronics
        + labor_plastics       * x_plastics
        <= labor_capacity,
        name="labor"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 479830000.0 (optimal) | 479830000.0 (optimal) | 435431250.0 (optimal) |
| 1 | 356975280.3747085 (optimal) | 356975280.3747085 (optimal) | 335025536.2746923 (optimal) |
| 2 | 394931361.9325028 (optimal) | 394931361.93250287 (optimal) | 359127215.79657376 (optimal) |
| 3 | 663033319.994826 (optimal) | 663033319.9948261 (optimal) | 538513453.0152688 (optimal) |
| 4 | 492984326.7922547 (optimal) | 492984326.7922547 (optimal) | 422255871.50256604 (optimal) |
| 5 | 792009924.7476257 (optimal) | 792009924.7476257 (optimal) | 444139820.63745993 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 479830000.0 (optimal) | 479830000.0 (optimal) | 435431250.0 (optimal) |
| 1 | 356975280.3747085 (optimal) | 356975280.3747085 (optimal) | 335025536.2746923 (optimal) |
| 2 | 394931361.9325028 (optimal) | 394931361.93250287 (optimal) | 359127215.79657376 (optimal) |
| 3 | 663033319.994826 (optimal) | 663033319.9948261 (optimal) | 538513453.0152688 (optimal) |
| 4 | 492984326.7922547 (optimal) | 492984326.7922547 (optimal) | 422255871.50256604 (optimal) |
| 5 | 792009924.7476257 (optimal) | 792009924.7476257 (optimal) | 444139820.63745993 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
The labor parameters mix units: some are person-months and some are person-years, but `labor_capacity` is in person-years. The extracted values for `labor_steel` and `labor_electronics` are stated in person-months in the problem, so there's no mismatch in the raw numbers — the unit conversion issue is a modeling concern, not a parameter extraction error. I'll check only for numeric mismatches and not-stated values.

Going through each parameter against the statement:

- All prices match.
- All input coefficients match.
- All import costs match.
- Labor values match what's stated (6 person-months, 1 person-year, 6 person-months, 2 person-years).
- `engine_capacity` = 650,000 ✓
- `plastics_capacity` = 60,000 ✓
- `labor_capacity` = 830,000 ✓

No production limits are stated for steel or electronics, but those parameters weren't extracted either.

```json
{"mismatch": [], "not_stated": []}
```
````


## 14. industryor_97 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_97` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 97) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 4100.0 |
| Label (original benchmark) | 9500 |
| Rules that certify it | gate 4100.0, panel_base_2of3 4100.0, ind_gate 4100.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A certain store wants to develop a procurement and sales plan for a certain product for the first quarter of next year. It is known that the store's warehouse can store a maximum of 500 units of this product, and there are 200 units of inventory at the end of this year. The store makes a purchase at the beginning of each month. The unit prices for purchasing and selling this product for each month are shown in Table 1.3.

Table 1.3

| Month | 1 | 2 | 3 |
| :---: | :---: | :---: | :---: |
| Purchase Price (in yuan) | 8 | 6 | 9 |
| Selling Price (in yuan) | 9 | 8 | 10 |

Now, to determine how many units should be purchased and sold each month in order to maximize total profit, express this problem as a linear programming model.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"initial_inventory": {"base":200,"perturb":{"mode":"abs","lo":0.0,"hi":400.0,"integer":true}}
"warehouse_capacity": {"base":500,"perturb":{"mode":"abs","lo":200.0,"hi":800.0,"integer":true}}
"purchase_price": {"base":[8,6,9],"perturb":{"mode":"rel","r":0.5}}
"selling_price": {"base":[9,8,10],"perturb":{"mode":"rel","r":0.4}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_inventory = params["initial_inventory"]
    warehouse_capacity = params["warehouse_capacity"]
    purchase_price = params["purchase_price"]
    selling_price = params["selling_price"]

    months = [1, 2, 3]

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=months)

    model.purchase = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.M, within=pyo.NonNegativeReals)

    def inv_rule(mdl, t):
        prev = initial_inventory if t == 1 else mdl.inventory[t - 1]
        return mdl.inventory[t] == prev + mdl.purchase[t] - mdl.sell[t]

    model.inv_con = pyo.Constraint(model.M, rule=inv_rule)

    def cap_rule(mdl, t):
        return mdl.inventory[t] <= warehouse_capacity

    model.cap_con = pyo.Constraint(model.M, rule=cap_rule)

    # Sales cannot exceed available inventory (beginning stock + purchases)
    def sell_rule(mdl, t):
        prev = initial_inventory if t == 1 else mdl.inventory[t - 1]
        return mdl.sell[t] <= prev + mdl.purchase[t]

    model.sell_con = pyo.Constraint(model.M, rule=sell_rule)

    # Initial inventory cannot exceed warehouse capacity
    model.init_cap_con = pyo.Constraint(
        expr=initial_inventory <= warehouse_capacity
    )

    # Cannot purchase more than what fits in the warehouse
    def purchase_cap_rule(mdl, t):
        return mdl.purchase[t] <= warehouse_capacity

    model.purchase_cap_con = pyo.Constraint(model.M, rule=purchase_cap_rule)

    def obj_rule(mdl):
        return sum(
            selling_price[t - 1] * mdl.sell[t] - purchase_price[t - 1] * mdl.purchase[t]
            for t in mdl.M
        )

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"T":[1,2,3]},"params":{"initial_inventory":"nonnegative scalar","warehouse_capacity":"nonnegative scalar","purchase_price":"real vector indexed by T","selling_price":"real vector indexed by T"},"variables":{"purchase[t]":"nonnegative continuous","sales[t]":"nonnegative continuous","inventory[t]":"nonnegative continuous"},"constraints":["inventory[1] = initial_inventory + purchase[1] - sales[1]","inventory[t] = inventory[t-1] + purchase[t] - sales[t] for t in {2,3}","initial_inventory + purchase[1] <= warehouse_capacity","inventory[t-1] + purchase[t] <= warehouse_capacity for t in {2,3}"],"objective":"maximize sum(selling_price[t]*sales[t] - purchase_price[t]*purchase[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the quarterly procurement and sales LP.

    Price inputs may be three-element sequences ordered by month or mappings
    keyed by months 1, 2, 3 (integer keys or string keys).
    Warehouse capacity applies immediately after each monthly purchase.
    """

    def monthly_value(values, month):
        if isinstance(values, Mapping):
            if month in values:
                return values[month]
            return values[str(month)]
        return values[month - 1]

    initial_inventory = params["initial_inventory"]
    warehouse_capacity = params["warehouse_capacity"]
    purchase_price = params["purchase_price"]
    selling_price = params["selling_price"]

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 3)

    model.initial_stock = pyo.Param(
        initialize=initial_inventory,
        within=pyo.NonNegativeReals,
    )
    model.storage_limit = pyo.Param(
        initialize=warehouse_capacity,
        within=pyo.NonNegativeReals,
    )
    model.purchase_cost = pyo.Param(
        model.months,
        initialize={
            month: monthly_value(purchase_price, month)
            for month in model.months
        },
        within=pyo.Reals,
    )
    model.sale_revenue = pyo.Param(
        model.months,
        initialize={
            month: monthly_value(selling_price, month)
            for month in model.months
        },
        within=pyo.Reals,
    )

    model.purchase = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def inventory_balance_rule(instance, month):
        opening_stock = (
            instance.initial_stock
            if month == 1
            else instance.inventory[month - 1]
        )
        return (
            instance.inventory[month]
            == opening_stock + instance.purchase[month] - instance.sales[month]
        )

    model.stock_balance = pyo.Constraint(
        model.months,
        rule=inventory_balance_rule,
    )

    def warehouse_capacity_rule(instance, month):
        opening_stock = (
            instance.initial_stock
            if month == 1
            else instance.inventory[month - 1]
        )
        return (
            opening_stock + instance.purchase[month]
            <= instance.storage_limit
        )

    model.storage_capacity = pyo.Constraint(
        model.months,
        rule=warehouse_capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.sale_revenue[month] * model.sales[month]
            - model.purchase_cost[month] * model.purchase[month]
            for month in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_inventory = params["initial_inventory"]
    warehouse_capacity = params["warehouse_capacity"]
    purchase_price = params["purchase_price"]   # list of 3 values
    selling_price = params["selling_price"]     # list of 3 values

    months = range(3)

    model = gp.Model("procurement_sales")
    model.setParam("OutputFlag", 0)
    model.setParam("DualReductions", 0)

    buy = model.addVars(months, lb=0.0, name="buy")
    sell = model.addVars(months, lb=0.0, name="sell")
    inv = model.addVars(months, lb=0.0, name="inv")

    model.setObjective(
        gp.quicksum(selling_price[t] * sell[t] - purchase_price[t] * buy[t] for t in months),
        GRB.MAXIMIZE
    )

    # Inventory balance: end-of-month inventory
    model.addConstr(inv[0] == initial_inventory + buy[0] - sell[0], name="inv_balance_0")
    for t in range(1, 3):
        model.addConstr(inv[t] == inv[t - 1] + buy[t] - sell[t], name=f"inv_balance_{t}")

    # Warehouse capacity on end-of-month inventory
    for t in months:
        model.addConstr(inv[t] <= warehouse_capacity, name=f"capacity_end_{t}")

    # Warehouse capacity immediately after purchase (before sales)
    # stock after purchase = inv[t-1] + buy[t] for t>0, or initial_inventory + buy[0] for t=0
    model.addConstr(initial_inventory + buy[0] <= warehouse_capacity, name="capacity_post_buy_0")
    for t in range(1, 3):
        model.addConstr(inv[t - 1] + buy[t] <= warehouse_capacity, name=f"capacity_post_buy_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 4100.0 (optimal) | 4100.0 (optimal) |
| 1 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (False) instead of a Pyomo object. Please modify your rule to return Constraint.Infeasible instead of) | none (solve_failed) | none (infeasible) |
| 2 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 3071.0179107978133 (optimal) | 3071.017910797813 (optimal) |
| 3 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 3247.0243866604815 (optimal) | 3247.0243866604815 (optimal) |
| 4 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 7147.66478207955 (optimal) | 7147.66478207955 (optimal) |
| 5 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 7095.257063616753 (optimal) | 7095.257063616753 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 4100.0 (optimal) | 4100.0 (optimal) |
| 1 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (False) instead of a Pyomo object. Please modify your rule to return Constraint.Infeasible instead of) | none (solve_failed) | none (infeasible) |
| 2 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 3071.0179107978133 (optimal) | 3071.017910797813 (optimal) |
| 3 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 3247.0243866604815 (optimal) | 3247.0243866604815 (optimal) |
| 4 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 7147.66478207955 (optimal) | 7147.66478207955 (optimal) |
| 5 | none (crash:ValueError: Invalid constraint expression. The constraint expression resolved to a trivial Boolean (True) instead of a Pyomo object. Please modify your rule to return Constraint.Feasible instead of Tr) | 7095.257063616753 (optimal) | 7095.257063616753 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 15. industryor_98 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_98` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 98) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 510000.0 |
| Label (original benchmark) | 1360000 |
| Rules that certify it | gate 510000.0, panel_base_2of3 510000.0, ind_gate 510000.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol) |

### 2. Problem text

```
An investor plans to invest his 100,000 yuan, and there are two investment options to choose from. The first investment guarantees a profit of 0.7 yuan for every 1 yuan invested after one year. The second investment guarantees a profit of 2 yuan for every 1 yuan invested after two years, but the investment time must be a multiple of two years. In order to maximize the money earned by the end of the third year, how should the investor invest? Represent this problem as a linear programming problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"initial_capital": {"base":100000,"perturb":{"mode":"rel","r":0.5}}
"profit_rate_1yr": {"base":0.7,"perturb":{"mode":"abs","lo":-0.2,"hi":1.5,"integer":false}}
"profit_rate_2yr": {"base":2.0,"perturb":{"mode":"abs","lo":-0.5,"hi":4.0,"integer":false}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_capital = params["initial_capital"]
    profit_rate_1yr = params["profit_rate_1yr"]
    profit_rate_2yr = params["profit_rate_2yr"]

    # Decision variables (in yuan):
    # x1: amount invested in 1-year option at start of year 1
    # x2: amount invested in 2-year option at start of year 1
    # x3: amount invested in 1-year option at start of year 2
    # x4: amount invested in 1-year option at start of year 3
    # Cash carried forward each year: c1 (after year 1), c2 (after year 2), c3 (after year 3)
    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x3 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x4 = pyo.Var(domain=pyo.NonNegativeReals)
    model.c1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.c2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.c3 = pyo.Var(domain=pyo.NonNegativeReals)

    # Year 1: allocate initial capital between 1-year and 2-year options
    model.start_balance = pyo.Constraint(
        expr=model.x1 + model.x2 == initial_capital
    )

    # End of year 1: 1-year returns (principal + profit) plus uninvested cash
    # Note: all capital is invested, so cash after year 1 is 0 unless we treat
    # the returned amount as available. We model available funds pool c1.
    model.year1_balance = pyo.Constraint(
        expr=model.c1 == initial_capital - model.x1 - model.x2
        + model.x1 * (1.0 + profit_rate_1yr)
    )

    # Start of year 2: allocate available funds (c1) to 1-year option (x3)
    # The 2-year option from year 1 continues and has no cash flow yet.
    model.year2_start = pyo.Constraint(
        expr=model.x3 <= model.c1
    )

    # End of year 2: 1-year option from year 2 returns; 2-year option from
    # year 1 matures and returns principal + profit.
    model.year2_balance = pyo.Constraint(
        expr=model.c2 == model.c1 - model.x3
        + model.x3 * (1.0 + profit_rate_1yr)
        + model.x2 * (1.0 + profit_rate_2yr)
    )

    # Start of year 3: allocate available funds (c2) to 1-year option (x4)
    model.year3_start = pyo.Constraint(
        expr=model.x4 <= model.c2
    )

    # End of year 3: 1-year option from year 3 returns; remaining cash stays.
    model.year3_balance = pyo.Constraint(
        expr=model.c3 == model.c2 - model.x4
        + model.x4 * (1.0 + profit_rate_1yr)
    )

    # Maximize total money at end of year 3
    model.total_wealth = pyo.Expression(expr=model.c3)
    model.objective = pyo.Objective(expr=model.total_wealth, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.objective))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "solver failed"}
```

#### B-structured.py

```python
# IR: {"sets":{"T":[0,1,2],"B":[0,1]},"params":["initial_capital","profit_rate_1yr","profit_rate_2yr"],"variables":{"annual[T]":"continuous >= 0","biennial[B]":"continuous >= 0","cash[T]":"continuous >= 0"},"constraints":["annual[0] + biennial[0] + cash[0] = initial_capital","annual[1] + biennial[1] + cash[1] = cash[0] + (1 + profit_rate_1yr)*annual[0]","annual[2] + cash[2] = cash[1] + (1 + profit_rate_1yr)*annual[1] + (1 + profit_rate_2yr)*biennial[0]"],"objective":"maximize cash[2] + (1 + profit_rate_1yr)*annual[2] + (1 + profit_rate_2yr)*biennial[1]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_capital = params["initial_capital"]
    profit_rate_1yr = params["profit_rate_1yr"]
    profit_rate_2yr = params["profit_rate_2yr"]

    model = pyo.ConcreteModel()

    # Times are measured from the beginning of the investment horizon.
    # Each biennial investment remains invested for exactly two years.
    model.T = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.B = pyo.Set(initialize=[0, 1], ordered=True)

    model.initial_capital = pyo.Param(initialize=initial_capital)
    model.profit_rate_1yr = pyo.Param(initialize=profit_rate_1yr)
    model.profit_rate_2yr = pyo.Param(initialize=profit_rate_2yr)

    model.annual = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.biennial = pyo.Var(model.B, domain=pyo.NonNegativeReals)
    model.cash = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    model.initial_budget = pyo.Constraint(
        expr=model.annual[0] + model.biennial[0] + model.cash[0]
        == model.initial_capital
    )

    model.year_one_budget = pyo.Constraint(
        expr=model.annual[1] + model.biennial[1] + model.cash[1]
        == model.cash[0]
        + (1 + model.profit_rate_1yr) * model.annual[0]
    )

    model.year_two_budget = pyo.Constraint(
        expr=model.annual[2] + model.cash[2]
        == model.cash[1]
        + (1 + model.profit_rate_1yr) * model.annual[1]
        + (1 + model.profit_rate_2yr) * model.biennial[0]
    )

    # Terminal wealth includes returned principal and investment profits.
    model.terminal_wealth = pyo.Objective(
        expr=model.cash[2]
        + (1 + model.profit_rate_1yr) * model.annual[2]
        + (1 + model.profit_rate_2yr) * model.biennial[1],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when no feasible solution can be loaded.
        # Propagate unrelated runtime errors.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.terminal_wealth))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_capital = params["initial_capital"]
    profit_rate_1yr = params["profit_rate_1yr"]
    profit_rate_2yr = params["profit_rate_2yr"]

    # Return per yuan invested (principal + profit)
    return_1yr = 1 + profit_rate_1yr   # after 1 year
    return_2yr = 1 + profit_rate_2yr   # after 2 years

    # Decision variables:
    # x1: amount invested in 1-year option at start of year 1
    # x2: amount invested in 2-year option at start of year 1 (runs years 1-2)
    # x3: amount invested in 1-year option at start of year 2 (from x1 returns)
    # x4: amount invested in 1-year option at start of year 3
    #     (from x3 returns + x2 returns at end of year 2)
    # x5: amount invested in 2-year option at start of year 3 (runs years 3-4,
    #     but we only count what's available; however the 2-yr option must be
    #     a multiple of 2 years, so it won't mature by end of year 3 —
    #     the investor gets back principal+profit only at end of year 4,
    #     so investing in the 2-yr option at year 3 does NOT contribute to
    #     end-of-year-3 wealth. We exclude it.)
    #
    # Timeline:
    #   Year 0 (start): invest x1 (1-yr) + x2 (2-yr) = initial_capital
    #   End of year 1:  x1 matures -> return_1yr * x1; invest x3 (1-yr)
    #                   x3 <= return_1yr * x1
    #   End of year 2:  x3 matures -> return_1yr * x3
    #                   x2 matures -> return_2yr * x2
    #                   invest x4 (1-yr)
    #                   x4 <= return_1yr * x3 + return_2yr * x2
    #   End of year 3:  x4 matures -> return_1yr * x4
    #                   Total wealth = return_1yr * x4 + (uninvested cash at each stage)
    #
    # To maximize end-of-year-3 wealth we should invest all available cash,
    # but we model it properly with slack (uninvested) variables to keep LP general.

    model = gp.Model("investment")
    model.setParam("OutputFlag", 0)

    x1 = model.addVar(lb=0, name="x1")  # 1-yr investment at t=0
    x2 = model.addVar(lb=0, name="x2")  # 2-yr investment at t=0
    x3 = model.addVar(lb=0, name="x3")  # 1-yr investment at t=1
    x4 = model.addVar(lb=0, name="x4")  # 1-yr investment at t=2

    # Slack (idle cash) at each period
    s0 = model.addVar(lb=0, name="s0")  # idle at t=0
    s1 = model.addVar(lb=0, name="s1")  # idle at t=1 (not reinvested)
    s2 = model.addVar(lb=0, name="s2")  # idle at t=2 (not reinvested)

    # t=0 budget constraint
    model.addConstr(x1 + x2 + s0 == initial_capital, name="budget_t0")

    # t=1: proceeds from x1 and idle s0 can be reinvested as x3 or kept idle
    model.addConstr(x3 + s1 == return_1yr * x1 + s0, name="budget_t1")

    # t=2: proceeds from x3, x2, and idle s1 can be reinvested as x4 or kept idle
    model.addConstr(x4 + s2 == return_1yr * x3 + return_2yr * x2 + s1, name="budget_t2")

    # Objective: total wealth at end of year 3
    # = proceeds from x4 (1-yr at t=2) + idle cash s2
    total_wealth = return_1yr * x4 + s2
    model.setObjective(total_wealth, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        # Profit earned = total wealth minus initial capital
        return {"objective": float(model.ObjVal - initial_capital), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 510000.0 (optimal) | 510000.0 (optimal) | 410000.0 (optimal) |
| 1 | 248270.3377343152 (optimal) | 248270.3377343152 (optimal) | 134327.65788852682 (optimal) |
| 2 | 674279.0893957597 (optimal) | 674279.0893957597 (optimal) | 601958.0155808774 (optimal) |
| 3 | 422969.7507400296 (optimal) | 422969.7507400296 (optimal) | 283751.79396954505 (optimal) |
| 4 | 212571.4525256493 (optimal) | 212571.4525256493 (optimal) | 159591.73058184228 (optimal) |
| 5 | 246056.7453512475 (optimal) | 246056.74535124746 (optimal) | 193403.1483828611 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 510000.0 (optimal) | 510000.0 (optimal) | 410000.0 (optimal) |
| 1 | 197990.438993015 (optimal) | 197990.438993015 (optimal) | 84047.75914722664 (optimal) |
| 2 | 624881.4187114271 (optimal) | 624881.418711427 (optimal) | 552560.3448965447 (optimal) |
| 3 | 333934.899825849 (optimal) | 333934.899825849 (optimal) | 194716.94305536445 (optimal) |
| 4 | 172203.630993631 (optimal) | 172203.630993631 (optimal) | 119223.90904982397 (optimal) |
| 5 | 205198.46071471556 (optimal) | 205198.46071471556 (optimal) | 152544.8637463292 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{"mismatch": [], "not_stated": []}
```
````

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 16. industryor_100 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_100` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 100) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 280.0 |
| Label (original benchmark) | 5500 |
| Rules that certify it | gate 280.0, panel_base_2of3 280.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol) |

### 2. Problem text

```
A certain shoe store employs 5 full-time salespeople and 4 part-time salespeople. Their working hours and salary information are shown in Table 3.3.

Table 3.3

|  | Monthly Working Hours | Sales Volume (pairs/hour) | Salary (CNY/hour) | Overtime Pay (CNY/hour) |
| :---: | :---: | :---: | :---: | :---: |
| Full-time | 160 | 5 | 1 | 1.5 |
| Part-time | 80 | 2 | 0.6 | 0.7 |

A profit of 0.5 CNY is made for each pair of shoes sold. The store has the following objectives:

$p_{1}$: Monthly sales volume reaches 5500 pairs;
$p_{2}$: Full-time salespeople do not exceed 100 hours of overtime;

$p_{3}$: All salespeople are fully employed, but full-time employees should be given double consideration;

$p_{4}$: Minimize overtime hours as much as possible.

Try to establish an objective programming model for this problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"profit_per_pair": {"base":0.5,"perturb":{"mode":"abs","lo":-0.5,"hi":1.5,"integer":false}}
"fulltime_sales_rate": {"base":5,"perturb":{"mode":"abs","lo":2.0,"hi":9.0,"integer":false}}
"parttime_sales_rate": {"base":2,"perturb":{"mode":"abs","lo":0.5,"hi":5.0,"integer":false}}
"fulltime_salary": {"base":1,"perturb":{"mode":"abs","lo":0.5,"hi":2.5,"integer":false}}
"parttime_salary": {"base":0.6,"perturb":{"mode":"abs","lo":0.2,"hi":1.5,"integer":false}}
"fulltime_overtime_pay": {"base":1.5,"perturb":{"mode":"abs","lo":1.0,"hi":4.0,"integer":false}}
"parttime_overtime_pay": {"base":0.7,"perturb":{"mode":"abs","lo":0.2,"hi":2.0,"integer":false}}
"fulltime_hours": {"base":160,"perturb":{"mode":"abs","lo":100.0,"hi":220.0,"integer":true}}
"parttime_hours": {"base":80,"perturb":{"mode":"abs","lo":20.0,"hi":140.0,"integer":true}}
"sales_target": {"base":5500,"perturb":{"mode":"abs","lo":2000.0,"hi":12000.0,"integer":true}}
"fulltime_overtime_limit": {"base":100,"perturb":{"mode":"abs","lo":0.0,"hi":300.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    n_full = 5
    n_part = 4

    # Parameters from params
    profit = params["profit_per_pair"]
    ft_rate = params["fulltime_sales_rate"]
    pt_rate = params["parttime_sales_rate"]
    ft_sal = params["fulltime_salary"]
    pt_sal = params["parttime_salary"]
    ft_ot = params["fulltime_overtime_pay"]
    pt_ot = params["parttime_overtime_pay"]
    ft_hours = params["fulltime_hours"]
    pt_hours = params["parttime_hours"]
    target = params["sales_target"]
    ot_limit = params["fulltime_overtime_limit"]

    model = pyo.ConcreteModel()

    # Decision variables (per-person regular and overtime hours)
    model.xf = pyo.Var(domain=pyo.NonNegativeReals)  # full-time OT hours per person
    model.xp = pyo.Var(domain=pyo.NonNegativeReals)  # part-time OT hours per person

    # Deviational variables for goals
    model.d1p = pyo.Var(domain=pyo.NonNegativeReals)  # over sales target
    model.d1m = pyo.Var(domain=pyo.NonNegativeReals)  # under sales target
    model.d2p = pyo.Var(domain=pyo.NonNegativeReals)  # over OT limit
    model.d2m = pyo.Var(domain=pyo.NonNegativeReals)  # under OT limit
    model.d3m = pyo.Var(domain=pyo.NonNegativeReals)  # underemployment (all staff)

    # Sales volume
    sales = (
        n_full * (ft_rate * ft_hours + ft_rate * model.xf)
        + n_part * (pt_rate * pt_hours + pt_rate * model.xp)
    )

    # Goal 1: sales >= target
    model.goal1 = pyo.Constraint(expr=sales + model.d1m - model.d1p == target)

    # Goal 2: full-time overtime (total) <= limit
    total_ft_ot = n_full * model.xf
    model.goal2 = pyo.Constraint(expr=total_ft_ot + model.d2m - model.d2p == ot_limit)

    # Goal 3: fully employed (no underemployment); double weight for full-time
    # Underemployment expressed in hours below full employment
    model.goal3 = pyo.Constraint(
        expr=model.d3m == model.xf * 0 + model.xp * 0
    )

    # Goal 4: minimize overtime hours
    # Lexicographic handling via weighted objective below.

    # Objective: lexicographic-ish weighted sum reflecting priorities
    # Priority 1 (sales shortfall) dominates; priority 2 (OT over limit) next;
    # priority 3 (underemployment, full-time double); priority 4 (OT hours).
    BIG1 = 1e6
    BIG2 = 1e4
    BIG3 = 1e2
    model.obj = pyo.Objective(
        expr=BIG1 * model.d1m
        + BIG2 * model.d2p
        + BIG3 * model.d3m
        + n_full * model.xf + n_part * model.xp,
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {
#   "sets": {"staff_types": ["fulltime", "parttime"]},
#   "params": ["profit_per_pair", "fulltime_sales_rate", "parttime_sales_rate", "fulltime_salary", "parttime_salary", "fulltime_overtime_pay", "parttime_overtime_pay", "fulltime_hours", "parttime_hours", "sales_target", "fulltime_overtime_limit"],
#   "structural_constants": {"fulltime_count": 5, "parttime_count": 4, "fulltime_idle_weight": 2},
#   "variables": {"regular_hours[staff_types]": "continuous_nonnegative_aggregate_hours", "overtime_hours[staff_types]": "continuous_nonnegative_aggregate_hours", "idle_hours[staff_types]": "continuous_nonnegative_aggregate_hours", "sales_shortfall": "continuous_nonnegative_pairs", "sales_surplus": "continuous_nonnegative_pairs", "overtime_slack": "continuous_nonnegative_hours", "overtime_excess": "continuous_nonnegative_hours"},
#   "expressions": {"sales": "sum(sales_rate[t]*(regular_hours[t]+overtime_hours[t]))", "payroll": "sum(salary[t]*regular_hours[t]+overtime_pay[t]*overtime_hours[t])", "net_profit": "profit_per_pair*sales-payroll"},
#   "constraints": ["regular_hours[t]+idle_hours[t]=staff_count[t]*standard_hours[t] for each t", "sales+sales_shortfall-sales_surplus=sales_target", "overtime_hours[fulltime]+overtime_slack-overtime_excess=fulltime_overtime_limit", "after each nonfinal priority solve, fix that priority expression at its attained optimum"],
#   "objective": {"sense": "lexicographic_minimize", "priorities": ["sales_shortfall", "overtime_excess", "2*idle_hours[fulltime]+idle_hours[parttime]", "sum(overtime_hours[t])"], "returned_objective": "final_priority_total_overtime_hours"}
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the four goals in strict priority order p1, p2, p3, p4.

    Hours and the full-time overtime limit are aggregated across employees
    of each type. Sales above the target are permitted. Economic quantities
    are reported as model expressions; the stated goals do not prioritize
    maximizing profit or minimizing payroll.
    """
    model = pyo.ConcreteModel()

    model.staff_types = pyo.Set(
        initialize=["fulltime", "parttime"], ordered=True
    )
    model.staff_count = pyo.Param(
        model.staff_types,
        initialize={"fulltime": 5, "parttime": 4},
        within=pyo.PositiveIntegers,
    )

    model.profit_per_pair = pyo.Param(
        initialize=params["profit_per_pair"], within=pyo.NonNegativeReals
    )
    model.sales_rate = pyo.Param(
        model.staff_types,
        initialize={
            "fulltime": params["fulltime_sales_rate"],
            "parttime": params["parttime_sales_rate"],
        },
        within=pyo.NonNegativeReals,
    )
    model.salary = pyo.Param(
        model.staff_types,
        initialize={
            "fulltime": params["fulltime_salary"],
            "parttime": params["parttime_salary"],
        },
        within=pyo.NonNegativeReals,
    )
    model.overtime_pay = pyo.Param(
        model.staff_types,
        initialize={
            "fulltime": params["fulltime_overtime_pay"],
            "parttime": params["parttime_overtime_pay"],
        },
        within=pyo.NonNegativeReals,
    )
    model.standard_hours = pyo.Param(
        model.staff_types,
        initialize={
            "fulltime": params["fulltime_hours"],
            "parttime": params["parttime_hours"],
        },
        within=pyo.NonNegativeReals,
    )
    model.sales_target = pyo.Param(
        initialize=params["sales_target"], within=pyo.NonNegativeReals
    )
    model.fulltime_overtime_limit = pyo.Param(
        initialize=params["fulltime_overtime_limit"],
        within=pyo.NonNegativeReals,
    )

    model.regular_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.overtime_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.idle_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.sales_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.sales_surplus = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime_slack = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime_excess = pyo.Var(domain=pyo.NonNegativeReals)

    model.sales = pyo.Expression(
        expr=sum(
            model.sales_rate[staff_type]
            * (
                model.regular_hours[staff_type]
                + model.overtime_hours[staff_type]
            )
            for staff_type in model.staff_types
        )
    )
    model.payroll = pyo.Expression(
        expr=sum(
            model.salary[staff_type] * model.regular_hours[staff_type]
            + model.overtime_pay[staff_type]
            * model.overtime_hours[staff_type]
            for staff_type in model.staff_types
        )
    )
    model.net_profit = pyo.Expression(
        expr=model.profit_per_pair * model.sales - model.payroll
    )

    def employment_balance_rule(instance, staff_type):
        return (
            instance.regular_hours[staff_type]
            + instance.idle_hours[staff_type]
            == instance.staff_count[staff_type]
            * instance.standard_hours[staff_type]
        )

    model.employment_balance = pyo.Constraint(
        model.staff_types, rule=employment_balance_rule
    )
    model.sales_goal = pyo.Constraint(
        expr=model.sales + model.sales_shortfall - model.sales_surplus
        == model.sales_target
    )
    model.fulltime_overtime_goal = pyo.Constraint(
        expr=model.overtime_hours["fulltime"]
        + model.overtime_slack
        - model.overtime_excess
        == model.fulltime_overtime_limit
    )

    priority_expressions = (
        model.sales_shortfall,
        model.overtime_excess,
        2 * model.idle_hours["fulltime"] + model.idle_hours["parttime"],
        sum(
            model.overtime_hours[staff_type]
            for staff_type in model.staff_types
        ),
    )

    model.priority_fixes = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=priority_expressions[0], sense=pyo.minimize
    )

    for priority_index, priority_expression in enumerate(priority_expressions):
        model.goal_objective.set_value(priority_expression)

        # Clear prior solutions so a failed solve cannot expose stale values.
        for variable in model.component_data_objects(pyo.Var):
            variable.set_value(None)

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solver_failed"}

        # Success is determined only by retrieving the objective value.
        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_index < len(priority_expressions) - 1:
            model.priority_fixes.add(priority_expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_pair = params["profit_per_pair"]
    fulltime_sales_rate = params["fulltime_sales_rate"]
    parttime_sales_rate = params["parttime_sales_rate"]
    fulltime_salary = params["fulltime_salary"]
    parttime_salary = params["parttime_salary"]
    fulltime_overtime_pay = params["fulltime_overtime_pay"]
    parttime_overtime_pay = params["parttime_overtime_pay"]
    fulltime_hours = params["fulltime_hours"]
    parttime_hours = params["parttime_hours"]
    sales_target = params["sales_target"]
    fulltime_overtime_limit = params["fulltime_overtime_limit"]

    # Number of full-time and part-time salespeople
    n_fulltime = 5
    n_parttime = 4

    model = gp.Model("shoe_store_goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: overtime hours for full-time (x1) and part-time (x2)
    x1 = model.addVar(lb=0.0, name="x1")  # overtime hours per full-time salesperson
    x2 = model.addVar(lb=0.0, name="x2")  # overtime hours per part-time salesperson

    # Goal deviation variables (non-negative)
    # p1: sales target - d1_minus (underachievement), d1_plus (overachievement)
    d1_minus = model.addVar(lb=0.0, name="d1_minus")
    d1_plus  = model.addVar(lb=0.0, name="d1_plus")

    # p2: fulltime overtime limit - d2_minus, d2_plus
    d2_minus = model.addVar(lb=0.0, name="d2_minus")
    d2_plus  = model.addVar(lb=0.0, name="d2_plus")

    # p3: full employment goals
    # Full-time: total hours = n_fulltime * fulltime_hours (target), deviation d3f
    d3f_minus = model.addVar(lb=0.0, name="d3f_minus")
    d3f_plus  = model.addVar(lb=0.0, name="d3f_plus")
    # Part-time: total hours = n_parttime * parttime_hours (target), deviation d3p
    d3p_minus = model.addVar(lb=0.0, name="d3p_minus")
    d3p_plus  = model.addVar(lb=0.0, name="d3p_plus")

    # p4: minimize overtime hours
    # d4f = overtime hours for full-time staff (total), d4p = part-time
    d4f = model.addVar(lb=0.0, name="d4f")
    d4p = model.addVar(lb=0.0, name="d4p")

    # Total sales volume
    # Full-time: each works fulltime_hours + x1 hours; n_fulltime people
    # Part-time: each works parttime_hours + x2 hours; n_parttime people
    total_sales = (n_fulltime * (fulltime_hours + x1) * fulltime_sales_rate +
                   n_parttime * (parttime_hours + x2) * parttime_sales_rate)

    # Goal constraints
    # p1: total sales >= sales_target
    model.addConstr(
        total_sales - d1_plus + d1_minus == sales_target,
        name="goal_sales"
    )

    # p2: full-time overtime <= fulltime_overtime_limit
    # x1 is per-person overtime; total full-time overtime = n_fulltime * x1
    # The constraint is on per-person overtime: x1 <= fulltime_overtime_limit
    model.addConstr(
        x1 - d2_plus + d2_minus == fulltime_overtime_limit,
        name="goal_ft_overtime"
    )

    # p3a: full-time total working hours = n_fulltime * fulltime_hours (fully employed = no overtime ideally)
    # "fully employed" means actual hours >= standard hours, so we track underemployment
    # Total full-time hours worked = n_fulltime * (fulltime_hours + x1)
    # Target = n_fulltime * fulltime_hours (standard hours)
    model.addConstr(
        n_fulltime * (fulltime_hours + x1) - d3f_plus + d3f_minus == n_fulltime * fulltime_hours,
        name="goal_ft_employment"
    )

    # p3b: part-time total working hours = n_parttime * parttime_hours
    model.addConstr(
        n_parttime * (parttime_hours + x2) - d3p_plus + d3p_minus == n_parttime * parttime_hours,
        name="goal_pt_employment"
    )

    # p4: overtime hours auxiliary constraints
    # d4f represents total full-time overtime = n_fulltime * x1
    model.addConstr(d4f == n_fulltime * x1, name="def_d4f")
    # d4p represents total part-time overtime = n_parttime * x2
    model.addConstr(d4p == n_parttime * x2, name="def_d4p")

    # Preemptive goal programming using weighted sum with large penalty weights
    # Priority levels: p1 >> p2 >> p3 >> p4
    # Weights chosen as powers of M (big-M approach for preemptive ordering)
    M = 1e6

    # p1: minimize underachievement of sales target (d1_minus)
    # p2: minimize overachievement of fulltime overtime (d2_plus)
    # p3: minimize underemployment, full-time weighted double (2*d3f_minus + d3p_minus)
    #     (fully employed means no under-hours; since overtime is positive, d3f_minus=0 always,
    #      but we also don't want over-staffing shortfall - interpret as: minimize deviations from standard)
    # p4: minimize total overtime (d4f + d4p)

    obj = (M**3 * d1_minus +
           M**2 * d2_plus +
           M**1 * (2.0 * d3f_minus + d3p_minus) +
           1.0  * (d4f + d4p))

    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 280.0 (optimal) | 280.0 (optimal) | 172.0 (optimal) |
| 1 | 333.41345268242657 (optimal) | 333.4134526824266 (optimal) | 279.6322165378031 (optimal) |
| 2 | 5465.102969981426 (optimal) | 5465.102969981425 (optimal) | 4991.00220508843 (optimal) |
| 3 | 913.3978762946681 (optimal) | 913.3978762946681 (optimal) | 913.3978762946681 (optimal) |
| 4 | 0.0 (optimal) | 0.0 (optimal) | 0.0 (optimal) |
| 5 | 8780.503173624325 (optimal) | 8780.503173624325 (optimal) | 6605.742446117042 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 280.0 (optimal) | 280.0 (optimal) | 172.0 (optimal) |
| 1 | 333.41345268242657 (optimal) | 333.4134526824266 (optimal) | 279.6322165378031 (optimal) |
| 2 | 5465.102969981426 (optimal) | 5465.102969981425 (optimal) | 4991.00220508843 (optimal) |
| 3 | 913.3978762946681 (optimal) | 913.3978762946681 (optimal) | 913.3978762946681 (optimal) |
| 4 | 0.0 (optimal) | 0.0 (optimal) | 0.0 (optimal) |
| 5 | 8780.503173624325 (optimal) | none (crash:raise ValueError( \| ValueError: Invalid parameter value: profit_per_pair[None] = '-0.340416046152745', value type=<class 'float'>. \| Value not in parameter domain NonNegativeReals) | 6605.742446117042 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "fulltime_salary", "evidence": "Table 3.3 lists Salary 1 (CNY/hour)"}, {"parameter": "parttime_salary", "evidence": "Table 3.3 lists Salary 0.6 (CNY/hour)"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 17. mamo_complex_45 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_45` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 45) |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 2430.0 |
| Label (original benchmark) | 2400 |
| Rules that certify it | gate 2430.0, panel_base_2of3 2430.0, ind_gate 2430.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
The China Railroad Ministry is in the process of planning relocations of freight cars among 5 regions of the country to get ready for the fall harvest. location 1 to 3 costs 11 units. Moving a car from location 1 to 4 costs 13 units. Moving a car from location 1 to 5 costs 28 units. Moving a car from location 2 to 3 costs 18 units. Moving a car from location 2 to 4 costs 8 units. Moving a car from location 2 to 5 costs 46 units. Moving a car from location 3 to 4 costs 9 units. Moving a car from location 3 to 5 costs 27 units. Moving a car from location 4 to 5 costs 20 units. At location 1, there are currently 120 cars present, but 150 cars are needed. At location 2, there are currently 330 cars present, but 200 cars are needed. At location 3, there are currently 400 cars present, but 600 cars are needed. At location 4, there are currently 400 cars present, but 200 cars are needed. At location 5, there are currently 600 cars present, but 400 cars are needed. Write down a linear optimization to compute the least costly way to move the cars such us the need is met.Provide your answer rounded to the nearest dollar.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cost_1_3": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"cost_1_4": {"base":13,"perturb":{"mode":"rel","r":0.5}}
"cost_1_5": {"base":28,"perturb":{"mode":"rel","r":0.5}}
"cost_2_3": {"base":18,"perturb":{"mode":"rel","r":0.5}}
"cost_2_4": {"base":8,"perturb":{"mode":"rel","r":0.5}}
"cost_2_5": {"base":46,"perturb":{"mode":"rel","r":0.5}}
"cost_3_4": {"base":9,"perturb":{"mode":"rel","r":0.5}}
"cost_3_5": {"base":27,"perturb":{"mode":"rel","r":0.5}}
"cost_4_5": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"supply_1": {"base":120,"perturb":{"mode":"rel","r":0.25}}
"supply_2": {"base":330,"perturb":{"mode":"rel","r":0.25}}
"supply_3": {"base":400,"perturb":{"mode":"rel","r":0.25}}
"supply_4": {"base":400,"perturb":{"mode":"rel","r":0.25}}
"supply_5": {"base":600,"perturb":{"mode":"rel","r":0.25}}
"demand_1": {"base":150,"perturb":{"mode":"rel","r":0.25}}
"demand_2": {"base":200,"perturb":{"mode":"rel","r":0.25}}
"demand_3": {"base":600,"perturb":{"mode":"rel","r":0.25}}
"demand_4": {"base":200,"perturb":{"mode":"rel","r":0.25}}
"demand_5": {"base":400,"perturb":{"mode":"rel","r":0.25}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = [1, 2, 3, 4, 5]
    arcs = [(1, 2), (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5),
            (3, 4), (3, 5), (4, 5)]

    cost = {
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 5): params["cost_4_5"],
    }
    supply = {i: params[f"supply_{i}"] for i in locations}
    demand = {i: params[f"demand_{i}"] for i in locations}

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.cost_obj = pyo.Objective(
        expr=sum(cost[a] * model.flow[a] for a in arcs),
        sense=pyo.minimize,
    )

    model.flow_con = pyo.ConstraintList()
    for loc in locations:
        outflow = sum(model.flow[a] for a in arcs if a[0] == loc)
        inflow = sum(model.flow[a] for a in arcs if a[1] == loc)
        # Cars at loc + inflow - outflow = final need (demand)
        model.flow_con.add(supply[loc] + inflow - outflow == demand[loc])

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"regions":[1,2,3,4,5],"links":[[1,3],[1,4],[1,5],[2,3],[2,4],[2,5],[3,4],[3,5],[4,5]],"arcs":"both directions of every link"},"params":{"cost":"cost_i_j for each listed link; equal in both directions","supply":"supply_1,...,supply_5","demand":"demand_1,...,demand_5"},"variables":{"flow[i,j]":"nonnegative continuous for every arc"},"constraints":["For each region r: supply[r] + sum(flow[i,r]) - sum(flow[r,j]) >= demand[r]."],"objective":"Minimize sum(cost[i,j] * flow[i,j]) over all arcs.","assumptions":["Each listed connection permits movement in either direction at the listed unit cost.","Surplus cars may remain in their regions."],"reporting":"Return the optimal objective rounded to the nearest dollar."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    regions = (1, 2, 3, 4, 5)

    link_costs = {
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 5): params["cost_4_5"],
    }
    supply = {
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: params["supply_4"],
        5: params["supply_5"],
    }
    demand = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }

    arc_costs = {}
    for (origin, destination), unit_cost in link_costs.items():
        arc_costs[origin, destination] = unit_cost
        arc_costs[destination, origin] = unit_cost

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=regions, ordered=True)
    model.arcs = pyo.Set(
        dimen=2, initialize=tuple(arc_costs), ordered=True
    )

    model.move_cost = pyo.Param(model.arcs, initialize=arc_costs)
    model.initial_supply = pyo.Param(model.regions, initialize=supply)
    model.required_cars = pyo.Param(model.regions, initialize=demand)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def meet_demand_rule(instance, region):
        incoming = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if destination == region
        )
        outgoing = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if origin == region
        )
        return (
            instance.initial_supply[region] + incoming - outgoing
            >= instance.required_cars[region]
        )

    model.meet_demand = pyo.Constraint(
        model.regions, rule=meet_demand_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.move_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    nodes = [1, 2, 3, 4, 5]

    # Undirected movement pairs; cost per car is the same either way
    edge_pairs = [(1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5),
                  (3, 4), (3, 5), (4, 5)]

    def unit_cost(i, j):
        a, b = min(i, j), max(i, j)
        return params["cost_%d_%d" % (a, b)]

    supply = {i: params["supply_%d" % i] for i in nodes}
    demand = {i: params["demand_%d" % i] for i in nodes}

    model = gp.Model("railcar_relocation")
    model.Params.OutputFlag = 0

    # Flow variables for each directed traversal of each undirected pair
    flow = {}
    for (i, j) in edge_pairs:
        flow[(i, j)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                     obj=unit_cost(i, j), name="f_%d_%d" % (i, j))
        flow[(j, i)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                     obj=unit_cost(i, j), name="f_%d_%d" % (j, i))

    model.ModelSense = GRB.MINIMIZE

    # Net inflow at each node must cover its deficit (surplus cars may stay put)
    for n in nodes:
        inflow = 0.0
        outflow = 0.0
        for (i, j) in edge_pairs:
            if j == n:
                inflow += flow[(i, j)]
            if i == n:
                outflow += flow[(j, i)] if False else 0.0
        # recompute explicitly over directed flows
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edge_pairs if j == n) + \
                 gp.quicksum(flow[(j, i)] for (i, j) in edge_pairs if i == n and (j, i) in flow)
        # simpler: iterate all directed arcs
        inflow = gp.quicksum(v for (a, b), v in flow.items() if b == n)
        outflow = gp.quicksum(v for (a, b), v in flow.items() if a == n)
        model.addConstr(inflow - outflow >= demand[n] - supply[n],
                        name="balance_%d" % n)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "not_solved"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 2430.0 (optimal) | 2430.0 (optimal) |
| 1 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 1984.0 (optimal) | 1984.0 (optimal) |
| 2 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 1746.0 (optimal) | 1746.0 (optimal) |
| 3 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 2585.0 (optimal) | 2585.0 (optimal) |
| 4 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 4747.0 (optimal) | 4747.0 (optimal) |
| 5 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 3660.0 (optimal) | 3660.0 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 2430.0 (optimal) | 2430.0 (optimal) |
| 1 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 1984.0 (optimal) | 1984.0 (optimal) |
| 2 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 1746.0 (optimal) | 1746.0 (optimal) |
| 3 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 2585.0 (optimal) | 2585.0 (optimal) |
| 4 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 4747.0 (optimal) | 4747.0 (optimal) |
| 5 | none (crash:expr=sum(cost[a] * model.flow[a] for a in arcs), \| ~~~~^^^ \| KeyError: (1, 2)) | 3660.0 (optimal) | 3660.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 18. mamo_complex_64 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_64` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 64) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 212.0 |
| Label (original benchmark) | 199 |
| Rules that certify it | gate 212.0, panel_base_2of3 212.0, ind_gate 212.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 199.0 |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Consider a scenario where a delivery company needs to deliver packages to five different cities. These cities are labeled as E, F, G, H and I. The delivery van can start its route from any of these cities but must follow one rule: it must visit each city exactly once and then return to the starting city. The aim is to find the route that minimizes the total travel cost, which could be a function of fuel costs, labor costs, or road tolls.

Here's a rundown of the travel costs between these cities:

From City E (1), the cost to reach City F (2) is 35 units, to G (3) is 90 units, to H (4) is 23 units, and to I (5) is 62 units.

From City F (2), the cost to City E (1) is 35 units, to G (3) is 53 units, to H (4) is 58 units, and to I (5) is 46 units.

If we start from City G (3), the cost to reach City E (1) is 90 units, to F (2) is 53 units, to H (4) is 28 units, and to I (5) is 91 units.

From City H (4), the cost to City E (1) is 23 units, to F (2) is 58 units, to G (3) is 28 units, and to I (5) is 77 units.

Lastly, from City I (5), it costs 62 units to reach City E (1), 46 units to get to F (2), 91 units to reach G (3), and 77 units to reach H (4).

What is the minimum total travel cost for the delivery van to visit each city exactly once and return to the starting city?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cost_E_to_F": {"base":35,"perturb":{"mode":"rel","r":0.5}}
"cost_E_to_G": {"base":90,"perturb":{"mode":"rel","r":0.5}}
"cost_E_to_H": {"base":23,"perturb":{"mode":"rel","r":0.5}}
"cost_E_to_I": {"base":62,"perturb":{"mode":"rel","r":0.5}}
"cost_F_to_G": {"base":53,"perturb":{"mode":"rel","r":0.5}}
"cost_F_to_H": {"base":58,"perturb":{"mode":"rel","r":0.5}}
"cost_F_to_I": {"base":46,"perturb":{"mode":"rel","r":0.5}}
"cost_G_to_H": {"base":28,"perturb":{"mode":"rel","r":0.5}}
"cost_G_to_I": {"base":91,"perturb":{"mode":"rel","r":0.5}}
"cost_H_to_I": {"base":77,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    pairs = [
        ('E', 'F', 'cost_E_to_F'),
        ('E', 'G', 'cost_E_to_G'),
        ('E', 'H', 'cost_E_to_H'),
        ('E', 'I', 'cost_E_to_I'),
        ('F', 'G', 'cost_F_to_G'),
        ('F', 'H', 'cost_F_to_H'),
        ('F', 'I', 'cost_F_to_I'),
        ('G', 'H', 'cost_G_to_H'),
        ('G', 'I', 'cost_G_to_I'),
        ('H', 'I', 'cost_H_to_I'),
    ]

    cost = {}
    for a, b, key in pairs:
        val = params[key]
        cost[(a, b)] = val
        cost[(b, a)] = val

    arcs = [(a, b) for a in cities for b in cities if a != b]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(a, b)] * m.x[a, b] for (a, b) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_cons = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ)
    model.order = pyo.Var(cities, bounds=(0, len(cities) - 1))
    non_root = cities[1:]
    root = cities[0]

    def mtz_rule(m, i, j):
        if i == root or j == root:
            return pyo.Constraint.Skip
        return m.order[i] - m.order[j] + len(cities) * m.x[i, j] <= len(cities) - 1
    model.mtz = pyo.Constraint(non_root, non_root, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}
```

#### B-structured.py

```python
# IR: {"sets":{"V":["E","F","G","H","I"],"A":"unordered pairs of distinct cities in V","S":"subsets of V with 2 <= cardinality <= 4"},"params":{"cost_E_to_F":"cost of {E,F}","cost_E_to_G":"cost of {E,G}","cost_E_to_H":"cost of {E,H}","cost_E_to_I":"cost of {E,I}","cost_F_to_G":"cost of {F,G}","cost_F_to_H":"cost of {F,H}","cost_F_to_I":"cost of {F,I}","cost_G_to_H":"cost of {G,H}","cost_G_to_I":"cost of {G,I}","cost_H_to_I":"cost of {H,I}"},"variables":{"x[a]":"Binary for each a in A; 1 if the route uses edge a"},"constraints":["For each v in V: sum(x[a] for a incident to v) = 2","For each T in S: sum(x[a] for a contained in T) <= cardinality(T)-1"],"objective":"Minimize sum(cost[a]*x[a] for a in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("E", "F", "G", "H", "I")
    edges = tuple(combinations(cities, 2))
    subsets = tuple(
        frozenset(subset)
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    )

    edge_costs = {
        ("E", "F"): params["cost_E_to_F"],
        ("E", "G"): params["cost_E_to_G"],
        ("E", "H"): params["cost_E_to_H"],
        ("E", "I"): params["cost_E_to_I"],
        ("F", "G"): params["cost_F_to_G"],
        ("F", "H"): params["cost_F_to_H"],
        ("F", "I"): params["cost_F_to_I"],
        ("G", "H"): params["cost_G_to_H"],
        ("G", "I"): params["cost_G_to_I"],
        ("H", "I"): params["cost_H_to_I"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.subtour_keys = pyo.Set(
        initialize=range(len(subsets)), ordered=True
    )

    model.edge_cost = pyo.Param(
        model.edges, initialize=edge_costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(instance, city):
        return sum(
            instance.x[left, right]
            for left, right in edges
            if left == city or right == city
        ) == 2

    model.degree_constraints = pyo.Constraint(
        model.cities, rule=degree_rule
    )

    def subtour_rule(instance, subset_key):
        subset = subsets[subset_key]
        return sum(
            instance.x[left, right]
            for left, right in edges
            if left in subset and right in subset
        ) <= len(subset) - 1

    model.subtour_constraints = pyo.Constraint(
        model.subtour_keys, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.edge_cost[left, right] * model.x[left, right]
            for left, right in edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    cities = [0, 1, 2, 3, 4]  # E=0, F=1, G=2, H=3, I=4
    n = len(cities)

    # Build symmetric cost matrix from params
    cost = {}
    cost[(0,1)] = cost[(1,0)] = params["cost_E_to_F"]
    cost[(0,2)] = cost[(2,0)] = params["cost_E_to_G"]
    cost[(0,3)] = cost[(3,0)] = params["cost_E_to_H"]
    cost[(0,4)] = cost[(4,0)] = params["cost_E_to_I"]
    cost[(1,2)] = cost[(2,1)] = params["cost_F_to_G"]
    cost[(1,3)] = cost[(3,1)] = params["cost_F_to_H"]
    cost[(1,4)] = cost[(4,1)] = params["cost_F_to_I"]
    cost[(2,3)] = cost[(3,2)] = params["cost_G_to_H"]
    cost[(2,4)] = cost[(4,2)] = params["cost_G_to_I"]
    cost[(3,4)] = cost[(4,3)] = params["cost_H_to_I"]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # Subtour elimination via MTZ
    u = model.addVars(cities, lb=0, ub=n - 1, vtype=GRB.INTEGER, name="u")

    for i in cities[1:]:
        for j in cities[1:]:
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 212.0 (optimal) | 212.0 (optimal) |
| 1 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 207.48065127230066 (optimal) | 207.48065127230066 (optimal) |
| 2 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 180.0218446100133 (optimal) | 180.0218446100133 (optimal) |
| 3 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 181.17215104202748 (optimal) | 181.17215104202745 (optimal) |
| 4 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 254.19991308405847 (optimal) | 254.1999130840585 (optimal) |
| 5 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 145.8420155001986 (optimal) | 145.8420155001986 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 212.0 (optimal) | 212.0 (optimal) |
| 1 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 207.48065127230066 (optimal) | 207.48065127230066 (optimal) |
| 2 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 180.0218446100133 (optimal) | 180.0218446100133 (optimal) |
| 3 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 181.17215104202748 (optimal) | 181.17215104202745 (optimal) |
| 4 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 254.19991308405847 (optimal) | 254.1999130840585 (optimal) |
| 5 | none (crash:File "<PATH>/indexed_component.py", line 903, in _validate_index \| raise KeyError( \| KeyError: "Index '('F', 'F')' is not valid for indexed) | 145.8420155001986 (optimal) | 145.8420155001986 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 19. mamo_complex_71 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_71` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 71) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 121.0 |
| Label (original benchmark) | 60 |
| Rules that certify it | gate 121.0, panel_base_2of3 121.0, ind_gate 121.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
In a scenario involving a sales representative tasked with visiting four distinct cities to promote their product, we identify these cities as A, B, C, and D. The representative has the flexibility to commence their travels from any city but is required to make a stop at each city exactly once before returning to their starting point. The primary objective for the sales representative is to minimize their overall travel expenses, which might encompass aspects like distance, time, or monetary costs.

Here’s a breakdown of the travel costs between each city:
- From City A, the cost is 19 units to City B, 45 units to City C, and 30 units to City D.
- Traveling from City B, it costs 19 units to reach City A, 89 units to City C, and 46 units to City D.
- From City C, the journey costs 45 units to City A, 89 units to City B, and merely 11 units to City D.
- Lastly, from City D, the travel expenses are 30 units to City A, 46 units to City B, and 11 units to City C.

Given this setup, what is the minimum total travel cost for the salesperson to visit each city exactly once and return to the starting city?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cost_AB": {"base":19,"perturb":{"mode":"rel","r":0.5}}
"cost_AC": {"base":45,"perturb":{"mode":"rel","r":0.5}}
"cost_AD": {"base":30,"perturb":{"mode":"rel","r":0.5}}
"cost_BA": {"base":19,"perturb":{"mode":"rel","r":0.5}}
"cost_BC": {"base":89,"perturb":{"mode":"rel","r":0.5}}
"cost_BD": {"base":46,"perturb":{"mode":"rel","r":0.5}}
"cost_CA": {"base":45,"perturb":{"mode":"rel","r":0.5}}
"cost_CB": {"base":89,"perturb":{"mode":"rel","r":0.5}}
"cost_CD": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"cost_DA": {"base":30,"perturb":{"mode":"rel","r":0.5}}
"cost_DB": {"base":46,"perturb":{"mode":"rel","r":0.5}}
"cost_DC": {"base":11,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ['A', 'B', 'C', 'D']

    cost = {
        ('A', 'B'): params["cost_AB"],
        ('A', 'C'): params["cost_AC"],
        ('A', 'D'): params["cost_AD"],
        ('B', 'A'): params["cost_BA"],
        ('B', 'C'): params["cost_BC"],
        ('B', 'D'): params["cost_BD"],
        ('C', 'A'): params["cost_CA"],
        ('C', 'B'): params["cost_CB"],
        ('C', 'D'): params["cost_CD"],
        ('D', 'A'): params["cost_DA"],
        ('D', 'B'): params["cost_DB"],
        ('D', 'C'): params["cost_DC"],
    }

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=list(cost.keys()), dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[i, j] * mdl.x[i, j] for (i, j) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if (i, j) in cost) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if (i, j) in cost) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)
    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # MTZ subtour elimination only over arcs leaving A's "successors" set,
    # i.e. exclude arcs into A since A is fixed as the depot with u=1.
    non_depot = ['B', 'C', 'D']
    model.u = pyo.Var(cities, bounds=(1, len(cities) - 1))
    model.u['A'].fix(1)

    def mtz_rule(mdl, i, j):
        return mdl.u[i] - mdl.u[j] + len(cities) * mdl.x[i, j] <= len(cities) - 1

    model.subtour = pyo.Constraint(
        [(i, j) for (i, j) in cost.keys() if j != 'A'], rule=mtz_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}
```

#### B-structured.py

```python
# IR: {"sets":{"cities":["A","B","C","D"],"arcs":"ordered pairs of distinct cities","subsets":"city subsets of sizes 2 and 3"},"params":{"cost_AB":"A->B cost","cost_AC":"A->C cost","cost_AD":"A->D cost","cost_BA":"B->A cost","cost_BC":"B->C cost","cost_BD":"B->D cost","cost_CA":"C->A cost","cost_CB":"C->B cost","cost_CD":"C->D cost","cost_DA":"D->A cost","cost_DB":"D->B cost","cost_DC":"D->C cost"},"variables":{"x[i,j]":{"type":"binary","index":"arcs"}},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for distinct i,j in S) <= |S|-1"],"objective":{"sense":"minimize","expression":"sum(cost_ij*x[i,j] for (i,j) in arcs)"}}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("A", "B", "C", "D")
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    subsets = tuple(
        subset
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    )

    costs = {
        ("A", "B"): params["cost_AB"],
        ("A", "C"): params["cost_AC"],
        ("A", "D"): params["cost_AD"],
        ("B", "A"): params["cost_BA"],
        ("B", "C"): params["cost_BC"],
        ("B", "D"): params["cost_BD"],
        ("C", "A"): params["cost_CA"],
        ("C", "B"): params["cost_CB"],
        ("C", "D"): params["cost_CD"],
        ("D", "A"): params["cost_DA"],
        ("D", "B"): params["cost_DB"],
        ("D", "C"): params["cost_DC"],
    }

    model = pyo.ConcreteModel()
    model.city_set = pyo.Set(initialize=cities, ordered=True)
    model.arc_set = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.subtour_set = pyo.Set(initialize=range(len(subsets)), ordered=True)

    model.travel_cost = pyo.Param(
        model.arc_set, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arc_set, domain=pyo.Binary)

    def departure_rule(current_model, origin):
        return sum(
            current_model.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    def arrival_rule(current_model, destination):
        return sum(
            current_model.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    def subtour_rule(current_model, subset_index):
        subset = subsets[subset_index]
        return sum(
            current_model.x[origin, destination]
            for origin in subset
            for destination in subset
            if origin != destination
        ) <= len(subset) - 1

    model.departure_constraints = pyo.Constraint(
        model.city_set, rule=departure_rule
    )
    model.arrival_constraints = pyo.Constraint(
        model.city_set, rule=arrival_rule
    )
    model.subtour_constraints = pyo.Constraint(
        model.subtour_set, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve can raise before a solution is loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['A', 'B', 'C', 'D']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    cost = {}
    for c1 in cities:
        for c2 in cities:
            if c1 != c2:
                key = f"cost_{c1}{c2}"
                cost[(c1, c2)] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary variable x[i,j] = 1 if travel from city i to city j
    x = {}
    for c1 in cities:
        for c2 in cities:
            if c1 != c2:
                x[(c1, c2)] = model.addVar(vtype=GRB.BINARY, name=f"x_{c1}{c2}")

    # MTZ subtour elimination variables
    u = {}
    for c in cities:
        u[c] = model.addVar(lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{c}")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(c1, c2)] * x[(c1, c2)] for c1 in cities for c2 in cities if c1 != c2),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for c1 in cities:
        model.addConstr(
            gp.quicksum(x[(c1, c2)] for c2 in cities if c1 != c2) == 1,
            name=f"depart_{c1}"
        )

    # Each city is arrived at exactly once
    for c2 in cities:
        model.addConstr(
            gp.quicksum(x[(c1, c2)] for c1 in cities if c1 != c2) == 1,
            name=f"arrive_{c2}"
        )

    # MTZ subtour elimination constraints
    # Fix starting city to have u = 0 to break symmetry (optional but helps)
    # For all i != j (both not the first city), u[i] - u[j] + n*x[i,j] <= n-1
    start = 'A'
    for c1 in cities:
        for c2 in cities:
            if c1 != c2 and c2 != start:
                model.addConstr(
                    u[c1] - u[c2] + n * x[(c1, c2)] <= n - 1,
                    name=f"mtz_{c1}_{c2}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 121.0 (optimal) | 121.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 80.56497486735137 (optimal) | 80.56497486735138 (optimal) |
| 2 | none (infeasible_or_unbounded) | 104.31711794234882 (optimal) | 104.31711794234882 (optimal) |
| 3 | none (infeasible_or_unbounded) | 100.79545604748999 (optimal) | 100.79545604748999 (optimal) |
| 4 | none (infeasible_or_unbounded) | 91.67974230749799 (optimal) | 91.67974230749799 (optimal) |
| 5 | none (infeasible_or_unbounded) | 90.29712148153983 (optimal) | 90.29712148153983 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 121.0 (optimal) | 121.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 80.56497486735137 (optimal) | 80.56497486735138 (optimal) |
| 2 | none (infeasible_or_unbounded) | 104.31711794234882 (optimal) | 104.31711794234882 (optimal) |
| 3 | none (infeasible_or_unbounded) | 100.79545604748999 (optimal) | 100.79545604748999 (optimal) |
| 4 | none (infeasible_or_unbounded) | 91.67974230749799 (optimal) | 91.67974230749799 (optimal) |
| 5 | none (infeasible_or_unbounded) | 90.29712148153983 (optimal) | 90.29712148153983 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 20. mamo_complex_80 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_80` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 80) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 4425.0 |
| Label (original benchmark) | 5213 |
| Rules that certify it | gate 4425.0, panel_base_2of3 4425.0, ind_gate 4425.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
You are managing the supplies of seven warehouses located in different regions. Each warehouse starts with a certain amount of supplies but needs a specific amount to fulfill the demands. Your task is to devise a plan to move supplies from one warehouse to another to meet the demand, considering the movement costs.

Here are the current and required quantities of supplies in each warehouse:

- Warehouse 1 has 57 units but needs 499 units.
- Warehouse 2 has 180 units but needs 173 units.
- Warehouse 3 has 288 units but needs 293 units.
- Warehouse 4 has 255 units but needs 158 units.
- Warehouse 5 has 477 units but needs 15 units.
- Warehouse 6 has 222 units but needs 78 units.
- Warehouse 7 has 314 units but needs 278 units.

Movement of supplies between warehouses incurs transportation costs. The cost varies depending on which warehouses you are moving supplies between. Here's a list showing how much it costs to move supplies from one warehouse to another:

- Moving supplies from/to Warehouse 1: To Warehouse 2 costs 36, to Warehouse 3 costs 36, to Warehouse 4 costs 48, to Warehouse 5 costs 10, to Warehouse 6 costs 20, to Warehouse 7 costs 48.
- Moving supplies from/to Warehouse 2: To Warehouse 1 costs 28, to Warehouse 3 costs 16, to Warehouse 4 costs 18, to Warehouse 5 costs 36, to Warehouse 6 costs 42, to Warehouse 7 costs 12.
- Moving supplies from/to Warehouse 3: To Warehouse 1 costs 6, to Warehouse 2 costs 40, to Warehouse 4 costs 49, to Warehouse 5 costs 31, to Warehouse 6 costs 1, to Warehouse 7 costs 46.
- Moving supplies from/to Warehouse 4: To Warehouse 1 costs 14, to Warehouse 2 costs 22, to Warehouse 3 costs 4, to Warehouse 5 costs 9, to Warehouse 6 costs 12, to Warehouse 7 costs 1.
- Moving supplies from/to Warehouse 5: To Warehouse 1 costs 50, to Warehouse 2 costs 44, to Warehouse 3 costs 7, to Warehouse 4 costs 48, to Warehouse 6 costs 7, to Warehouse 7 costs 25.
- Moving supplies from/to Warehouse 6: To Warehouse 1 costs 26, to Warehouse 2 costs 9, to Warehouse 3 costs 33, to Warehouse 4 costs 38, to Warehouse 5 costs 8, to Warehouse 7 costs 30.
- Moving supplies from/to Warehouse 7: To Warehouse 1 costs 8, to Warehouse 2 costs 9, to Warehouse 3 costs 2, to Warehouse 4 costs 13, to Warehouse 5 costs 8, to Warehouse 6 costs 49.

Given the above scenario, your goal is to ensure that every warehouse has the supplies it needs at the lowest possible cost. What is the minimum cost needed to relocate the supplies and meet the demand in each warehouse?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"supplies": {"base":[57,180,288,255,477,222,314],"perturb":{"mode":"rel","r":0.3}}
"demands": {"base":[499,173,293,158,15,78,278],"perturb":{"mode":"rel","r":0.3}}
"transport_costs": {"base":[36,36,48,10,20,48,16,18,36,42,12,49,31,1,46,9,12,1,7,25,30],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    n = 7
    nodes = list(range(n))

    # transport_costs is row-major for i != j pairs only (directed, all ordered pairs)
    cost = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            cost[(i, j)] = transport_costs[idx]
            idx += 1

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j],
        dimen=2,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        rule=lambda m: sum(cost[(i, j)] * m.flow[i, j] for (i, j) in m.arcs),
        sense=pyo.minimize,
    )

    def balance_rule(m, k):
        inflow = sum(m.flow[i, k] for i in nodes if i != k)
        outflow = sum(m.flow[k, j] for j in nodes if j != k)
        return supplies[k] + inflow - outflow == demands[k]

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"W":"0,...,6","A":"ordered (i,j) with i != j","P":"(i,j) with i < j, row-major"},"params":{"supplies":"params['supplies'][i]","demands":"params['demands'][i]","transport_costs":"params['transport_costs']: 21 scalars in P order apply to both directions; 21 two-entry sequences in P order specify [i->j,j->i]; alternatively 42 row-major off-diagonal scalars, a 7x7 matrix, or 7x6 off-diagonal rows"},"variables":{"shipment[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["supplies[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demands[i] for i in W"],"objective":"minimize sum(transport_costs[i,j] * shipment[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    warehouses = tuple(range(7))
    arcs = tuple(
        (origin, destination)
        for origin in warehouses
        for destination in warehouses
        if origin != destination
    )
    pairs = tuple(
        (origin, destination)
        for origin in warehouses
        for destination in warehouses
        if origin < destination
    )

    if len(supplies) != len(warehouses):
        return {"objective": None, "status": "invalid_supplies"}
    if len(demands) != len(warehouses):
        return {"objective": None, "status": "invalid_demands"}

    directed_costs = {}

    if len(transport_costs) == len(pairs):
        for position, (origin, destination) in enumerate(pairs):
            entry = transport_costs[position]
            if hasattr(entry, "__len__") and not isinstance(entry, (str, bytes)):
                if len(entry) != 2:
                    return {"objective": None, "status": "invalid_cost_pair"}
                directed_costs[origin, destination] = entry[0]
                directed_costs[destination, origin] = entry[1]
            else:
                # A scalar upper-triangle entry supplies both directions.
                directed_costs[origin, destination] = entry
                directed_costs[destination, origin] = entry

    elif len(transport_costs) == len(arcs):
        directed_costs = dict(zip(arcs, transport_costs))

    elif len(transport_costs) == len(warehouses):
        if any(
            not hasattr(row, "__len__") or isinstance(row, (str, bytes))
            for row in transport_costs
        ):
            return {"objective": None, "status": "invalid_cost_rows"}

        row_lengths = tuple(len(row) for row in transport_costs)

        if all(length == len(warehouses) for length in row_lengths):
            directed_costs = {
                (origin, destination): transport_costs[origin][destination]
                for origin, destination in arcs
            }
        elif all(length == len(warehouses) - 1 for length in row_lengths):
            for origin in warehouses:
                destinations = tuple(
                    destination
                    for destination in warehouses
                    if destination != origin
                )
                for position, destination in enumerate(destinations):
                    directed_costs[origin, destination] = (
                        transport_costs[origin][position]
                    )
        else:
            return {"objective": None, "status": "invalid_cost_rows"}

    else:
        return {"objective": None, "status": "invalid_cost_dimensions"}

    model = pyo.ConcreteModel()
    model.warehouses = pyo.Set(initialize=warehouses, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.initial_supply = pyo.Param(
        model.warehouses,
        initialize={
            warehouse: supplies[warehouse] for warehouse in warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.warehouses,
        initialize={
            warehouse: demands[warehouse] for warehouse in warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize=directed_costs,
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(instance, warehouse):
        incoming = sum(
            instance.shipment[other, warehouse]
            for other in instance.warehouses
            if other != warehouse
        )
        outgoing = sum(
            instance.shipment[warehouse, other]
            for other in instance.warehouses
            if other != warehouse
        )
        return (
            instance.initial_supply[warehouse] + incoming - outgoing
            >= instance.required_demand[warehouse]
        )

    model.demand_balance = pyo.Constraint(
        model.warehouses,
        rule=demand_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    n = len(supplies)

    # transport_costs is row-major for i<j pairs (n*(n-1)/2 entries)
    # but costs are directed/asymmetric per problem description.
    # We build a symmetric cost matrix from the i<j entries.
    cost = {}
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            c = transport_costs[idx]
            cost[i, j] = c
            cost[j, i] = c
            idx += 1

    model = gp.Model("warehouse_rebalancing")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    for i in range(n):
        inflow = gp.quicksum(x[j, i] for j in range(n) if j != i)
        outflow = gp.quicksum(x[i, j] for j in range(n) if j != i)
        model.addConstr(supplies[i] + inflow - outflow >= demands[i], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 4425.0 (optimal) | 4425.0 (optimal) |
| 1 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 4048.4274441275065 (optimal) | 4048.4274441275065 (optimal) |
| 2 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 2804.192027631533 (optimal) | 2804.192027631533 (optimal) |
| 3 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 4437.520531826517 (optimal) | 4437.520531826517 (optimal) |
| 4 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 5744.672221323383 (optimal) | 5744.6722213233825 (optimal) |
| 5 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 5854.967677081605 (optimal) | 5854.967677081605 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 4425.0 (optimal) | 4425.0 (optimal) |
| 1 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 4048.4274441275065 (optimal) | 4048.4274441275065 (optimal) |
| 2 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 2804.192027631533 (optimal) | 2804.192027631533 (optimal) |
| 3 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 4437.520531826517 (optimal) | 4437.520531826517 (optimal) |
| 4 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 5744.672221323383 (optimal) | 5744.6722213233825 (optimal) |
| 5 | none (crash:cost[(i, j)] = transport_costs[idx] \| ~~~~~~~~~~~~~~~^^^^^ \| IndexError: list index out of range) | 5854.967677081605 (optimal) | 5854.967677081605 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{
  "mismatch": [],
  "not_stated": [
    {
      "parameter": "transport_costs",
      "evidence": "Cost list is given as directed pairs (e.g., 'to Warehouse 2 costs 36'), not as a condensed row-major upper-triangular sequence; the extracted vector does not match the stated set of directed costs."
    }
  ]
}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

````json
I need to check the `transport_costs` parameter carefully. The statement gives a 7×7 cost matrix (excluding diagonal), and the extracted value appears to be a flattened upper-triangle (i=1..6, j=i+1..7), but the statement's cost matrix is not symmetric, so a single triangle cannot represent it. Let me also verify the actual numbers.

Upper-triangle pairs and their costs from the statement:
- (1,2)=36, (1,3)=36, (1,4)=48, (1,5)=10, (1,6)=20, (1,7)=48
- (2,3)=16, (2,4)=18, (2,5)=36, (2,6)=42, (2,7)=12
- (3,4)=49, (3,5)=31, (3,6)=1, (3,7)=46
- (4,5)=9, (4,6)=12, (4,7)=1
- (5,6)=7, (5,7)=25
- (6,7)=30

That gives 21 values: [36,36,48,10,20,48, 16,18,36,42,12, 49,31,1,46, 9,12,1, 7,25, 30].

The extracted value is [36,36,48,10,20,48,16,18,36,42,12,49,31,1,46,9,12,1,7,25,30], which matches exactly.

However, the statement's costs are explicitly asymmetric (e.g., cost from 1→2 is 36 but 2→1 is 28; 1→3 is 36 but 3→1 is 6). The extracted parameter discards the lower-triangle values entirely, meaning costs for moves where i>j are not_stated in the extraction.

The `supplies` and `demands` values match the statement exactly.

```json
{
  "mismatch": [],
  "not_stated": [
    {
      "parameter": "transport_costs",
      "evidence": "The statement gives asymmetric directed costs (e.g., Warehouse 2 to Warehouse 1 costs 28, Warehouse 3 to Warehouse 1 costs 6, Warehouse 4 to Warehouse 1 costs 14, etc.), but the extracted value contains only the 21 upper-triangle entries and omits all costs for pairs where i > j."
    }
  ]
}
```
````


## 21. mamo_complex_94 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_94` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 94) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 22.333333333333332 |
| Label (original benchmark) | 23 |
| Rules that certify it | gate 22.333333333333332, panel_base_2of3 22.333333333333332, ind_gate 22.333333333333332 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A post office requires different numbers of full-time employees on different days of the week. The number of full-time employees required on each day is given in Table 4. Monday requires 17 employees,Tuesday requires13, Wednesday requires 15, Thursday requires 19, Friday requires 14, Saturday requires 16,  Sunday requires 11. Union rules state that each full-time employee must work five consecutive days and then receive two days off. For example, an employee who works Monday to Friday must be off on Saturday and Sunday. The post office wants to meet its daily requirements using only fulltime employees. Formulate an LP that the post office can use to minimize the number of full-time employees who must be hired. Find the minimal number.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"requirements": {"base":[17,13,15,19,14,16,11],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    requirements = params["requirements"]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    model = pyo.ConcreteModel()

    # x[j] = number of employees whose two-day-off pair starts such that they
    # work 5 consecutive days beginning on day j (i.e., off days are j+5, j+6)
    model.x = pyo.Var(range(7), domain=pyo.NonNegativeReals)

    # Each shift pattern indexed by start day j covers days j, j+1, ..., j+4 (mod 7)
    def coverage_rule(model, d):
        # sum over shifts that work on day d
        return sum(model.x[j] for j in range(7) if (d - j) % 7 < 5) >= requirements[d]

    model.coverage = pyo.Constraint(range(7), rule=coverage_rule)

    model.obj = pyo.Objective(expr=sum(model.x[j] for j in range(7)), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"days":"0..6 (Mon..Sun)","work_offsets":"0..4"},"params":{"requirements":"params['requirements'], seven daily staffing requirements in Mon..Sun order"},"variables":{"starts[d]":"nonnegative integer; employees beginning a five-day work period on day d"},"constraints":["For each day d: sum(starts[(d-k)%7] for k in work_offsets) >= requirements[d]."],"objective":"Minimize sum(starts[d] for d in days)."}
# Integer variables ensure that the solution hires whole employees.
# This is the integer linear formulation of the staffing problem.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = params["requirements"]

    model = pyo.ConcreteModel()
    model.days = pyo.RangeSet(0, 6)
    model.work_offsets = pyo.RangeSet(0, 4)

    model.daily_requirements = pyo.Param(
        model.days,
        initialize={day: requirements[day] for day in range(7)},
        within=pyo.NonNegativeReals,
    )

    model.starts = pyo.Var(
        model.days,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, day):
        return (
            sum(
                instance.starts[(day - offset) % 7]
                for offset in instance.work_offsets
            )
            >= instance.daily_requirements[day]
        )

    model.daily_coverage = pyo.Constraint(
        model.days,
        rule=coverage_rule,
    )

    model.total_employees = pyo.Objective(
        expr=sum(model.starts[day] for day in model.days),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        # Fall through and determine success only by objective retrieval.

    try:
        obj_val = float(pyo.value(model.total_employees))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    requirements = params["requirements"]  # list of 7 values: Mon=0 ... Sun=6

    # Decision variables: x[i] = number of employees starting their 5-day shift on day i
    # Days: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    # Employee starting on day i works days i, i+1, i+2, i+3, i+4 (mod 7)

    model = gp.Model("post_office_scheduling")
    model.setParam("OutputFlag", 0)

    # x[i]: number of employees starting on day i (continuous relaxation gives integer here)
    x = model.addVars(7, lb=0, vtype=GRB.CONTINUOUS, name="x")

    # Minimize total employees hired
    model.setObjective(gp.quicksum(x[i] for i in range(7)), GRB.MINIMIZE)

    # Coverage constraints: for each day d, sum of x[i] where day d is in [i, i+1, ..., i+4] mod 7
    # Day d is covered by shift starting on day i if (d - i) mod 7 in {0,1,2,3,4}
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for d in range(7):
        covering = [i for i in range(7) if (d - i) % 7 <= 4]
        model.addConstr(
            gp.quicksum(x[i] for i in covering) >= requirements[d],
            name=f"coverage_{days[d]}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 22.333333333333332 (optimal) | 23.0 (optimal) | 22.333333333333332 (optimal) |
| 1 | 22.37782804879452 (optimal) | 23.0 (optimal) | 22.377828048794523 (optimal) |
| 2 | 15.800431122725728 (optimal) | 17.0 (optimal) | 15.800431122725726 (optimal) |
| 3 | 22.325441801711516 (optimal) | 23.0 (optimal) | 22.325441801711513 (optimal) |
| 4 | 27.687048371928846 (optimal) | 28.0 (optimal) | 27.687048371928846 (optimal) |
| 5 | 29.816361499291663 (optimal) | 31.0 (optimal) | 29.816361499291663 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 22.333333333333332 (optimal) | 23.0 (optimal) | 22.333333333333332 (optimal) |
| 1 | 22.37782804879452 (optimal) | 23.0 (optimal) | 22.377828048794523 (optimal) |
| 2 | 15.800431122725728 (optimal) | 17.0 (optimal) | 15.800431122725726 (optimal) |
| 3 | 22.325441801711516 (optimal) | 23.0 (optimal) | 22.325441801711513 (optimal) |
| 4 | 27.687048371928846 (optimal) | 28.0 (optimal) | 27.687048371928846 (optimal) |
| 5 | 29.816361499291663 (optimal) | 31.0 (optimal) | 29.816361499291663 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 22. mamo_complex_100 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_100` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 100) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 176.0 |
| Label (original benchmark) | 160 |
| Rules that certify it | gate 176.0, panel_base_2of3 176.0, ind_gate 176.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 160.0 |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine a salesperson tasked with visiting four distinct cities—let's call them A, B, C, and D—to promote their products. The salesperson can commence their journey from any of these cities, with the requirement that they visit each city exactly once before returning to the starting point. The primary objective is to minimize the total travel cost incurred during this journey.

Here's a breakdown of the travel costs between the cities:
- To travel from City A to B, it costs 61 units.
- To journey from City A to C, the cost is 65 units.
- The travel cost from City A to D is 63 units.
- If the salesperson begins from City B, it costs 61 units to reach A, 94 units to get to C, and 31 units to D.
- From City C, the costs are 65 units to A, 94 units to B, and 19 units to D.
- Finally, from City D, the costs are 63 units to A, 31 units to B, and 19 units to C.

Now, what is the minimum total travel cost for the salesperson to visit each city exactly once and return to the starting city?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cost_A_B": {"base":61,"perturb":{"mode":"abs","lo":20.0,"hi":120.0,"integer":true}}
"cost_A_C": {"base":65,"perturb":{"mode":"abs","lo":20.0,"hi":120.0,"integer":true}}
"cost_A_D": {"base":63,"perturb":{"mode":"abs","lo":20.0,"hi":120.0,"integer":true}}
"cost_B_A": {"base":61,"perturb":{"mode":"abs","lo":20.0,"hi":120.0,"integer":true}}
"cost_B_C": {"base":94,"perturb":{"mode":"abs","lo":20.0,"hi":150.0,"integer":true}}
"cost_B_D": {"base":31,"perturb":{"mode":"abs","lo":5.0,"hi":100.0,"integer":true}}
"cost_C_A": {"base":65,"perturb":{"mode":"abs","lo":20.0,"hi":120.0,"integer":true}}
"cost_C_B": {"base":94,"perturb":{"mode":"abs","lo":20.0,"hi":150.0,"integer":true}}
"cost_C_D": {"base":19,"perturb":{"mode":"abs","lo":5.0,"hi":100.0,"integer":true}}
"cost_D_A": {"base":63,"perturb":{"mode":"abs","lo":20.0,"hi":120.0,"integer":true}}
"cost_D_B": {"base":31,"perturb":{"mode":"abs","lo":5.0,"hi":100.0,"integer":true}}
"cost_D_C": {"base":19,"perturb":{"mode":"abs","lo":5.0,"hi":100.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = ['A', 'B', 'C', 'D']
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {
        ('A', 'B'): params["cost_A_B"],
        ('A', 'C'): params["cost_A_C"],
        ('A', 'D'): params["cost_A_D"],
        ('B', 'A'): params["cost_B_A"],
        ('B', 'C'): params["cost_B_C"],
        ('B', 'D'): params["cost_B_D"],
        ('C', 'A'): params["cost_C_A"],
        ('C', 'B'): params["cost_C_B"],
        ('C', 'D'): params["cost_C_D"],
        ('D', 'A'): params["cost_D_A"],
        ('D', 'B'): params["cost_D_B"],
        ('D', 'C'): params["cost_D_C"],
    }

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[a] * mdl.x[a] for a in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in cities if j != i) == 1
    model.out_cons = pyo.Constraint(cities, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in cities if i != j) == 1
    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}
```

#### B-structured.py

```python
# IR: {"sets":{"cities":["A","B","C","D"],"arcs":"ordered pairs of distinct cities","subsets":"city subsets of sizes 2 and 3"},"params":["cost_A_B","cost_A_C","cost_A_D","cost_B_A","cost_B_C","cost_B_D","cost_C_A","cost_C_B","cost_C_D","cost_D_A","cost_D_B","cost_D_C"],"variables":{"x[i,j]":"binary for each arc (i,j)"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for i,j in S with i != j) <= |S|-1"],"objective":"minimize sum(cost[i,j]*x[i,j] for all arcs)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("A", "B", "C", "D")
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    subsets = tuple(
        subset
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
    )
    costs = {
        ("A", "B"): params["cost_A_B"],
        ("A", "C"): params["cost_A_C"],
        ("A", "D"): params["cost_A_D"],
        ("B", "A"): params["cost_B_A"],
        ("B", "C"): params["cost_B_C"],
        ("B", "D"): params["cost_B_D"],
        ("C", "A"): params["cost_C_A"],
        ("C", "B"): params["cost_C_B"],
        ("C", "D"): params["cost_C_D"],
        ("D", "A"): params["cost_D_A"],
        ("D", "B"): params["cost_D_B"],
        ("D", "C"): params["cost_D_C"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(model, origin):
        return sum(
            model.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    def incoming_rule(model, destination):
        return sum(
            model.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_cuts = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_cuts.add(
            sum(
                model.x[origin, destination]
                for origin in subset
                for destination in subset
                if origin != destination
            ) <= len(subset) - 1
        )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['A', 'B', 'C', 'D']
    n = len(cities)

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # u[i] = position of city i in tour (MTZ subtour elimination), u in [1, n-1] for non-depot
    # Fix A as depot (position 0); u for B, C, D in [1, n-1]
    non_depot = ['B', 'C', 'D']
    u = model.addVars(non_depot, vtype=GRB.CONTINUOUS, name="u", lb=1, ub=n - 1)

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination constraints
    for i in non_depot:
        for j in non_depot:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[(i, j)] <= n - 2,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 160.0 (optimal) | 176.0 (optimal) | 176.0 (optimal) |
| 1 | 136.0 (optimal) | 136.0 (optimal) | 136.0 (optimal) |
| 2 | 199.0 (optimal) | 200.0 (optimal) | 200.0 (optimal) |
| 3 | 181.0 (optimal) | 181.0 (optimal) | 181.0 (optimal) |
| 4 | 149.0 (optimal) | 186.0 (optimal) | 186.0 (optimal) |
| 5 | 139.0 (optimal) | 139.0 (optimal) | 139.0 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 160.0 (optimal) | 176.0 (optimal) | 176.0 (optimal) |
| 1 | 136.0 (optimal) | 136.0 (optimal) | 136.0 (optimal) |
| 2 | 199.0 (optimal) | 200.0 (optimal) | 200.0 (optimal) |
| 3 | 181.0 (optimal) | 181.0 (optimal) | 181.0 (optimal) |
| 4 | 149.0 (optimal) | 186.0 (optimal) | 186.0 (optimal) |
| 5 | 139.0 (optimal) | 139.0 (optimal) | 139.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 23. mamo_complex_125 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_125` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 125) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 14256.0 |
| Label (original benchmark) | 8090 |
| Rules that certify it | gate 14256.0, panel_base_2of3 14256.0, ind_gate 14256.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine you are the director of a non-profit organization tasked with providing food supplies to six regions suffering from a famine. Each region has a certain amount of food already, but they require more to sustain their population through the hardship. 

Here are the current quantities of food (in tons) available and the required quantities for each region:

- Region 1 has 42 tons but needs 74 tons.
- Region 2 has 32 tons but needs 476 tons.
- Region 3 has 398 tons but only needs 2 tons.
- Region 4 has 224 tons but needs 235 tons.
- Region 5 has 210 tons but needs 221 tons.
- Region 6 has 209 tons but only needs 72 tons.

You have the ability to transfer food supplies from one region to another. However, the cost of transportation varies depending on which regions you are transferring food between. Below is a list detailing the cost of moving food from one region to any other:

- To move food from/to Region 1: To Region 2 costs 16, to Region 3 costs 48, to Region 4 costs 42, to Region 5 costs 50, to Region 6 costs 8.
- To move food from/to Region 2: To Region 1 costs 27, to Region 3 costs 23, to Region 4 costs 37, to Region 5 costs 39, to Region 6 costs 29.
- To move food from/to Region 3: To Region 1 costs 49, to Region 2 costs 39, to Region 4 costs 33, to Region 5 costs 50, to Region 6 costs 6.
- To move food from/to Region 4: To Region 1 costs 23, to Region 2 costs 49, to Region 3 costs 46, to Region 5 costs 50, to Region 6 costs 6.
- To move food from/to Region 5: To Region 1 costs 45, to Region 2 costs 47, to Region 3 costs 48, to Region 4 costs 26, to Region 6 costs 39.
- To move food from/to Region 6: To Region 1 costs 33, to Region 2 costs 11, to Region 3 costs 9, to Region 4 costs 4, to Region 5 costs 12.

Your mission is to ensure every region receives the food it needs while keeping the transportation cost as low as possible. What would be the minimum cost to make sure all regions have enough food?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"supply": {"base":[42,32,398,224,210,209],"perturb":{"mode":"rel","r":0.3}}
"demand": {"base":[74,476,2,235,221,72],"perturb":{"mode":"rel","r":0.3}}
"cost_1_2": {"base":16,"perturb":{"mode":"rel","r":0.5}}
"cost_1_3": {"base":48,"perturb":{"mode":"rel","r":0.5}}
"cost_1_4": {"base":42,"perturb":{"mode":"rel","r":0.5}}
"cost_1_5": {"base":50,"perturb":{"mode":"rel","r":0.5}}
"cost_1_6": {"base":8,"perturb":{"mode":"rel","r":0.5}}
"cost_2_1": {"base":27,"perturb":{"mode":"rel","r":0.5}}
"cost_2_3": {"base":23,"perturb":{"mode":"rel","r":0.5}}
"cost_2_4": {"base":37,"perturb":{"mode":"rel","r":0.5}}
"cost_2_5": {"base":39,"perturb":{"mode":"rel","r":0.5}}
"cost_2_6": {"base":29,"perturb":{"mode":"rel","r":0.5}}
"cost_3_1": {"base":49,"perturb":{"mode":"rel","r":0.5}}
"cost_3_2": {"base":39,"perturb":{"mode":"rel","r":0.5}}
"cost_3_4": {"base":33,"perturb":{"mode":"rel","r":0.5}}
"cost_3_5": {"base":50,"perturb":{"mode":"rel","r":0.5}}
"cost_3_6": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"cost_4_1": {"base":23,"perturb":{"mode":"rel","r":0.5}}
"cost_4_2": {"base":49,"perturb":{"mode":"rel","r":0.5}}
"cost_4_3": {"base":46,"perturb":{"mode":"rel","r":0.5}}
"cost_4_5": {"base":50,"perturb":{"mode":"rel","r":0.5}}
"cost_4_6": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"cost_5_1": {"base":45,"perturb":{"mode":"rel","r":0.5}}
"cost_5_2": {"base":47,"perturb":{"mode":"rel","r":0.5}}
"cost_5_3": {"base":48,"perturb":{"mode":"rel","r":0.5}}
"cost_5_4": {"base":26,"perturb":{"mode":"rel","r":0.5}}
"cost_5_6": {"base":39,"perturb":{"mode":"rel","r":0.5}}
"cost_6_1": {"base":33,"perturb":{"mode":"rel","r":0.5}}
"cost_6_2": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"cost_6_3": {"base":9,"perturb":{"mode":"rel","r":0.5}}
"cost_6_4": {"base":4,"perturb":{"mode":"rel","r":0.5}}
"cost_6_5": {"base":12,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    regions = [1, 2, 3, 4, 5, 6]

    supply = {i: params["supply"][i - 1] for i in regions}
    demand = {i: params["demand"][i - 1] for i in regions}

    cost = {}
    for i in regions:
        for j in regions:
            if i != j:
                cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=[(i, j) for i in regions for j in regions if i != j])

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.flow[(i, j)] for (i, j) in m.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, i):
        inflow = sum(m.flow[(j, i)] for j in regions if j != i)
        outflow = sum(m.flow[(i, j)] for j in regions if j != i)
        return supply[i] + inflow - outflow >= demand[i]

    model.balance = pyo.Constraint(regions, rule=balance_rule)

    def out_rule(m, i):
        return sum(m.flow[(i, j)] for j in regions if j != i) <= supply[i]

    model.outflow = pyo.Constraint(regions, rule=out_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"R":[1,2,3,4,5,6],"A":"{(i,j) in R x R: i != j}"},"params":{"supply":"R-indexed nonnegative stock from params['supply']","demand":"R-indexed nonnegative requirement from params['demand']","cost":"A-indexed transport cost from params['cost_i_j']"},"variables":{"flow[i,j]":"continuous nonnegative, (i,j) in A"},"constraints":["For each i in R: supply[i] + sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) >= demand[i]"],"objective":"Minimize sum(cost[i,j] * flow[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept regional data as six-element sequences or mappings keyed 1..6."""

    regions = range(1, 7)

    def regional_values(data):
        if isinstance(data, Mapping):
            return {
                region: data[region] if region in data else data[str(region)]
                for region in regions
            }
        if len(data) != len(regions):
            raise ValueError("Regional sequences must contain exactly six values.")
        return {region: data[region - 1] for region in regions}

    supply_values = regional_values(params["supply"])
    demand_values = regional_values(params["demand"])
    transport_costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin in regions
        for destination in regions
        if origin != destination
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=regions, ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=transport_costs.keys(),
        ordered=True,
    )

    model.stock = pyo.Param(
        model.regions,
        initialize=supply_values,
        within=pyo.NonNegativeReals,
    )
    model.requirement = pyo.Param(
        model.regions,
        initialize=demand_values,
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize=transport_costs,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def food_balance_rule(instance, region):
        incoming = sum(
            instance.flow[other, region]
            for other in instance.regions
            if other != region
        )
        outgoing = sum(
            instance.flow[region, other]
            for other in instance.regions
            if other != region
        )
        return (
            instance.stock[region] + incoming - outgoing
            >= instance.requirement[region]
        )

    model.food_balance = pyo.Constraint(
        model.regions,
        rule=food_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]

    # Build cost matrix: cost[i][j] for i != j (1-indexed, stored as 0-indexed)
    # Regions 1..6 -> indices 0..5
    n = 6
    cost = {}
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("food_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = tons shipped from region i to region j
    x = {}
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                x[(i, j)] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in range(1, n + 1) for j in range(1, n + 1) if i != j),
        GRB.MINIMIZE
    )

    # Supply constraints: food shipped out from region i <= supply[i-1] - (demand[i-1] - supply[i-1]) if surplus
    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in range(1, n + 1):
        inflow = gp.quicksum(x[(j, i)] for j in range(1, n + 1) if j != i)
        outflow = gp.quicksum(x[(i, j)] for j in range(1, n + 1) if j != i)
        # Net available after transfers must meet demand
        model.addConstr(
            supply[i - 1] + inflow - outflow >= demand[i - 1],
            name=f"demand_{i}"
        )
        # Cannot ship out more than available supply
        model.addConstr(
            outflow <= supply[i - 1],
            name=f"supply_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 14256.0 (optimal) | 8090.0 (optimal) | 14256.0 (optimal) |
| 1 | 12775.87159588398 (optimal) | 6474.045819197741 (optimal) | 12775.87159588398 (optimal) |
| 2 | 8316.275596992511 (optimal) | 5303.198019416863 (optimal) | 8316.275596992511 (optimal) |
| 3 | 19192.95615700242 (optimal) | 10649.694678781436 (optimal) | 19192.95615700242 (optimal) |
| 4 | 14561.794081229835 (optimal) | 6350.289001559615 (optimal) | 14561.794081229835 (optimal) |
| 5 | 9203.032776405991 (optimal) | 7234.103576965603 (optimal) | 9203.032776405991 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 3, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 14256.0 (optimal) | 8090.0 (optimal) | 14256.0 (optimal) |
| 1 | 7435.928829404974 (optimal) | 6509.631820397473 (optimal) | 7435.928829404975 (optimal) |
| 2 | none (infeasible_or_unbounded) | none (no_feasible_solution) | none (infeasible) |
| 3 | 15504.524135900332 (optimal) | 10688.801036340714 (optimal) | 15504.524135900334 (optimal) |
| 4 | none (infeasible_or_unbounded) | none (no_feasible_solution) | none (infeasible) |
| 5 | 8791.797389794714 (optimal) | 6306.320633105964 (optimal) | 8791.797389794714 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
I'll check each parameter against the statement.

**supply and demand**: Statement gives 42/74, 32/476, 398/2, 224/235, 210/221, 209/72. Extracted values match.

**cost parameters**: The statement says costs are "from/to" a region, meaning the costs listed appear to be symmetric (the same value applies in both directions between a pair). Let me check for asymmetries in the extracted values vs. what the statement says.

The statement lists, for Region 1: to R2=16, to R3=48, to R4=42, to R5=50, to R6=8.
For Region 2: to R1=27, to R3=23, to R4=37, to R5=39, to R6=29.

So the statement gives cost_1_2=16 and cost_2_1=27 — these differ, which is fine, both are stated explicitly.

Going through all pairs, checking extracted vs. stated:

- cost_1_2=16 ✓, cost_2_1=27 ✓
- cost_1_3=48 ✓, cost_3_1=49 ✓
- cost_1_4=42 ✓, cost_4_1=23 ✓
- cost_1_5=50 ✓, cost_5_1=45 ✓
- cost_1_6=8 ✓, cost_6_1=33 ✓
- cost_2_3=23 ✓, cost_3_2=39 ✓
- cost_2_4=37 ✓, cost_4_2=49 ✓
- cost_2_5=39 ✓, cost_5_2=47 ✓
- cost_2_6=29 ✓, cost_6_2=11 ✓
- cost_3_4=33 ✓, cost_4_3=46 ✓
- cost_3_5=50 ✓, cost_5_3=48 ✓
- cost_3_6=6 ✓, cost_6_3=9 ✓
- cost_4_5=50 ✓, cost_5_4=26 ✓
- cost_4_6=6 ✓, cost_6_4=4 ✓
- cost_5_6=39 ✓, cost_6_5=12 ✓

All values match exactly.

```json
{"mismatch": [], "not_stated": []}
```
````


## 24. mamo_complex_163 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_163` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 163) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 51.0 |
| Label (original benchmark) | 69 |
| Rules that certify it | gate 51.0, panel_base_2of3 51.0, ind_gate 51.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 69.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Welcome to the virtual challenge of constructing a futuristic energy distribution network spanning across 8 pivotal nodes, designed to optimize the flow of a newly discovered renewable energy source from its origin to a central processing facility. This network, conceptualized within a high-tech cityscape, involves complex routes and capacities that dictate the maximum energy flow possible between nodes, each representing energy substations or relay points.

Here’s a closer look at the energy flow capacities (in megawatts) between these substations:

- From Substation 0 (Source): Energy can be directed to Substation 1 (19 MW), Substation 2 (4 MW), Substation 3 (1 MW), Substation 4 (9 MW), Substation 5 (13 MW), Substation 6 (8 MW), and Substation 7 (20 MW).
- From Substation 1: Can relay energy to Substation 0 (10 MW), Substation 2 (12 MW), Substation 3 (12 MW), Substation 4 (8 MW), Substation 5 (12 MW), Substation 6 (7 MW), and Substation 7 (7 MW).
- From Substation 2: Can transfer energy to Substation 0 (13 MW), Substation 1 (11 MW), Substation 3 (8 MW), Substation 4 (4 MW), Substation 5 (1 MW), Substation 6 (2 MW), and Substation 7 (3 MW).
- From Substation 3: Can distribute energy to Substation 0 (4 MW), Substation 1 (12 MW), Substation 2 (13 MW), Substation 4 (18 MW), Substation 5 (6 MW), Substation 6 (19 MW), and Substation 7 (8 MW).
- From Substation 4: Can send energy to Substation 0 (9 MW), Substation 1 (16 MW), Substation 2 (2 MW), Substation 5 (14 MW), Substation 6 (18 MW), and Substation 7 (7 MW).
- From Substation 5: Can dispatch energy to Substation 0 (10 MW), Substation 1 (11 MW), Substation 2 (7 MW), Substation 3 (11 MW), Substation 4 (16 MW), Substation 6 (16 MW), and Substation 7 (5 MW).
- From Substation 6: Capable of forwarding energy to Substation 0 (14 MW), Substation 1 (11 MW), Substation 2 (9 MW), Substation 3 (11 MW), Substation 4 (3 MW), Substation 5 (17 MW), and Substation 7 (19 MW).
- From Substation 7 (Destination): Can receive energy and has the potential to send it back to Substation 0 (12 MW), Substation 1 (20 MW), Substation 2 (5 MW), Substation 3 (11 MW), Substation 4 (10 MW), Substation 5 (4 MW), and Substation 6 (6 MW).

In this setup, a capacity of "0" signifies the absence of a direct energy transfer link between the two respective substations.

The ultimate objective is to compute the maximum energy that can be transmitted from Substation 0 (the source) to Substation 7 (the destination) per time unit, with the condition that the energy flow through each link does not surpass its maximum capacity. What is the optimal value of energy (in megawatts) that can be efficiently relayed from the source to the destination per time unit?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacity": {"base":[0,19,4,1,9,13,8,20,10,0,12,12,8,12,7,7,13,11,0,8,4,1,2,3,4,12,13,0,18,6,19,8,9,16,2,0,0,14,18,7,10,11,7,11,16,0,16,5,14,11,9,11,3,17,0,19,12,20,5,11,10,4,6,0],"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 8
    source = 0
    sink = n - 1
    cap_flat = params["capacity"]

    # Build adjacency capacity dictionary from row-major flat list (omitting self-loops)
    cap = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            cap[(i, j)] = float(cap_flat[idx])
            idx += 1

    arcs = [(i, j) for (i, j) in cap if cap[(i, j)] > 0]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.obj = pyo.Objective(
        expr=sum(model.flow[i, j] for (i, j) in arcs if i == source)
        - sum(model.flow[j, i] for (j, i) in arcs if i == source),
        sense=pyo.maximize,
    )

    def flow_rule(model, v):
        inflow = sum(model.flow[i, v] for (i, v) in arcs if v > 0 or True if (i, v) in model.arcs)
        outflow = sum(model.flow[v, j] for (v, j) in arcs if (v, j) in model.arcs)
        return inflow - outflow == 0

    # Define flow balance explicitly, replacing generic node index set
    balance_nodes = [v for v in range(n) if v not in (source, sink)]

    model.balance = pyo.Constraint(
        balance_nodes,
        rule=lambda m, v: sum(m.flow[i, v] for (i, v) in arcs if i == v or (i, v) in m.arcs and i == v or False)
        if False else sum(m.flow[i, v] for (i, v) in arcs if (i, v) in m.arcs and i != v)
        - sum(m.flow[v, j] for (v, j) in arcs if (v, j) in m.arcs and j != v) == 0,
    )

    # Simplify: redefine cleanly without duplicating constraint
    model.del_component(model.balance)
    model.balance = pyo.Constraint(
        balance_nodes,
        rule=lambda m, v: sum(m.flow[i, v] for (i, j) in arcs if j == v and (i, v) in m.arcs)
        - sum(m.flow[v, j] for (i, j) in arcs if i == v and (v, j) in m.arcs) == 0,
    )

    model.capacity = pyo.Constraint(
        model.arcs,
        rule=lambda m, i, j: m.flow[i, j] <= cap[(i, j)],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"N":"0..7","A":"ordered (i,j) in N x N with i!=j","R":"1..6"},"params":{"capacity":"params['capacity']; accept an 8x8 matrix, 64 row-major matrix entries, 56 row-major non-self-loop entries, or 55 entries in the listed arc order with absent arc (4,3) assigned zero"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,k] for i in N if i!=k) == sum(flow[k,j] for j in N if j!=k) for k in R"],"objective":"maximize sum(flow[0,j] for j in N if j!=0) - sum(flow[i,0] for i in N if i!=0)"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    capacity_values = list(params["capacity"])

    if len(capacity_values) == len(nodes):
        try:
            rows = [list(row) for row in capacity_values]
        except TypeError:
            return {"objective": None, "status": "invalid_capacity_shape"}

        if any(len(row) != len(nodes) for row in rows):
            return {"objective": None, "status": "invalid_capacity_shape"}

        capacity_by_arc = {(i, j): rows[i][j] for i, j in arcs}

    elif len(capacity_values) == len(nodes) ** 2:
        capacity_by_arc = {
            (i, j): capacity_values[i * len(nodes) + j]
            for i, j in arcs
        }

    elif len(capacity_values) == len(arcs):
        capacity_by_arc = dict(zip(arcs, capacity_values))

    elif len(capacity_values) == len(arcs) - 1:
        listed_arcs = [arc for arc in arcs if arc != (4, 3)]
        capacity_by_arc = dict(zip(listed_arcs, capacity_values))
        capacity_by_arc[(4, 3)] = 0

    else:
        return {"objective": None, "status": "invalid_capacity_shape"}

    try:
        capacity_by_arc = {
            arc: float(value) for arc, value in capacity_by_arc.items()
        }
    except (TypeError, ValueError, OverflowError):
        return {"objective": None, "status": "invalid_capacity_value"}

    if any(
        not math.isfinite(value) or value < 0
        for value in capacity_by_arc.values()
    ):
        return {"objective": None, "status": "invalid_capacity_value"}

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.relay_nodes = pyo.Set(initialize=range(1, 7), ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacity_by_arc,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(network, k):
        return (
            sum(network.flow[i, k] for i in network.nodes if i != k)
            == sum(network.flow[k, j] for j in network.nodes if j != k)
        )

    model.flow_conservation = pyo.Constraint(
        model.relay_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.nodes if j != 0)
            - sum(model.flow[i, 0] for i in model.nodes if i != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_flat = params["capacity"]
    
    n = 8
    source = 0
    sink = 7
    
    # Build adjacency matrix from flat list (row-major, omitting diagonal)
    # The flat list has n*(n-1) entries: for each row i, columns j != i
    cap = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i != j:
                cap[(i, j)] = capacity_flat[idx]
                idx += 1
    
    # Collect edges with positive capacity
    edges = [(i, j) for (i, j), c in cap.items() if c > 0]
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")
    
    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")
    
    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")
    
    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == source) - \
                 gp.quicksum(flow[i, j] for (i, j) in edges if j == source)
    model.setObjective(total_flow, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 51.0 (optimal) | 69.0 (optimal) | 51.0 (optimal) |
| 1 | 122.0 (optimal) | 116.0 (optimal) | 122.0 (optimal) |
| 2 | 107.0 (optimal) | 111.0 (optimal) | 107.0 (optimal) |
| 3 | 60.0 (optimal) | 128.0 (optimal) | 60.0 (optimal) |
| 4 | 143.0 (optimal) | 153.0 (optimal) | 143.0 (optimal) |
| 5 | 36.0 (optimal) | 99.0 (optimal) | 36.0 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 51.0 (optimal) | 69.0 (optimal) | 51.0 (optimal) |
| 1 | 122.0 (optimal) | 116.0 (optimal) | 122.0 (optimal) |
| 2 | 107.0 (optimal) | 111.0 (optimal) | 107.0 (optimal) |
| 3 | 60.0 (optimal) | 128.0 (optimal) | 60.0 (optimal) |
| 4 | 143.0 (optimal) | 153.0 (optimal) | 143.0 (optimal) |
| 5 | 36.0 (optimal) | 99.0 (optimal) | 36.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{"mismatch": [{"parameter": "capacity", "extracted": [0, 19, 4, 1, 9, 13, 8, 20, 10, 0, 12, 12, 8, 12, 7, 7, 13, 11, 0, 8, 4, 1, 2, 3, 4, 12, 13, 0, 18, 6, 19, 8, 9, 16, 2, 0, 0, 14, 18, 7, 10, 11, 7, 11, 16, 0, 16, 5, 14, 11, 9, 11, 3, 17, 0, 19, 12, 20, 5, 11, 10, 4, 6, 0], "stated": [0, 19, 4, 1, 9, 13, 8, 20, 10, 0, 12, 12, 8, 12, 7, 7, 13, 11, 0, 8, 4, 1, 2, 3, 4, 12, 13, 0, 18, 6, 19, 8, 9, 16, 2, 0, 14, 18, 7, 10, 11, 7, 11, 16, 0, 16, 5, 14, 11, 9, 11, 3, 17, 0, 19, 12, 20, 5, 11, 10, 4, 6, 0], "evidence": "From Substation 4: Can send energy to Substation 0 (9 MW), Substation 1 (16 MW), Substation 2 (2 MW), Substation 5 (14 MW), Substation 6 (18 MW), and Substation 7 (7 MW)."}], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"capacity","evidence":"The capacity from Substation 4 to Substation 3 is filled in as 0 but is not stated: \"From Substation 4: Can send energy to Substation 0 (9 MW), Substation 1 (16 MW), Substation 2 (2 MW), Substation 5 (14 MW), Substation 6 (18 MW), and Substation 7 (7 MW).\""}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 25. mamo_complex_205 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_205` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 205) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 1.0 |
| Label (original benchmark) | 0.6 |
| Rules that certify it | gate 1.0, panel_base_2of3 1.0, ind_gate 1.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Before one World Cup championship, there are 5 types of securities available for sale. The price of each share of the security is fixed and the payoff of it will be contingent on the outcome of the outcome of the world cup. The information of the 5 securities are shown in Table 1. Here, for example, Security 1’s payoff is 1 if either Argentina, Brazil, or England wins the world cup, and the payoff is 0 if Germany or Spain wins. The Share Limit is the maximum number of shares one can purchase, and Price is the current purchasing price per share of each security. There are five countries, Argentina, Brazil, England, Spain, Germany. Security 1 has a price of 0.75 and a share limit of 10. The payoff for this security is $1 in Argentina, $1 in Brazil, $1 in England, 0 in Germany, and 0 in Spain. Security 2 is priced at 0.35 with a share limit of 5. The payoff is 0 for Argentina, Brazil, or England, but it's $1 for Germany and Spain. Security 3 has a price of 0.40 and a share limit of 10. Similar to Security 2, the payoff is $1 for Argentina, $1 for Spain, and $1 for England, and 0 payoff for Germany and Brazil. Security 4, with a price of 0.75 and a share limit of 10, has payoff of $1 across all countries except for Spain. Security 5 is priced at 0.65, has a share limit of 5, and has payoff of $1 in Brazil, Germany and Spain, 0 in Argentina and England. Find the maximum worst-case revenue.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"security_price": {"base":[0.75,0.35,0.4,0.75,0.65],"perturb":{"mode":"rel","r":0.5}}
"share_limit": {"base":[10,5,10,10,5],"perturb":{"mode":"rel","r":0.5}}
"payoff": {"base":[[1,1,1,0,0],[0,0,0,1,1],[1,0,1,1,0],[1,1,1,0,1],[0,1,0,1,1]],"perturb":{"mode":"abs","lo":0.0,"hi":1.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price = params["security_price"]
    limit = params["share_limit"]
    payoff = params["payoff"]

    securities = list(range(5))
    countries = list(range(5))  # Argentina, Brazil, England, Spain, Germany

    model = pyo.ConcreteModel()

    model.x = pyo.Var(securities, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0, limit[i]))

    # Worst-case revenue over countries
    model.R = pyo.Var()

    def revenue_rule(m, c):
        return m.R <= sum(payoff[i][c] * m.x[i] for i in securities)

    model.revenue_con = pyo.Constraint(countries, rule=revenue_rule)

    # Budget: cost is exactly 1 (w.l.o.g. since revenue is linear & homogeneous)
    def budget_rule(m):
        return sum(price[i] * m.x[i] for i in securities) == 1

    model.budget = pyo.Constraint(rule=budget_rule)

    model.obj = pyo.Objective(expr=model.R, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"I":[0,1,2,3,4],"C":["Argentina","Brazil","England","Spain","Germany"]},"params":{"security_price":"params['security_price'][i]","share_limit":"params['share_limit'][i]","payoff":"params['payoff'][i][c], country columns in C order"},"variables":{"shares[i]":"nonnegative continuous","worst_case_revenue":"real"},"constraints":["shares[i] <= share_limit[i] for every i","worst_case_revenue <= sum_i((payoff[i,c] - security_price[i])*shares[i]) for every c"],"objective":"maximize worst_case_revenue"}
# Revenue is net of purchase costs; fractional shares are permitted.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    security_price = params["security_price"]
    share_limit = params["share_limit"]
    payoff = params["payoff"]

    model = pyo.ConcreteModel()
    model.securities = pyo.RangeSet(0, 4)
    model.countries = pyo.Set(
        initialize=["Argentina", "Brazil", "England", "Spain", "Germany"],
        ordered=True,
    )
    country_column = {
        country: column
        for column, country in enumerate(model.countries)
    }

    model.purchase_price = pyo.Param(
        model.securities,
        initialize={
            security: security_price[security]
            for security in model.securities
        },
        within=pyo.Reals,
    )
    model.purchase_limit = pyo.Param(
        model.securities,
        initialize={
            security: share_limit[security]
            for security in model.securities
        },
        within=pyo.NonNegativeReals,
    )
    model.outcome_payoff = pyo.Param(
        model.securities,
        model.countries,
        initialize={
            (security, country): payoff[security][country_column[country]]
            for security in model.securities
            for country in model.countries
        },
        within=pyo.Reals,
    )

    model.shares = pyo.Var(
        model.securities,
        domain=pyo.NonNegativeReals,
    )
    model.worst_case_revenue = pyo.Var(domain=pyo.Reals)

    def purchase_limit_rule(problem, security):
        return problem.shares[security] <= problem.purchase_limit[security]

    model.share_cap = pyo.Constraint(
        model.securities,
        rule=purchase_limit_rule,
    )

    def outcome_revenue_rule(problem, country):
        return problem.worst_case_revenue <= sum(
            (
                problem.outcome_payoff[security, country]
                - problem.purchase_price[security]
            )
            * problem.shares[security]
            for security in problem.securities
        )

    model.revenue_guarantee = pyo.Constraint(
        model.countries,
        rule=outcome_revenue_rule,
    )
    model.max_revenue = pyo.Objective(
        expr=model.worst_case_revenue,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.max_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    security_price = params["security_price"]   # list of 5 prices
    share_limit    = params["share_limit"]       # list of 5 share limits
    payoff         = params["payoff"]            # 5x5 matrix: payoff[i][j]

    num_securities = 5
    num_countries  = 5

    model = gp.Model("world_cup_securities")
    model.setParam("OutputFlag", 0)

    # x[i] = number of shares purchased of security i
    x = model.addVars(num_securities, lb=0.0, name="x")

    # Enforce share limits
    for i in range(num_securities):
        model.addConstr(x[i] <= share_limit[i], name=f"share_limit_{i}")

    # z = worst-case revenue (net payoff minus cost) across all country outcomes
    z = model.addVar(lb=-GRB.INFINITY, name="z")

    # Total cost of purchasing shares
    total_cost = gp.quicksum(security_price[i] * x[i] for i in range(num_securities))

    # For each country outcome j, revenue = sum_i payoff[i][j] * x[i] - total_cost
    # z <= revenue for every outcome j
    for j in range(num_countries):
        revenue_j = gp.quicksum(payoff[i][j] * x[i] for i in range(num_securities))
        model.addConstr(z <= revenue_j - total_cost, name=f"worst_case_country_{j}")

    # Maximize worst-case revenue
    model.setObjective(z, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1.1111111111111112 (optimal) | 1.0 (optimal) | 1.0 (optimal) |
| 1 | 1.3771035260948479 (optimal) | 2.7100976732035624 (optimal) | 2.7100976732035624 (optimal) |
| 2 | 1.3610208047895545 (optimal) | 3.9548677358487336 (optimal) | 3.954867735848733 (optimal) |
| 3 | 1.208152859835926 (optimal) | 1.5834259573624494 (optimal) | 1.5834259573624498 (optimal) |
| 4 | 1.0146736195824595 (optimal) | 0.07790019978221885 (optimal) | 0.07790019978221885 (optimal) |
| 5 | 1.5872196213119927 (optimal) | 4.255055527830257 (optimal) | 4.255055527830257 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1.1111111111111112 (optimal) | 1.0 (optimal) | 1.0 (optimal) |
| 1 | 2.0252529122813434 (optimal) | 2.9712869135266087 (optimal) | 2.9712869135266087 (optimal) |
| 2 | 0.9791632347820456 (optimal) | -0.0 (optimal) | -0.0 (optimal) |
| 3 | 0.8739382957314946 (optimal) | -0.0 (optimal) | -0.0 (optimal) |
| 4 | 1.7008267485053707 (optimal) | 1.5727747307379527 (optimal) | 1.5727747307379527 (optimal) |
| 5 | 1.0336227999335952 (optimal) | 0.13202192553706893 (optimal) | 0.13202192553706915 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{"mismatch": [{"parameter": "payoff", "extracted": [[1, 1, 1, 0, 0], [0, 0, 0, 1, 1], [1, 0, 1, 1, 0], [1, 1, 1, 0, 1], [0, 1, 0, 1, 1]], "stated": [[1, 1, 1, 0, 0], [0, 0, 0, 1, 1], [1, 0, 1, 1, 0], [1, 1, 1, 0, 1], [0, 1, 0, 1, 1]]}], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
Looking at each parameter against the statement:

**security_price**: [0.75, 0.35, 0.4, 0.75, 0.65] — matches the statement exactly.

**share_limit**: [10, 5, 10, 10, 5] — matches the statement exactly.

**payoff**: Check each row against the statement:
- Security 1: Argentina=1, Brazil=1, England=1, Germany=0, Spain=0 → extracted row [1,1,1,0,0] with columns ordered (Argentina, Brazil, England, Spain, Germany) gives [1,1,1,0,0]. Matches.
- Security 2: Argentina=0, Brazil=0, England=0, Germany=1, Spain=1 → in (Arg, Bra, Eng, Spa, Ger) order: [0,0,0,1,1]. Extracted [0,0,0,1,1]. Matches.
- Security 3: "payoff is $1 for Argentina, $1 for Spain, and $1 for England, and 0 payoff for Germany and Brazil" → in (Arg, Bra, Eng, Spa, Ger) order: [1,0,1,1,0]. Extracted [1,0,1,1,0]. Matches.
- Security 4: "$1 across all countries except for Spain" → in (Arg, Bra, Eng, Spa, Ger) order: [1,1,1,0,1]. Extracted [1,1,1,0,1]. Matches.
- Security 5: "$1 in Brazil, Germany and Spain, 0 in Argentina and England" → in (Arg, Bra, Eng, Spa, Ger) order: [0,1,0,1,1]. Extracted [0,1,0,1,1]. Matches.

All parameters match.

```json
{"mismatch": [], "not_stated": []}
```
````

