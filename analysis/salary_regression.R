# Is mentioning Machine Learning associated with a higher posted salary once
# seniority is held fixed?
#
# Model: log(salary midpoint) ~ mentions_ml + seniority
# (Remote status is left out: every posting with salary data has remote = 0.)
# On the log scale, exp(coef) - 1 is the associated percentage difference.
# Observational data: this is an adjusted association, not a causal effect.
#
# Reads the SQLite database through the sqlite3 command-line tool, so it needs
# no R packages beyond base R.
#
# Run from the repo root:  Rscript analysis/salary_regression.R

query <- "
SELECT j.id, COALESCE(j.seniority, 'unknown') AS seniority,
       (j.salary_min + j.salary_max) / 2.0 AS salary,
       MAX(CASE WHEN s.skill = 'Machine Learning' THEN 1 ELSE 0 END) AS mentions_ml
FROM jobs j
LEFT JOIN job_skills s ON s.job_id = j.id
WHERE j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL
GROUP BY j.id"

jobs <- read.csv(pipe(sprintf('sqlite3 -csv -header data/skillradar.db "%s"', gsub("\n", " ", query))))
jobs <- subset(jobs, salary >= 30000 & salary <= 500000)  # same filter as src/train_salary.py
jobs$seniority <- relevel(factor(jobs$seniority), ref = "mid")

cat(sprintf("%d postings; %d mention Machine Learning\n\n", nrow(jobs), sum(jobs$mentions_ml)))

# Unadjusted Welch t-test, to cross-check the Python script (ML group first, same sign as Python)
tt <- t.test(jobs$salary[jobs$mentions_ml == 1], jobs$salary[jobs$mentions_ml == 0])
cat(sprintf("Welch t-test (unadjusted): t = %.2f, p = %.2e\n\n", tt$statistic, tt$p.value))

fit <- lm(log(salary) ~ mentions_ml + seniority, data = jobs)
print(summary(fit))

b <- coef(fit)["mentions_ml"]
ci <- confint(fit)["mentions_ml", ]
cat(sprintf(
  "\nAdjusted for seniority: mentioning ML is associated with a %.1f%% higher salary (95%% CI %.1f%% to %.1f%%)\n",
  100 * (exp(b) - 1), 100 * (exp(ci[1]) - 1), 100 * (exp(ci[2]) - 1)
))
cat(sprintf("Model R-squared: %.3f\n", summary(fit)$r.squared))
