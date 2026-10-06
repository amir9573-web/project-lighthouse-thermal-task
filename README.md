# Thermal commissioning research task

This package asks an agent to identify a coupled thermal assembly from calibrated, incomplete measurements and decide how much of a proposed heater cycle can be used within a specified temperature envelope. The data is synthetic. The work is intended to resemble an engineering commissioning analysis rather than an exam problem.

The Harbor task directory is `tasks/engineering/thermal-systems/pulsed-cooling-identification`. Only `environment/data` is copied into the agent image. The reference implementation lives in `solution` and the independent verifier in `tests`; neither is baked into the image.

## Run the required checks

On a Docker-capable host with Python 3.12 or 3.13 and uv available:

```bash
uv tool install harbor==0.24.0
harbor run -p tasks/engineering/thermal-systems/pulsed-cooling-identification -a oracle
harbor run -p tasks/engineering/thermal-systems/pulsed-cooling-identification -a nop
```

The Harbor version above is pinned to the PyPI release checked during preparation; the current official documentation uses schema_version 1.3. Confirm any version required by Hurix before submission. The package has not yet been validated inside Docker. See VALIDATION.md for the exact local checks and outstanding requirements.

The reference entry point writes `/app/output/result.json` and `/app/output/forecast.csv`. The verifier independently estimates the scientific results from raw inputs, checks every numerical output, and writes `/logs/verifier/reward.txt`. It awards 1 only if all checks pass. Missing output and incorrect scientific quantities receive 0.

## Review and submission

Read solution_explanation.md for scientific reasoning and the dependency depth audit. DECLARATION.md records assistance and the review still required from the contributor. Contributor Guidelines were not supplied, so their additional metadata or declaration requirements remain unchecked.

Do not circulate the solution outside the assessment. Create a private GitHub repository, invite the Hurix reviewers, and share its URL with your contact. If a public repository is expressly required for access, follow Hurix's visibility instructions and make it private when requested. The package is uploaded to the private repository https://github.com/amir9573-web/project-lighthouse-thermal-task. Reviewer access and delivery of the URL to Hurix remain outstanding.

## Technical references

* Harbor task structure and isolation: https://docs.harborframework.com/tasks/overview
* Harbor configuration schema: https://docs.harborframework.com/tasks/configuration
* SciPy least squares API: https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.optimize.least_squares.html
* Python container image source: https://github.com/docker-library/python

The thermal model is fully specified through its energy balances in the supplied measurement specification; no external paper is required to interpret the data.
