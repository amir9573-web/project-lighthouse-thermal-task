# Scientific reasoning for the thermal commissioning task

The engineering decision is whether a proposed heater duty cycle can be operated within a specified core temperature envelope. A steady-state resistance estimate is not enough. Heat accumulates in two bodies at different rates, and the hottest core temperature may occur at a different time from the hottest enclosure temperature. The task therefore combines an inverse problem with an operating decision: infer a dynamic model from several experiments, assess whether it predicts separate experiments, and use its sensitivity to experimental selection when setting the heater power.

The measurements are synthetic. Their purpose is to create a controlled commissioning study in which the physical assumptions, acquisition conventions and correct estimands can be stated without relying on unavailable laboratory information. The specification contains the energy balances and definitions of the quantities to estimate. It does not supply generating coefficients, fitted results or code. An agent still has to interpret the records and build a defensible computation.

## Interpreting the observations

Calibration comes before any inference about thermal behaviour. The two sensors have different gains and offsets, so treating their raw difference as a physical temperature difference would distort the coupling conductance. Ordinary least squares is appropriate for the defined bath calibration: the reference temperatures are treated as exact, and the raw sensor response is affine. The raw-to-physical conversion must invert the fitted relation. Confusing that direction changes both the transient fit and the eventual temperature limit calculation.

Each observation has a separate validity indicator. A missing enclosure value does not make a simultaneous core observation useless. Conversely, a numerical value with a rejected quality flag must not enter the objective simply because it can be parsed. The initial states are independently measured physical temperatures. Replacing them with the first noisy sensor readings would introduce initial-state errors which the fitted heat capacities could absorb.

Timing is another consequential choice. Commands and environmental inputs are held constant over the interval starting at each row; temperatures are sampled at the row timestamp. Only the heater is delayed. Shifting fan commands along with heater commands would change both conductances at the wrong time. Interpolating the piecewise-constant input would create a different experiment.

## Estimation and identification

The two energy balances conserve heat between the core and enclosure. Their exchange terms have opposite signs, while only the enclosure loses heat to ambient. The six positive coefficients describe two heat capacities and the base and fan contributions to two conductances. Several training runs are used because a single constant-power transient can leave capacities and conductances strongly correlated. Changes in heating, fan state and ambient expose different parts of the response. Observing both bodies is especially useful for separating internal transfer from external loss.

The heater delay is a discrete nuisance parameter. For each allowed delay, the reference implementation minimizes the same noise-standardized residual sum of squares over all accepted training observations. It then selects the smallest minimized objective. This is a comparison of fitted candidates, not a comparison made while holding coefficients at an arbitrary starting value. Each candidate is fitted from two starting points. Agreement supports convergence, although it is not a mathematical proof of global optimality.

For a fixed fan state and input interval, the differential equations are linear with constant coefficients. The reference uses an exact matrix exponential transition and a constant-forcing integral. This avoids confusing numerical integration error with measurement noise. Logarithmic parameter coordinates enforce positivity; bounds implement the explicitly stated admissible domain. The independent verifier uses an RK4 transition polynomial with twenty subintervals and optimizes directly in scaled physical coordinates. Its calibration uses normal equations rather than the reference's least-squares factorization. Different propagation and parameterization choices reduce the chance that a shared implementation error passes unnoticed.

The known measurement standard deviation defines the residual weighting. The covariance is conditional on the selected delay, calibration and initial states. It is computed from the inverse information matrix in physical parameter units. The reference converts its logarithmic-coordinate Jacobian back into that convention; the verifier computes a central-difference Jacobian in scaled physical coordinates. A residual-variance multiplier would be inappropriate because this task specifies the variance as known. This covariance is a local linear approximation and does not describe uncertainty about the discrete delay or the bath calibration.

## Validation and operating decision

The two validation runs are excluded from every training fit. Their channel-specific RMSE values are computed using only accepted observations and the full-data fitted model. Small training residuals alone cannot establish useful prediction: a model can absorb a timing or calibration error and still extrapolate badly when inputs change. The separate validation inputs make that issue observable.

Four further fits each omit one complete training experiment while retaining the chosen delay. Omitting individual points would answer a different question, since records within an experiment share their input history and initial state. These fits indicate how the engineering recommendation depends on the measurement campaign. The resulting five-model envelope is a sensitivity measure, not a confidence band with a stated coverage probability.

The proposed cycle begins with both bodies at constant ambient temperature. In this linear setting, excess temperature scales linearly with heater power. The reference uses that fact to compute the largest feasible multiplier from the largest unscaled ensemble core rise. It also enforces the permitted interval from zero to one. The verifier reaches the multiplier through bisection and repeated trajectory calculations instead of using the scaling shortcut. Both methods evaluate the entire supplied timestamp grid, including the cooling period. The task intentionally defines a sampled operating constraint. It does not certify unseen continuous-time maxima or thermal safety of a real assembly.

The forecast reports both the nominal trajectory and the pointwise maximum across the ensemble for each body. A single ensemble member need not dominate at every timestamp. Taking only the maximum final temperature, or using one model's peak as an envelope for every time, would not reproduce the requested quantities.

## Dependency depth audit

The following analysis units describe the reasoning behind the implementation. They are reviewer documentation, not instructions supplied to the agent. Some are repeated across multiple runs; the list does not count ordinary file operations as scientific steps.

1. Establish the two-body energy accounting and units.
2. Identify the calibration direction for the core sensor.
3. Identify the calibration direction for the enclosure sensor.
4. Estimate each sensor's gain and offset from bath records.
5. Convert experimental observations into physical temperatures.
6. Build separate missing-value masks for both channels.
7. Apply each channel's acquisition flags without discarding its partner.
8. Distinguish fixed physical initial states from noisy sensor readings.
9. Resolve row timestamps against interval-held inputs.
10. Separate heater timing from fan and ambient timing.
11. Construct the delayed heater history for each candidate.
12. Form the fan-dependent internal conductance.
13. Form the fan-dependent external loss conductance.
14. Assemble the coupled state dynamics with correct transfer signs.
15. Account for the ambient forcing term.
16. Propagate states across every input transition.
17. Align model states with accepted observations.
18. Form the known-variance standardized objective across experiments.
19. Fit all six bounded physical coefficients for each delay.
20. Check convergence from distinct starting points.
21. Compare optimized delay candidates and select the full-data delay.
22. Compute local sensitivities to physical coefficients.
23. Assess and invert the parameter information matrix.
24. Preserve conditional uncertainty units and variance conventions.
25. Predict the first validation experiment without refitting.
26. Predict the second validation experiment without refitting.
27. Compute validation errors independently for each channel.
28. Refit after deletion of each complete training experiment.
29. Build the operating ensemble while keeping delay fixed.
30. Propagate the proposed cycle for all ensemble members.
31. Locate nominal and ensemble peaks over the full reporting grid.
32. Determine the largest feasible common heater multiplier.
33. Recompute nominal and pointwise envelope histories at that multiplier.
34. Cross-check the decision with independent propagation and optimization.

An error in calibration or timing damages parameter estimation, uncertainty, validation and the power recommendation. The workflow therefore has consequential dependencies. Its actual difficulty for advanced agents still needs Hurix's model trials; the step audit is not evidence of an observed agent failure rate.
