# Measurement specification

## Physical scope

These are synthetic measurements of a two-body heater and enclosure. They represent a numerical commissioning study, not observations from a physical laboratory. Both bodies are spatially uniform, with constant heat capacities. Heat is delivered entirely to the core. The enclosure exchanges heat with ambient air; direct core-to-ambient exchange is excluded. Conductances depend on binary fan state. Radiative and nonlinear material effects are outside this study.

The governing balances are

Ccore dTcore/dt = Qdelivered - G(fan) (Tcore - Tcase)

Ccase dTcase/dt = G(fan) (Tcore - Tcase) - H(fan) (Tcase - Tambient)

G(fan) = coupling-base + coupling-fan * fan

H(fan) = loss-base + loss-fan * fan

Capacities are in J/K and conductances in W/K. Temperature is in degrees Celsius; all differences have the same numerical value in kelvin. Time is in seconds and power in watts. All six coefficients are constant across runs. The physical parameter order is core-capacity, case-capacity, coupling-base, coupling-fan, loss-base, loss-fan. Admissible intervals in that order are [50,5000], [90,9000], [0.4,40], [0.2,20], [0.2,20], [0.3,30].

## Acquisition records

calibration.csv contains independently traceable bath temperatures and simultaneous raw readings from each sensor. Each sensor obeys raw = gain * temperature + offset. Fit a separate ordinary least squares affine calibration to all its bath records; calibration uncertainty is excluded from the subsequent conditional covariance. This convention defines a reproducible estimator, not a recommendation for full metrological uncertainty reporting.

Each run CSV contains time_s, power_W, fan, ambient_C, core_raw, case_raw, core_valid and case_valid. A row's power, fan and ambient apply on the interval beginning at that row. Its temperatures are instantaneous readings at the row timestamp. The final row defines the last reported temperature, with no following propagation interval. All grids have 10-second intervals. An empty reading is unavailable. A channel is usable only when its validity flag equals 1 and its reading is finite; a rejected channel does not invalidate the other channel. Unusable readings carry no information about temperature.

The initial temperatures in protocol.json are independent physical measurements, already in degrees Celsius, and are the fixed state at time zero. There is no unknown initial-state offset. Noise on accepted run measurements is independent Gaussian temperature noise with known standard deviation noise_C; do not estimate a new variance from residuals.

The heater delay is one shared integer number of sampling intervals from the listed candidates. On interval i, delivered power is power_W at row i minus delay_samples, or zero if that index is negative. Fan and ambient are not delayed. The model uses zero-order holds at input transitions. This is an explicit actuator convention, not an invitation to interpolate the commands.

## Estimands and uncertainty

For each candidate delay, the estimand is the global minimum sum of squared residuals over accepted, calibrated core and enclosure readings in the training runs, divided by noise_C squared. Select the candidate with the smallest objective; a tie would select the smaller delay. The validation runs never enter parameter estimation or delay selection. Report validation RMSE separately for each channel, using its accepted readings and predictions from the full training fit.

The covariance is conditional on the selected delay, calibration and initial states. It is the inverse of J transpose J, where J is the Jacobian of noise-standardized training residuals with respect to the six physical parameters in their declared units. There is no residual-variance multiplier. A singular information matrix would require reporting a failure to identify the model rather than inventing a covariance.

For each training run, omit that entire run and refit the six coefficients to the remaining training runs, retaining the full-data selected delay. The operating ensemble consists of the full-data fit and these four deletion fits. Its pointwise envelope is the maximum temperature across the five members, separately for each body. This sensitivity envelope is not a statistical confidence interval.

proposed-cycle.csv uses the same input timing convention. All ensemble members start at cycle_initial_C. A common multiplier in [0,1] applies to every commanded power in this cycle. The permitted multiplier is the largest value for which the maximum ensemble core temperature at all supplied reporting timestamps is no greater than core_limit_C. This is a sampled commissioning constraint; do not claim certification of continuous-time peaks between timestamps. Report the unscaled core peak of the full-data model and the unscaled ensemble core peak as well.

## Output contract

result.json is a JSON object with exactly the following keys. Use finite JSON numbers and do not round intermediate estimates.

* parameter_order: the six parameter names in the stated order.
* calibration: core and case, each holding [gain, offset].
* parameters: six fitted physical coefficients.
* delay_samples: the selected integer delay.
* delay_profile: a map from each candidate's decimal string to its minimized noise-standardized sum of squares.
* weighted_sse: the full-data objective at the selected delay.
* covariance: a 6 by 6 array in physical units.
* leave_one_run_out: one object for each omitted training run, each with parameters and weighted_sse.
* validation_rmse_C: one array [core RMSE, case RMSE] for each validation run.
* power_scale: the permitted multiplier.
* unscaled_core_peak_C: the nominal unscaled cycle peak.
* envelope_core_peak_C: the ensemble unscaled cycle peak.

forecast.csv has columns time_s,core_C,case_C,core_envelope_C,case_envelope_C, in that order. It contains every proposed-cycle timestamp exactly once in increasing order, including zero and the final timestamp. Nominal columns use the full-data model at power_scale. Envelope columns use the maximum over the operating ensemble at the same multiplier. Column names encode units and there is no row index column.
