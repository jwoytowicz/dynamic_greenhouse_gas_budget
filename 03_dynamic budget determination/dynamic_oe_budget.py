import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.integrate import quad
from matplotlib.ticker import MaxNLocator


# Key parameters for the time period and the constant budget
T_min = 2025
T_max = 2045

# Constant GHG emission level for operational emissions
x_op_base = 3.86

# Area (integral) under this constant budget line
I_constant = x_op_base * (T_max - T_min)

# Fitted functions for heating (f) and electricity (g)

def f(x):
    # Sigmoid fit for the share of non-renewable heating.
    # Example parameters from previous analysis.
    return 88.71710115840355 / (1 + np.exp(-(-3.348762256837263) * (x - 0.4505688285851687)))

def g(x):
    # Sinusoidal fit for the share of non-renewable electricity.
    # Example parameters from previous analysis.
    return 36.10080564331148 * np.sin(0.3155578919710513 * x + 3.058151974258264) + 39.54060321870498

# Weight factor (share of electricity vs. heating)
w = 0.137

# Raw function Z(t): combination of f and g,
# mapping t in [2025..2045] to x in [0..1].

def scale_year(year):
    # Scale a given year between T_min and T_max onto the range [0..1]
    return (year - T_min) / (T_max - T_min)

def Z(year):
    # Combined function Z(t) = (1 - w)*f(x) + w*g(x), where x = scaled year.
    x = scale_year(year)
    return (1 - w) * f(x) + w * g(x)

# We want dynamic(t) = a + b*Z(t) such that:
#       (a) The integral over [T_min..T_max] equals I_constant
#       (b) dynamic(2045) = 0.15 * dynamic(2025)

# Compute Z(2025) and Z(2045) for boundary conditions
Z_2025 = Z(T_min)
Z_2045 = Z(T_max)

# Compute the integral of Z(t) over [2025..2045]
def Z_of_t(t):
    return Z(t)

I_Z, _ = quad(Z_of_t, T_min, T_max)

# We aim for:
#   dynamic budget (2025) = a + b * Z_2025
#   dynamic budget (2045) = a + b * Z_2045
#   Condition 1 (to stay in line with the available budget): ∫ dynamic(t) dt = I_constant
#   Condition 2 (to make sure that the relation of the projection data stays relevant): 
#   factor_2025_2045 = dynamic budget (2045) / dynamic budget(2025) = w * (electricity mix (2045) / electricity mix (2025)) + (1 - w) * (heating mix (2045) / heating mix (2025))

# Distribution factor (based on ratio of partial shares of the electricity and heating mix)
factor_2025_2045 = w * (4.3 / 42.2) + (1 - w) * (11.6 / 71.9) # = 0,15

# => dynamic(2045) = 0.15 * dynamic(2025)
# => a + b * Z_2045 = 0.15 * (a + b * Z_2025)
# => (1)  0.85 * a + b * (Z_2045 - 0.15 * Z_2025) = 0
# => (2)  ∫(a + b * Z(t)) dt = a * (T_max - T_min) + b * I_Z = I_constant

def solve_for_a_b():

    # Solve the system of equations:
    #   0.85 * a + b * (Z_2045 - 0.15 * Z_2025) = 0
    #   a * (T_max - T_min) + b * I_Z = I_constant
    
    # Using a parametric approach, we express a in terms of b, then
    # solve for b from the integral condition.

    # (1) Express a as a function of b
    # numerator = -(Z_2045 - 0.15 * Z_2025)
    numerator = -(Z_2045 - factor_2025_2045 * Z_2025)
    
    def a_in_terms_of_b(b_val):
        return b_val * numerator / (1 - factor_2025_2045)

    # (2) The integral condition:
    # a*(T_max - T_min) + b * I_Z = I_constant
    # Substituting a_in_terms_of_b into it:
    denom = (numerator / (1 - factor_2025_2045)) * (T_max - T_min) + I_Z

    b_sol = I_constant / denom
    a_sol = a_in_terms_of_b(b_sol)
    return a_sol, b_sol

a, b = solve_for_a_b()

def dynamic(t):
    # Define the dynamic GHG budget function: dynamic(t) = a + b * Z(t)
    return a + b * Z(t)

# Plot and verification

# Check that dynamic(2045)/dynamic(2025) ~ 0.15 and that the integral is correct
ratio_2045_2025 = dynamic(T_max) / dynamic(T_min)
I_dynamic, _ = quad(dynamic, T_min, T_max)

print(f"Z(2025) = {Z_2025:.3f},   Z(2045) = {Z_2045:.3f}")
print("a =", a, "   b =", b)
print(f"Ratio dynamic(2045)/dynamic(2025) = {ratio_2045_2025:.3f}")
print(f"I_constant  = {I_constant:.4f}")
print(f"I_dynamic   = {I_dynamic:.4f}\n")

# Set the font family to Arial
plt.rcParams["font.family"] = "Arial"

years = np.arange(T_min, T_max + 1)
dyn_vals = [dynamic(y) for y in years]

plt.figure(figsize=(8, 6))

# Plot the static GHG budget line
plt.axhline(
    x_op_base,
    color='b',
    linestyle='--',
    label=f"Static GHG budget for operational \nemissions = {x_op_base} kg CO$_2$e/(m$^2$*a)"
)

# Plot the dynamic budget
plt.plot(
    years,
    dyn_vals,
    label="Dynamic GHG budget\n(Climate neutrality by 2045)",
    color='purple'
)

# Highlight the area under the dynamic budget curve
plt.fill_between(
    years,
    dyn_vals,
    0,
    color='purple',
    alpha=0.2,
    hatch='///',
    label="Total GHG budget for operational emissions"
)

plt.xlabel("Year", fontsize=16)
plt.ylabel("Emissions [kg CO$_2$e/(m$^2$·a)]", fontsize=16)
plt.xlim([T_min, T_max])
plt.ylim([0, 10])
plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
plt.legend(fontsize=16)
plt.grid(alpha=0.3)
plt.tick_params(axis='both', labelsize=16)

# Force integer ticks on the x-axis
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

plt.show()

# Print result
print(f"2025: dynamic = {dynamic(T_min):.2f} kg CO₂e/(m²·a)")
print(f"2045: dynamic = {dynamic(T_max):.2f} kg CO₂e/(m²·a)")

dyn_results = {year: dynamic(year) for year in years}

# Convert results to DataFrame
df_results = pd.DataFrame(list(dyn_results.items()), columns=["Year", "Dynamic GHG Budget"])

# Print results for each year
for year, value in dyn_results.items():
    print(f"{year}: dynamic = {value:.2f} kgCO₂e/(m²·a)")
