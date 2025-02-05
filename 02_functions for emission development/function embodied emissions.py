import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import pandas as pd
from matplotlib import rcParams

# Set the font family to Arial
rcParams['font.family'] = 'Arial'

# Color scheme suitable for red-green color blindness
color_cycle = [
    "#1b9e77",
    "#d95f02",
    "#7570b3",
    "#e7298a",
    "#66a61e",
    "#e6ab02",
    "#a6761d",
    "#666666"
]

# Data from projections of the Agora Industrie (2024) for the share of non-renewable electricity from 2025 to 2045
# (https://www.agora-industrie.de/fileadmin/Projekte/2022/2022-10_IND_Embodied_Carbon/A-IN_341_Embodied_Carbon_WEB.pdf)
years = np.array([
    2025, 2026, 2027, 2028, 2029, 2030,
    2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040,
    2041, 2042, 2043, 2044, 2045
])

values = np.array([
    47.7, 41.2, 35.3, 30.1, 25.5, 21.6, 
    19.6, 17.6, 15.7, 14.4, 13.7, 12.4, 11.8, 10.5, 9.8, 9.2,
    8.5, 7.8, 7.2, 6.5, 5.9
])

# Normalization and scaling for later use in certain function types
x_normalized = (years - years.min()) / (years.max() - years.min())
x_scaled_sinus = x_normalized * 2 * np.pi

# Define the function types for curve fitting
def linear(x, a, b):
    return a * x + b

def quadratic(x, a, b, c):
    return a * x**2 + b * x + c

def cubic(x, a, b, c, d):
    return a * x**3 + b * x**2 + c * x + d

def exponential(x, a, b):
    return a * np.exp(b * x)

def logarithmic(x, a, b):
    return a * np.log(x + 1) + b  # +1 to avoid log(0) issues

def power(x, a, b):
    return a * (x + 1)**b  # +1 to avoid issues at x=0

def sinusoidal(x, a, b, c, d):
    return a * np.sin(b * x + c) + d

def sigmoid(x, L, k, x0):
    return L / (1 + np.exp(-k * (x - x0)))

# List of function definitions and their initial parameters (p0)
functions = [
    (linear, "Linear", x_normalized, None),
    (quadratic, "Quadratic", x_normalized, None),
    (cubic, "Cubic", x_normalized, None),
    (exponential, "Exponential", x_normalized, None),
    (logarithmic, "Logarithmic", x_normalized, None),
    (power, "Power", x_normalized, None),
    # Provide initial guesses for the sinusoidal fit:
    (sinusoidal, "Sinusoidal", x_scaled_sinus, [10, 1, 0, np.mean(values)]), 
    # Provide initial guesses for the sigmoid fit:
    (sigmoid, "Sigmoid", x_normalized, [max(values), 1, 0.5])
]

# Prepare for fitting and plotting
results = []
plt.figure(figsize=(8, 6))
plt.scatter(years, values, label="Projection data", color="black", s=30)

# Filter the data for the range 2025–2045 (optional if your data is already in range)
start_year = 2025
end_year = 2045
mask = (years >= start_year) & (years <= end_year)

# Filtered data
years_subset = years[mask]
values_subset = values[mask]
x_normalized_subset = x_normalized[mask]
x_scaled_sinus_subset = x_scaled_sinus[mask]

# Fitting each function and evaluating performance
for i, (func, name, x, p0) in enumerate(functions):
    try:
        # Curve Fitting
        popt, _ = curve_fit(func, x, values, p0=p0, maxfev=10000)
        y_pred = func(x, *popt)

        # Subset prediction for performance metrics
        if name == "Sinusoidal":
            y_pred_subset = func(x_scaled_sinus_subset, *popt)
        else:
            y_pred_subset = func(x_normalized_subset, *popt)

        # Calculate metrics (R², MAE, RMSE)
        r2 = r2_score(values_subset, y_pred_subset)
        mae = mean_absolute_error(values_subset, y_pred_subset)
        rmse = np.sqrt(mean_squared_error(values_subset, y_pred_subset))

        # AIC calculation
        n = len(values_subset)
        residuals = values_subset - y_pred_subset
        sse = np.sum(residuals**2)
        k = len(popt)
        aic = 2 * k + n * np.log(sse / n)

        # Save results
        results.append((name, r2, mae, rmse, aic, popt))

        # Plot the fitted curve over the full x-range (2025–2045)
        plt.plot(years, y_pred, label=f"{name} (R²={r2:.3f})", color=color_cycle[i % len(color_cycle)], linewidth=2)

    except Exception as e:
        # If fitting fails, store None or error message
        results.append((name, None, None, None, None, str(e)))
        print(f"Function: {name} - Error: {e}")

# Final plot formatting
plt.xlabel("Year", fontsize=16)
plt.ylabel("Reduction for embodied emissions\n compared to 2025 [%]", fontsize=16)

# Set the x-axis range and y-axis range
plt.xlim([2025, 2045]) 
plt.ylim([0, 100]) 

# Force integer ticks on x-axis
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
# Increase tick font size
ax.tick_params(axis='both', which='major',labelsize=16)

# Legend with adjusted font size
plt.legend(fontsize=16)
plt.show()

# Create a DataFrame of results and print
results_df = pd.DataFrame(results, columns=["Function Type", "R²", "MAE", "RMSE", "AIC", "Parameters"])

# Print the entire results DataFrame
print(results_df.to_string())